"""
CloudWatch Pro - Dashboard Service
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import logging
import uvicorn
import redis
import json
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CloudWatch Pro - Dashboard Service",
    description="Dashboard management and configuration service",
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

class WidgetType(str, Enum):
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    GAUGE = "gauge"
    TABLE = "table"
    METRIC_CARD = "metric_card"

class Dashboard(BaseModel):
    name: str = Field(..., description="Dashboard name")
    description: str = Field(..., description="Dashboard description")
    is_public: bool = Field(default=False, description="Whether dashboard is public")
    layout: Dict[str, Any] = Field(..., description="Dashboard layout configuration")
    widgets: List[Dict[str, Any]] = Field(default_factory=list, description="Dashboard widgets")
    tags: List[str] = Field(default_factory=list, description="Dashboard tags")

class Widget(BaseModel):
    type: WidgetType = Field(..., description="Widget type")
    title: str = Field(..., description="Widget title")
    position: Dict[str, int] = Field(..., description="Widget position and size")
    config: Dict[str, Any] = Field(..., description="Widget configuration")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return {"status": "healthy", "service": "dashboard-service", "timestamp": datetime.utcnow()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/dashboards")
async def list_dashboards(user_id: Optional[str] = None):
    """List all dashboards"""
    try:
        dashboard_ids = redis_client.smembers("dashboards")
        dashboards = []
        
        for dashboard_id in dashboard_ids:
            dashboard_data = redis_client.hgetall(f"dashboard:{dashboard_id}")
            if not dashboard_data:
                continue
                
            dashboards.append({
                "dashboard_id": dashboard_id,
                "name": dashboard_data["name"],
                "description": dashboard_data["description"],
                "is_public": dashboard_data.get("is_public", "false").lower() == "true",
                "created_at": dashboard_data["created_at"],
                "updated_at": dashboard_data.get("updated_at", dashboard_data["created_at"]),
                "widgets_count": len(json.loads(dashboard_data.get("widgets", "[]"))),
                "tags": json.loads(dashboard_data.get("tags", "[]"))
            })
            
        return {"dashboards": dashboards}
        
    except Exception as e:
        logger.error(f"Error listing dashboards: {e}")
        raise HTTPException(status_code=500, detail="Failed to list dashboards")

@app.post("/dashboards")
async def create_dashboard(dashboard: Dashboard):
    """Create new dashboard"""
    try:
        dashboard_id = f"dash_{uuid.uuid4().hex[:8]}"
        
        dashboard_data = {
            "dashboard_id": dashboard_id,
            "name": dashboard.name,
            "description": dashboard.description,
            "is_public": str(dashboard.is_public).lower(),
            "layout": json.dumps(dashboard.layout),
            "widgets": json.dumps(dashboard.widgets),
            "tags": json.dumps(dashboard.tags),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        redis_client.hset(f"dashboard:{dashboard_id}", mapping=dashboard_data)
        redis_client.sadd("dashboards", dashboard_id)
        
        logger.info(f"Created dashboard: {dashboard_id}")
        
        return {
            "dashboard_id": dashboard_id,
            "message": "Dashboard created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to create dashboard")

@app.get("/dashboards/{dashboard_id}")
async def get_dashboard(dashboard_id: str):
    """Get dashboard by ID"""
    try:
        dashboard_data = redis_client.hgetall(f"dashboard:{dashboard_id}")
        if not dashboard_data:
            raise HTTPException(status_code=404, detail="Dashboard not found")
            
        return {
            "dashboard_id": dashboard_id,
            "name": dashboard_data["name"],
            "description": dashboard_data["description"],
            "is_public": dashboard_data.get("is_public", "false").lower() == "true",
            "layout": json.loads(dashboard_data["layout"]),
            "widgets": json.loads(dashboard_data["widgets"]),
            "tags": json.loads(dashboard_data.get("tags", "[]")),
            "created_at": dashboard_data["created_at"],
            "updated_at": dashboard_data.get("updated_at", dashboard_data["created_at"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)

