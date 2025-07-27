"""
CloudWatch Pro - Metrics Collector Service
Mikrousługa odpowiedzialna za zbieranie metryk z różnych źródeł chmurowych.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
import json
import logging
from datetime import datetime, timedelta
import os

from collectors import (
    AWSCloudWatchCollector,
    AzureMonitorCollector,
    GCPMonitoringCollector,
    PrometheusCollector
)
from storage import InfluxDBStorage, RedisCache
from schemas import (
    MetricData, MetricQuery, MetricSource, 
    CollectionConfig, MetricResponse
)
from config import settings

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CloudWatch Pro - Metrics Collector",
    description="Mikrousługa zbierania metryk z różnych źródeł chmurowych",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Konfiguracja CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicjalizacja komponentów
influx_storage = InfluxDBStorage()
redis_cache = RedisCache()

# Kolektory metryk
collectors = {
    "aws": AWSCloudWatchCollector(),
    "azure": AzureMonitorCollector(),
    "gcp": GCPMonitoringCollector(),
    "prometheus": PrometheusCollector()
}

# WebSocket connections dla real-time streaming
active_connections: List[WebSocket] = []

@app.on_startup
async def startup_event():
    """Inicjalizacja przy starcie aplikacji"""
    logger.info("Starting Metrics Collector Service...")
    
    # Inicjalizacja połączeń z bazami danych
    await influx_storage.initialize()
    await redis_cache.initialize()
    
    # Uruchomienie zadań w tle
    asyncio.create_task(periodic_collection_task())
    
    logger.info("Metrics Collector Service started successfully")

@app.on_shutdown
async def shutdown_event():
    """Czyszczenie przy zamykaniu aplikacji"""
    logger.info("Shutting down Metrics Collector Service...")
    
    await influx_storage.close()
    await redis_cache.close()
    
    logger.info("Metrics Collector Service shut down successfully")

@app.get("/")
async def root():
    """Endpoint sprawdzający status serwisu"""
    return {
        "service": "CloudWatch Pro - Metrics Collector",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "active_collectors": list(collectors.keys()),
        "active_connections": len(active_connections)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint dla Kubernetes"""
    try:
        # Sprawdzenie połączenia z InfluxDB
        influx_status = await influx_storage.health_check()
        
        # Sprawdzenie połączenia z Redis
        redis_status = await redis_cache.health_check()
        
        return {
            "status": "healthy",
            "influxdb": influx_status,
            "redis": redis_status,
            "collectors": {name: collector.is_healthy() for name, collector in collectors.items()}
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/metrics/ingest")
async def ingest_metrics(metrics: List[MetricData], background_tasks: BackgroundTasks):
    """Przyjmowanie metryk z zewnętrznych źródeł"""
    try:
        # Walidacja i normalizacja metryk
        normalized_metrics = []
        for metric in metrics:
            normalized_metric = await normalize_metric(metric)
            normalized_metrics.append(normalized_metric)
        
        # Zapisanie metryk w tle
        background_tasks.add_task(store_metrics, normalized_metrics)
        
        # Wysłanie metryk do active connections (real-time streaming)
        background_tasks.add_task(broadcast_metrics, normalized_metrics)
        
        return {
            "status": "accepted",
            "metrics_count": len(metrics),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error ingesting metrics: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/metrics/query", response_model=MetricResponse)
async def query_metrics(
    source: Optional[str] = None,
    metric_name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    tags: Optional[str] = None,
    limit: int = 1000
):
    """Zapytania o metryki"""
    try:
        # Sprawdzenie cache
        cache_key = f"query:{source}:{metric_name}:{start_time}:{end_time}:{tags}:{limit}"
        cached_result = await redis_cache.get(cache_key)
        
        if cached_result:
            return MetricResponse.parse_raw(cached_result)
        
        # Budowanie zapytania
        query = build_influx_query(source, metric_name, start_time, end_time, tags, limit)
        
        # Wykonanie zapytania
        results = await influx_storage.query(query)
        
        # Przetworzenie wyników
        processed_results = process_query_results(results)
        
        response = MetricResponse(
            metrics=processed_results,
            total_count=len(processed_results),
            query_time=datetime.utcnow(),
            source=source
        )
        
        # Zapisanie w cache na 5 minut
        await redis_cache.set(cache_key, response.json(), expire=300)
        
        return response
    
    except Exception as e:
        logger.error(f"Error querying metrics: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.websocket("/metrics/stream")
async def metrics_stream(websocket: WebSocket):
    """WebSocket endpoint dla real-time streaming metryk"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Oczekiwanie na wiadomości od klienta (np. filtry)
            data = await websocket.receive_text()
            filters = json.loads(data)
            
            # Aplikacja filtrów do streamingu
            await apply_stream_filters(websocket, filters)
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("WebSocket connection closed")

@app.post("/sources/configure")
async def configure_source(config: CollectionConfig):
    """Konfiguracja źródła metryk"""
    try:
        source_type = config.source_type
        
        if source_type not in collectors:
            raise HTTPException(status_code=400, detail=f"Unsupported source type: {source_type}")
        
        # Konfiguracja kolektora
        collector = collectors[source_type]
        await collector.configure(config.config)
        
        # Zapisanie konfiguracji
        await redis_cache.set(f"config:{source_type}", config.json())
        
        return {
            "status": "configured",
            "source_type": source_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error configuring source: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/sources")
async def list_sources():
    """Lista dostępnych źródeł metryk"""
    sources = []
    
    for source_type, collector in collectors.items():
        config_data = await redis_cache.get(f"config:{source_type}")
        
        sources.append({
            "type": source_type,
            "status": "active" if collector.is_configured() else "not_configured",
            "last_collection": collector.last_collection_time,
            "metrics_count": collector.metrics_collected,
            "config": json.loads(config_data) if config_data else None
        })
    
    return {"sources": sources}

@app.post("/collection/start")
async def start_collection(source_type: str, background_tasks: BackgroundTasks):
    """Uruchomienie zbierania metryk z określonego źródła"""
    if source_type not in collectors:
        raise HTTPException(status_code=400, detail=f"Unknown source type: {source_type}")
    
    collector = collectors[source_type]
    
    if not collector.is_configured():
        raise HTTPException(status_code=400, detail=f"Source {source_type} is not configured")
    
    # Uruchomienie zbierania w tle
    background_tasks.add_task(collect_from_source, source_type)
    
    return {
        "status": "started",
        "source_type": source_type,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/collection/stop")
async def stop_collection(source_type: str):
    """Zatrzymanie zbierania metryk z określonego źródła"""
    if source_type not in collectors:
        raise HTTPException(status_code=400, detail=f"Unknown source type: {source_type}")
    
    collector = collectors[source_type]
    await collector.stop_collection()
    
    return {
        "status": "stopped",
        "source_type": source_type,
        "timestamp": datetime.utcnow().isoformat()
    }

# Funkcje pomocnicze

async def normalize_metric(metric: MetricData) -> Dict[str, Any]:
    """Normalizacja metryki do standardowego formatu"""
    return {
        "measurement": metric.name,
        "tags": metric.tags or {},
        "fields": {"value": metric.value},
        "time": metric.timestamp or datetime.utcnow()
    }

async def store_metrics(metrics: List[Dict[str, Any]]):
    """Zapisanie metryk w InfluxDB"""
    try:
        await influx_storage.write_metrics(metrics)
        logger.info(f"Stored {len(metrics)} metrics")
    except Exception as e:
        logger.error(f"Error storing metrics: {e}")

async def broadcast_metrics(metrics: List[Dict[str, Any]]):
    """Wysłanie metryk do wszystkich aktywnych połączeń WebSocket"""
    if not active_connections:
        return
    
    message = {
        "type": "metrics",
        "data": metrics,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(message))
        except:
            disconnected.append(connection)
    
    # Usunięcie nieaktywnych połączeń
    for connection in disconnected:
        active_connections.remove(connection)

async def collect_from_source(source_type: str):
    """Zbieranie metryk z określonego źródła"""
    try:
        collector = collectors[source_type]
        metrics = await collector.collect_metrics()
        
        if metrics:
            await store_metrics(metrics)
            await broadcast_metrics(metrics)
            
        logger.info(f"Collected {len(metrics)} metrics from {source_type}")
        
    except Exception as e:
        logger.error(f"Error collecting from {source_type}: {e}")

async def periodic_collection_task():
    """Zadanie okresowego zbierania metryk"""
    while True:
        try:
            for source_type, collector in collectors.items():
                if collector.is_configured() and collector.is_auto_collection_enabled():
                    await collect_from_source(source_type)
            
            # Oczekiwanie przed następnym cyklem
            await asyncio.sleep(settings.COLLECTION_INTERVAL)
            
        except Exception as e:
            logger.error(f"Error in periodic collection: {e}")
            await asyncio.sleep(60)  # Oczekiwanie przed ponowną próbą

def build_influx_query(source, metric_name, start_time, end_time, tags, limit):
    """Budowanie zapytania InfluxDB"""
    query = f'from(bucket: "{settings.INFLUX_BUCKET}")'
    
    if start_time:
        query += f' |> range(start: {start_time.isoformat()}Z'
        if end_time:
            query += f', stop: {end_time.isoformat()}Z'
        query += ')'
    else:
        query += ' |> range(start: -1h)'
    
    if source:
        query += f' |> filter(fn: (r) => r.source == "{source}")'
    
    if metric_name:
        query += f' |> filter(fn: (r) => r._measurement == "{metric_name}")'
    
    if tags:
        # Parsowanie tagów (format: key1=value1,key2=value2)
        tag_filters = tags.split(',')
        for tag_filter in tag_filters:
            if '=' in tag_filter:
                key, value = tag_filter.split('=', 1)
                query += f' |> filter(fn: (r) => r.{key} == "{value}")'
    
    query += f' |> limit(n: {limit})'
    
    return query

def process_query_results(results):
    """Przetwarzanie wyników zapytania"""
    processed = []
    
    for table in results:
        for record in table.records:
            processed.append({
                "time": record.get_time(),
                "measurement": record.get_measurement(),
                "value": record.get_value(),
                "tags": {k: v for k, v in record.values.items() if k.startswith('tag_')},
                "fields": {k: v for k, v in record.values.items() if k.startswith('field_')}
            })
    
    return processed

async def apply_stream_filters(websocket: WebSocket, filters: Dict[str, Any]):
    """Aplikacja filtrów do streamingu"""
    # Implementacja filtrowania w czasie rzeczywistym
    # Na razie wysyłamy potwierdzenie
    await websocket.send_text(json.dumps({
        "type": "filters_applied",
        "filters": filters,
        "timestamp": datetime.utcnow().isoformat()
    }))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8002)),
        reload=True
    )

