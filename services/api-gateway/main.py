"""
CloudWatch Pro - API Gateway
Centralny punkt dostępu do wszystkich mikrousług systemu CloudWatch Pro.
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import asyncio
import time
import logging
from typing import Dict, Any, Optional
import os
import json
from datetime import datetime

from auth_middleware import verify_token, rate_limit_middleware
from service_discovery import ServiceDiscovery
from load_balancer import LoadBalancer
from config import settings

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CloudWatch Pro - API Gateway",
    description="Centralny punkt dostępu do mikrousług CloudWatch Pro",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Konfiguracja CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicjalizacja komponentów
service_discovery = ServiceDiscovery()
load_balancer = LoadBalancer()

# Mapa routingu do mikrousług
SERVICE_ROUTES = {
    "/auth": "user-service",
    "/users": "user-service",
    "/metrics": "metrics-collector",
    "/alerts": "alert-manager",
    "/dashboards": "dashboard-service",
    "/costs": "cost-analyzer",
    "/ml": "ml-predictor",
    "/reports": "report-generator",
    "/notifications": "notification-service",
    "/config": "configuration-service"
}

# Endpointy publiczne (nie wymagające autoryzacji)
PUBLIC_ENDPOINTS = [
    "/auth/login",
    "/auth/register",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json"
]

@app.on_startup
async def startup_event():
    """Inicjalizacja przy starcie"""
    logger.info("Starting API Gateway...")
    
    # Inicjalizacja service discovery
    await service_discovery.initialize()
    
    # Rejestracja API Gateway w service discovery
    await service_discovery.register_service(
        "api-gateway",
        "0.0.0.0",
        int(os.getenv("PORT", 8000)),
        health_check_url="/health"
    )
    
    logger.info("API Gateway started successfully")

@app.on_shutdown
async def shutdown_event():
    """Czyszczenie przy zamykaniu"""
    logger.info("Shutting down API Gateway...")
    
    # Wyrejestrowanie z service discovery
    await service_discovery.deregister_service("api-gateway")
    
    logger.info("API Gateway shut down successfully")

@app.get("/")
async def root():
    """Endpoint główny"""
    return {
        "service": "CloudWatch Pro - API Gateway",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "available_services": list(SERVICE_ROUTES.values())
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Sprawdzenie dostępności mikrousług
        services_status = {}
        
        for route, service_name in SERVICE_ROUTES.items():
            try:
                service_url = await service_discovery.get_service_url(service_name)
                if service_url:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(f"{service_url}/health")
                        services_status[service_name] = {
                            "status": "healthy" if response.status_code == 200 else "unhealthy",
                            "url": service_url,
                            "response_time": response.elapsed.total_seconds()
                        }
                else:
                    services_status[service_name] = {
                        "status": "not_found",
                        "url": None
                    }
            except Exception as e:
                services_status[service_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Sprawdzenie ogólnego stanu
        healthy_services = sum(1 for status in services_status.values() if status.get("status") == "healthy")
        total_services = len(services_status)
        
        overall_status = "healthy" if healthy_services == total_services else "degraded"
        
        return {
            "status": overall_status,
            "services": services_status,
            "healthy_services": f"{healthy_services}/{total_services}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    """Middleware główny API Gateway"""
    start_time = time.time()
    
    # Logowanie żądania
    logger.info(f"Request: {request.method} {request.url.path}")
    
    try:
        # Rate limiting
        await rate_limit_middleware(request)
        
        # Autoryzacja (jeśli wymagana)
        if not is_public_endpoint(request.url.path):
            await verify_token(request)
        
        # Przetworzenie żądania
        response = await call_next(request)
        
        # Logowanie odpowiedzi
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} in {process_time:.4f}s")
        
        # Dodanie nagłówków
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Gateway-Version"] = "1.0.0"
        
        return response
    
    except HTTPException as e:
        process_time = time.time() - start_time
        logger.warning(f"HTTP Exception: {e.status_code} - {e.detail} in {process_time:.4f}s")
        raise e
    
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Unexpected error: {str(e)} in {process_time:.4f}s")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "message": str(e)}
        )

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_request(request: Request, path: str):
    """Proxy żądań do odpowiednich mikrousług"""
    
    # Znajdowanie odpowiedniej mikrousługi
    service_name = find_target_service(f"/{path}")
    
    if not service_name:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Pobieranie URL mikrousługi
    service_url = await service_discovery.get_service_url(service_name)
    
    if not service_url:
        raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")
    
    # Budowanie docelowego URL
    target_url = f"{service_url}/{path}"
    
    # Przygotowanie nagłówków
    headers = dict(request.headers)
    headers.pop("host", None)  # Usunięcie nagłówka host
    
    # Przygotowanie parametrów zapytania
    query_params = str(request.url.query) if request.url.query else ""
    if query_params:
        target_url += f"?{query_params}"
    
    try:
        # Wykonanie żądania do mikrousługi
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            if request.method == "GET":
                response = await client.get(target_url, headers=headers)
            
            elif request.method == "POST":
                body = await request.body()
                response = await client.post(target_url, headers=headers, content=body)
            
            elif request.method == "PUT":
                body = await request.body()
                response = await client.put(target_url, headers=headers, content=body)
            
            elif request.method == "DELETE":
                response = await client.delete(target_url, headers=headers)
            
            elif request.method == "PATCH":
                body = await request.body()
                response = await client.patch(target_url, headers=headers, content=body)
            
            elif request.method == "OPTIONS":
                response = await client.options(target_url, headers=headers)
            
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
        
        # Przygotowanie odpowiedzi
        response_headers = dict(response.headers)
        response_headers.pop("content-encoding", None)  # Usunięcie problematycznych nagłówków
        response_headers.pop("transfer-encoding", None)
        
        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            headers=response_headers
        )
    
    except httpx.TimeoutException:
        logger.error(f"Timeout calling {service_name} at {target_url}")
        raise HTTPException(status_code=504, detail="Service timeout")
    
    except httpx.ConnectError:
        logger.error(f"Connection error calling {service_name} at {target_url}")
        raise HTTPException(status_code=503, detail="Service unavailable")
    
    except Exception as e:
        logger.error(f"Error proxying request to {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/gateway/services")
async def list_services():
    """Lista dostępnych mikrousług"""
    services = await service_discovery.list_services()
    
    return {
        "services": services,
        "routes": SERVICE_ROUTES,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/gateway/metrics")
async def gateway_metrics():
    """Metryki API Gateway"""
    return {
        "requests_total": load_balancer.get_total_requests(),
        "requests_per_service": load_balancer.get_requests_per_service(),
        "average_response_time": load_balancer.get_average_response_time(),
        "error_rate": load_balancer.get_error_rate(),
        "timestamp": datetime.utcnow().isoformat()
    }

def find_target_service(path: str) -> Optional[str]:
    """Znajdowanie docelowej mikrousługi na podstawie ścieżki"""
    for route_prefix, service_name in SERVICE_ROUTES.items():
        if path.startswith(route_prefix):
            return service_name
    return None

def is_public_endpoint(path: str) -> bool:
    """Sprawdzenie czy endpoint jest publiczny"""
    return any(path.startswith(endpoint) for endpoint in PUBLIC_ENDPOINTS)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )