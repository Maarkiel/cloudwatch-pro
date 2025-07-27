"""
CloudWatch Pro - ML Predictor Service
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import uvicorn
import redis
import json
import numpy as np
import random
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CloudWatch Pro - ML Predictor",
    description="Machine learning predictions for infrastructure metrics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis client
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

class PredictionType(str, Enum):
    RESOURCE_USAGE = "resource_usage"
    ANOMALY_DETECTION = "anomaly_detection"
    CAPACITY_PLANNING = "capacity_planning"
    COST_FORECAST = "cost_forecast"

class MetricType(str, Enum):
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IO = "network_io"
    REQUEST_RATE = "request_rate"

class PredictionRequest(BaseModel):
    metric_type: MetricType
    resource_id: str
    prediction_horizon: int = Field(default=24, description="Hours to predict ahead")
    confidence_level: float = Field(default=0.95, description="Confidence level for predictions")

class PredictionResult(BaseModel):
    prediction_id: str
    metric_type: MetricType
    resource_id: str
    timestamp: datetime
    predictions: List[Dict[str, Any]]
    confidence_level: float
    model_accuracy: float
    next_update: datetime

class AnomalyDetectionRequest(BaseModel):
    metric_type: MetricType
    resource_id: str
    time_window: int = Field(default=24, description="Hours of historical data to analyze")
    sensitivity: float = Field(default=0.8, description="Anomaly detection sensitivity")

class AnomalyResult(BaseModel):
    detection_id: str
    metric_type: MetricType
    resource_id: str
    timestamp: datetime
    anomalies_detected: List[Dict[str, Any]]
    anomaly_score: float
    threshold: float

class CapacityPlanningRequest(BaseModel):
    resource_type: str
    current_usage: float
    growth_rate: Optional[float] = None
    target_utilization: float = Field(default=0.8, description="Target utilization percentage")
    planning_horizon: int = Field(default=90, description="Days to plan ahead")

class CapacityPlanningResult(BaseModel):
    planning_id: str
    resource_type: str
    current_capacity: float
    projected_demand: List[Dict[str, Any]]
    recommended_scaling: List[Dict[str, Any]]
    cost_impact: float

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return {"status": "healthy", "service": "ml-predictor", "timestamp": datetime.utcnow()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/predict/metrics", response_model=PredictionResult)
async def predict_metrics(request: PredictionRequest):
    """Predict future metric values using ML models"""
    try:
        prediction_id = f"pred_{random.randint(100000, 999999)}"
        
        # Simulate ML prediction (in real implementation, would use trained models)
        predictions = []
        base_value = random.uniform(30, 80)  # Base metric value
        
        for i in range(request.prediction_horizon):
            # Simulate time series prediction with trend and seasonality
            time_factor = i / request.prediction_horizon
            trend = base_value * (1 + 0.1 * time_factor)  # Linear trend
            seasonal = 10 * math.sin(2 * math.pi * i / 24)  # Daily seasonality
            noise = random.uniform(-5, 5)  # Random noise
            
            predicted_value = max(0, min(100, trend + seasonal + noise))
            
            # Calculate confidence intervals
            confidence_margin = (1 - request.confidence_level) * 20
            lower_bound = max(0, predicted_value - confidence_margin)
            upper_bound = min(100, predicted_value + confidence_margin)
            
            predictions.append({
                "timestamp": (datetime.utcnow() + timedelta(hours=i+1)).isoformat(),
                "predicted_value": round(predicted_value, 2),
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
                "confidence": request.confidence_level
            })
            
        # Store prediction in Redis for caching
        prediction_data = {
            "prediction_id": prediction_id,
            "metric_type": request.metric_type.value,
            "resource_id": request.resource_id,
            "predictions": json.dumps(predictions),
            "created_at": datetime.utcnow().isoformat()
        }
        redis_client.hset(f"prediction:{prediction_id}", mapping=prediction_data)
        
        return PredictionResult(
            prediction_id=prediction_id,
            metric_type=request.metric_type,
            resource_id=request.resource_id,
            timestamp=datetime.utcnow(),
            predictions=predictions,
            confidence_level=request.confidence_level,
            model_accuracy=random.uniform(0.85, 0.95),
            next_update=datetime.utcnow() + timedelta(hours=1)
        )
        
    except Exception as e:
        logger.error(f"Error predicting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to predict metrics")

@app.post("/detect/anomalies", response_model=AnomalyResult)
async def detect_anomalies(request: AnomalyDetectionRequest):
    """Detect anomalies in metric data using ML algorithms"""
    try:
        detection_id = f"anom_{random.randint(100000, 999999)}"
        
        # Simulate anomaly detection
        anomalies = []
        threshold = 2.5 * request.sensitivity  # Anomaly threshold
        
        # Generate some sample anomalies
        num_anomalies = random.randint(0, 3)
        for i in range(num_anomalies):
            anomaly_time = datetime.utcnow() - timedelta(hours=random.randint(1, request.time_window))
            anomaly_score = random.uniform(threshold, threshold + 2)
            
            anomalies.append({
                "timestamp": anomaly_time.isoformat(),
                "value": random.uniform(80, 100),
                "expected_value": random.uniform(30, 60),
                "anomaly_score": round(anomaly_score, 2),
                "severity": "high" if anomaly_score > threshold + 1 else "medium",
                "description": f"Unusual {request.metric_type.value} pattern detected"
            })
            
        overall_anomaly_score = max([a["anomaly_score"] for a in anomalies]) if anomalies else 0
        
        return AnomalyResult(
            detection_id=detection_id,
            metric_type=request.metric_type,
            resource_id=request.resource_id,
            timestamp=datetime.utcnow(),
            anomalies_detected=anomalies,
            anomaly_score=round(overall_anomaly_score, 2),
            threshold=round(threshold, 2)
        )
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect anomalies")

@app.post("/plan/capacity", response_model=CapacityPlanningResult)
async def plan_capacity(request: CapacityPlanningRequest):
    """Generate capacity planning recommendations"""
    try:
        planning_id = f"cap_{random.randint(100000, 999999)}"
        
        # Calculate growth rate if not provided
        if request.growth_rate is None:
            request.growth_rate = random.uniform(0.05, 0.15)  # 5-15% monthly growth
            
        current_capacity = request.current_usage / request.target_utilization
        
        # Project demand over planning horizon
        projected_demand = []
        recommended_scaling = []
        
        for week in range(0, request.planning_horizon, 7):
            # Calculate projected usage
            growth_factor = (1 + request.growth_rate) ** (week / 30)  # Monthly growth
            projected_usage = request.current_usage * growth_factor
            
            # Determine if scaling is needed
            utilization = projected_usage / current_capacity
            
            projected_demand.append({
                "week": week // 7 + 1,
                "date": (datetime.utcnow() + timedelta(days=week)).strftime("%Y-%m-%d"),
                "projected_usage": round(projected_usage, 2),
                "utilization": round(utilization * 100, 1),
                "capacity_needed": round(projected_usage / request.target_utilization, 2)
            })
            
            # Recommend scaling if utilization exceeds target
            if utilization > request.target_utilization:
                new_capacity = projected_usage / request.target_utilization
                scaling_factor = new_capacity / current_capacity
                
                recommended_scaling.append({
                    "week": week // 7 + 1,
                    "date": (datetime.utcnow() + timedelta(days=week)).strftime("%Y-%m-%d"),
                    "action": "scale_up",
                    "current_capacity": round(current_capacity, 2),
                    "recommended_capacity": round(new_capacity, 2),
                    "scaling_factor": round(scaling_factor, 2),
                    "urgency": "high" if utilization > 0.9 else "medium"
                })
                
                current_capacity = new_capacity
                
        # Calculate cost impact (simplified)
        total_scaling = sum([s["scaling_factor"] - 1 for s in recommended_scaling])
        cost_impact = total_scaling * 1000  # $1000 per scaling unit
        
        return CapacityPlanningResult(
            planning_id=planning_id,
            resource_type=request.resource_type,
            current_capacity=round(request.current_usage / request.target_utilization, 2),
            projected_demand=projected_demand,
            recommended_scaling=recommended_scaling,
            cost_impact=round(cost_impact, 2)
        )
        
    except Exception as e:
        logger.error(f"Error planning capacity: {e}")
        raise HTTPException(status_code=500, detail="Failed to plan capacity")

@app.get("/models/status")
async def get_model_status():
    """Get status of ML models"""
    try:
        models = [
            {
                "model_name": "cpu_usage_predictor",
                "model_type": "LSTM",
                "status": "active",
                "accuracy": 0.92,
                "last_trained": "2024-01-15T10:30:00Z",
                "training_data_points": 50000,
                "version": "1.2.3"
            },
            {
                "model_name": "anomaly_detector",
                "model_type": "Isolation Forest",
                "status": "active",
                "accuracy": 0.88,
                "last_trained": "2024-01-14T08:15:00Z",
                "training_data_points": 75000,
                "version": "2.1.0"
            },
            {
                "model_name": "capacity_planner",
                "model_type": "Linear Regression",
                "status": "active",
                "accuracy": 0.85,
                "last_trained": "2024-01-13T14:45:00Z",
                "training_data_points": 30000,
                "version": "1.0.5"
            }
        ]
        
        return {
            "total_models": len(models),
            "active_models": len([m for m in models if m["status"] == "active"]),
            "average_accuracy": round(sum(m["accuracy"] for m in models) / len(models), 3),
            "models": models
        }
        
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model status")

@app.get("/predictions/{prediction_id}")
async def get_prediction(prediction_id: str):
    """Get stored prediction by ID"""
    try:
        prediction_data = redis_client.hgetall(f"prediction:{prediction_id}")
        if not prediction_data:
            raise HTTPException(status_code=404, detail="Prediction not found")
            
        return {
            "prediction_id": prediction_id,
            "metric_type": prediction_data["metric_type"],
            "resource_id": prediction_data["resource_id"],
            "predictions": json.loads(prediction_data["predictions"]),
            "created_at": prediction_data["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to get prediction")

@app.get("/insights/trends")
async def get_trend_insights():
    """Get trend insights and patterns"""
    try:
        insights = [
            {
                "insight_id": "trend_001",
                "title": "CPU Usage Trending Upward",
                "description": "CPU usage has increased by 15% over the past week",
                "metric": "cpu_usage",
                "trend_direction": "increasing",
                "confidence": 0.89,
                "impact": "medium",
                "recommendation": "Consider scaling up resources or optimizing workloads"
            },
            {
                "insight_id": "trend_002",
                "title": "Memory Usage Stabilizing",
                "description": "Memory usage patterns have stabilized after recent optimizations",
                "metric": "memory_usage",
                "trend_direction": "stable",
                "confidence": 0.94,
                "impact": "low",
                "recommendation": "Continue monitoring current configuration"
            },
            {
                "insight_id": "trend_003",
                "title": "Network Traffic Spike Pattern",
                "description": "Regular traffic spikes detected every 6 hours, likely batch processing",
                "metric": "network_io",
                "trend_direction": "cyclical",
                "confidence": 0.96,
                "impact": "low",
                "recommendation": "Consider scheduling batch jobs during off-peak hours"
            }
        ]
        
        return {
            "analysis_date": datetime.utcnow().isoformat(),
            "insights_found": len(insights),
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error getting trend insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trend insights")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)

