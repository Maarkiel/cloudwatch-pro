"""
CloudWatch Pro - Cost Analyzer Service
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
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CloudWatch Pro - Cost Analyzer",
    description="Cloud cost analysis and optimization service",
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

class CloudProvider(str, Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"

class CostPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class CostData(BaseModel):
    date: datetime
    service: str
    provider: CloudProvider
    cost: float
    currency: str = "USD"
    region: str
    tags: Dict[str, str] = Field(default_factory=dict)

class CostSummary(BaseModel):
    period: str
    total_cost: float
    currency: str
    breakdown_by_service: Dict[str, float]
    breakdown_by_provider: Dict[str, float]
    breakdown_by_region: Dict[str, float]
    trend_percentage: float

class OptimizationRecommendation(BaseModel):
    recommendation_id: str
    title: str
    description: str
    potential_savings: float
    confidence: float
    priority: str
    service: str
    provider: CloudProvider
    implementation_effort: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return {"status": "healthy", "service": "cost-analyzer", "timestamp": datetime.utcnow()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/costs/summary", response_model=CostSummary)
async def get_cost_summary(
    period: CostPeriod = CostPeriod.MONTHLY,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get cost summary for specified period"""
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
            
        # Simulate cost data (in real implementation, would fetch from cloud APIs)
        services = ["EC2", "RDS", "S3", "Lambda", "EKS", "CloudWatch"]
        providers = ["aws", "azure", "gcp"]
        regions = ["us-west-2", "us-east-1", "eu-west-1"]
        
        total_cost = 0
        service_costs = {}
        provider_costs = {}
        region_costs = {}
        
        for service in services:
            cost = random.uniform(100, 1000)
            service_costs[service] = round(cost, 2)
            total_cost += cost
            
        for provider in providers:
            cost = random.uniform(200, 800)
            provider_costs[provider] = round(cost, 2)
            
        for region in regions:
            cost = random.uniform(150, 600)
            region_costs[region] = round(cost, 2)
            
        # Calculate trend (simulate)
        trend_percentage = random.uniform(-15, 25)
        
        return CostSummary(
            period=f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            total_cost=round(total_cost, 2),
            currency="USD",
            breakdown_by_service=service_costs,
            breakdown_by_provider=provider_costs,
            breakdown_by_region=region_costs,
            trend_percentage=round(trend_percentage, 2)
        )
        
    except Exception as e:
        logger.error(f"Error getting cost summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cost summary")

@app.get("/costs/daily", response_model=List[CostData])
async def get_daily_costs(
    days: int = Query(default=30, ge=1, le=365),
    service: Optional[str] = None,
    provider: Optional[CloudProvider] = None
):
    """Get daily cost breakdown"""
    try:
        costs = []
        services = ["EC2", "RDS", "S3", "Lambda", "EKS"] if not service else [service]
        providers = [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP] if not provider else [provider]
        regions = ["us-west-2", "us-east-1", "eu-west-1"]
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            
            for svc in services:
                for prov in providers:
                    cost = random.uniform(10, 100)
                    costs.append(CostData(
                        date=date,
                        service=svc,
                        provider=prov,
                        cost=round(cost, 2),
                        region=random.choice(regions),
                        tags={"environment": random.choice(["prod", "staging", "dev"])}
                    ))
                    
        return sorted(costs, key=lambda x: x.date, reverse=True)
        
    except Exception as e:
        logger.error(f"Error getting daily costs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get daily costs")

@app.get("/optimization/recommendations", response_model=List[OptimizationRecommendation])
async def get_optimization_recommendations(
    provider: Optional[CloudProvider] = None,
    min_savings: Optional[float] = None
):
    """Get cost optimization recommendations"""
    try:
        recommendations = [
            OptimizationRecommendation(
                recommendation_id="rec_001",
                title="Right-size EC2 instances",
                description="Several EC2 instances are underutilized and can be downsized to save costs",
                potential_savings=450.00,
                confidence=0.85,
                priority="high",
                service="EC2",
                provider=CloudProvider.AWS,
                implementation_effort="low"
            ),
            OptimizationRecommendation(
                recommendation_id="rec_002",
                title="Use Reserved Instances",
                description="Convert on-demand instances to reserved instances for long-running workloads",
                potential_savings=1200.00,
                confidence=0.95,
                priority="high",
                service="EC2",
                provider=CloudProvider.AWS,
                implementation_effort="medium"
            ),
            OptimizationRecommendation(
                recommendation_id="rec_003",
                title="Optimize S3 storage classes",
                description="Move infrequently accessed data to cheaper storage classes",
                potential_savings=280.00,
                confidence=0.75,
                priority="medium",
                service="S3",
                provider=CloudProvider.AWS,
                implementation_effort="low"
            ),
            OptimizationRecommendation(
                recommendation_id="rec_004",
                title="Schedule non-production resources",
                description="Automatically stop development and staging resources during off-hours",
                potential_savings=650.00,
                confidence=0.90,
                priority="medium",
                service="EC2",
                provider=CloudProvider.AWS,
                implementation_effort="medium"
            ),
            OptimizationRecommendation(
                recommendation_id="rec_005",
                title="Clean up unused resources",
                description="Remove unattached EBS volumes and unused load balancers",
                potential_savings=180.00,
                confidence=0.95,
                priority="low",
                service="EBS",
                provider=CloudProvider.AWS,
                implementation_effort="low"
            )
        ]
        
        # Filter by provider if specified
        if provider:
            recommendations = [r for r in recommendations if r.provider == provider]
            
        # Filter by minimum savings if specified
        if min_savings:
            recommendations = [r for r in recommendations if r.potential_savings >= min_savings]
            
        return sorted(recommendations, key=lambda x: x.potential_savings, reverse=True)
        
    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get optimization recommendations")

@app.get("/costs/forecast")
async def get_cost_forecast(days: int = Query(default=30, ge=1, le=365)):
    """Get cost forecast for specified number of days"""
    try:
        current_daily_avg = random.uniform(80, 120)
        growth_rate = random.uniform(0.02, 0.08)  # 2-8% monthly growth
        
        forecast = []
        for i in range(days):
            date = datetime.utcnow() + timedelta(days=i+1)
            # Simple linear growth model
            projected_cost = current_daily_avg * (1 + (growth_rate * i / 30))
            
            forecast.append({
                "date": date.strftime("%Y-%m-%d"),
                "projected_cost": round(projected_cost, 2),
                "confidence": max(0.5, 0.95 - (i * 0.01))  # Confidence decreases over time
            })
            
        total_forecast = sum(item["projected_cost"] for item in forecast)
        
        return {
            "forecast_period": f"{days} days",
            "total_projected_cost": round(total_forecast, 2),
            "currency": "USD",
            "daily_forecast": forecast,
            "assumptions": {
                "growth_rate": f"{growth_rate*100:.1f}% monthly",
                "base_daily_cost": round(current_daily_avg, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting cost forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cost forecast")

@app.get("/costs/anomalies")
async def detect_cost_anomalies():
    """Detect cost anomalies and unusual spending patterns"""
    try:
        # Simulate anomaly detection
        anomalies = [
            {
                "anomaly_id": "anom_001",
                "date": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "service": "EC2",
                "provider": "aws",
                "expected_cost": 85.50,
                "actual_cost": 142.30,
                "deviation_percentage": 66.4,
                "severity": "high",
                "description": "Unusual spike in EC2 costs, possibly due to auto-scaling event"
            },
            {
                "anomaly_id": "anom_002",
                "date": (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d"),
                "service": "S3",
                "provider": "aws",
                "expected_cost": 25.00,
                "actual_cost": 45.80,
                "deviation_percentage": 83.2,
                "severity": "medium",
                "description": "Higher than expected S3 costs, check for data transfer spikes"
            }
        ]
        
        return {
            "detection_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "anomalies_found": len(anomalies),
            "anomalies": anomalies
        }
        
    except Exception as e:
        logger.error(f"Error detecting cost anomalies: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect cost anomalies")

@app.get("/costs/budget-alerts")
async def get_budget_alerts():
    """Get budget alerts and threshold notifications"""
    try:
        alerts = [
            {
                "budget_name": "Monthly Production Budget",
                "budget_amount": 5000.00,
                "current_spend": 4250.00,
                "percentage_used": 85.0,
                "status": "warning",
                "days_remaining": 8,
                "projected_overage": 150.00
            },
            {
                "budget_name": "Development Environment",
                "budget_amount": 1000.00,
                "current_spend": 750.00,
                "percentage_used": 75.0,
                "status": "ok",
                "days_remaining": 12,
                "projected_overage": 0.00
            }
        ]
        
        return {
            "budget_period": "Monthly",
            "alerts": alerts,
            "total_budgets": len(alerts),
            "budgets_at_risk": len([a for a in alerts if a["status"] == "warning"])
        }
        
    except Exception as e:
        logger.error(f"Error getting budget alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get budget alerts")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)

