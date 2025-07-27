"""
CloudWatch Pro - Report Generator Service
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import uvicorn
import redis
import json
import uuid
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CloudWatch Pro - Report Generator",
    description="Report generation and export service",
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

class ReportType(str, Enum):
    SYSTEM_HEALTH = "system_health"
    COST_ANALYSIS = "cost_analysis"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CUSTOM = "custom"

class ReportFormat(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    HTML = "html"

class ReportRequest(BaseModel):
    name: str = Field(..., description="Report name")
    type: ReportType = Field(..., description="Report type")
    format: ReportFormat = Field(..., description="Report format")
    start_date: datetime = Field(..., description="Report start date")
    end_date: datetime = Field(..., description="Report end date")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Report filters")
    recipients: List[str] = Field(default_factory=list, description="Report recipients")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return {"status": "healthy", "service": "report-generator", "timestamp": datetime.utcnow()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/generate")
async def generate_report(
    report_request: ReportRequest,
    background_tasks: BackgroundTasks
):
    """Generate report"""
    try:
        report_id = f"report_{uuid.uuid4().hex[:8]}"
        
        # Store report request
        report_data = {
            "report_id": report_id,
            "name": report_request.name,
            "type": report_request.type.value,
            "format": report_request.format.value,
            "start_date": report_request.start_date.isoformat(),
            "end_date": report_request.end_date.isoformat(),
            "filters": json.dumps(report_request.filters),
            "recipients": json.dumps(report_request.recipients),
            "status": "generating",
            "created_at": datetime.utcnow().isoformat()
        }
        
        redis_client.hset(f"report:{report_id}", mapping=report_data)
        redis_client.sadd("reports", report_id)
        
        # Generate report in background
        background_tasks.add_task(
            process_report_generation,
            report_id,
            report_request
        )
        
        return {
            "report_id": report_id,
            "status": "generating",
            "message": "Report generation started"
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")

async def process_report_generation(report_id: str, report_request: ReportRequest):
    """Process report generation (background task)"""
    try:
        logger.info(f"Generating report {report_id}")
        
        # Simulate report generation
        import time
        time.sleep(5)  # Simulate processing time
        
        # Create dummy report file
        os.makedirs("/tmp/reports", exist_ok=True)
        file_path = f"/tmp/reports/{report_id}.{report_request.format.value}"
        
        with open(file_path, "w") as f:
            f.write(f"CloudWatch Pro Report\n")
            f.write(f"Report ID: {report_id}\n")
            f.write(f"Type: {report_request.type.value}\n")
            f.write(f"Generated: {datetime.utcnow()}\n")
            f.write(f"Period: {report_request.start_date} to {report_request.end_date}\n")
        
        # Update status
        redis_client.hset(
            f"report:{report_id}",
            mapping={
                "status": "completed",
                "file_path": file_path,
                "completed_at": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Report {report_id} generated successfully")
        
    except Exception as e:
        logger.error(f"Failed to generate report {report_id}: {e}")
        redis_client.hset(
            f"report:{report_id}",
            mapping={
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            }
        )

@app.get("/reports")
async def list_reports(limit: int = 100):
    """List reports"""
    try:
        report_ids = list(redis_client.smembers("reports"))[:limit]
        reports = []
        
        for report_id in report_ids:
            report_data = redis_client.hgetall(f"report:{report_id}")
            if report_data:
                reports.append({
                    "report_id": report_id,
                    "name": report_data["name"],
                    "type": report_data["type"],
                    "format": report_data["format"],
                    "status": report_data["status"],
                    "created_at": report_data["created_at"],
                    "completed_at": report_data.get("completed_at")
                })
                
        return {"reports": reports}
        
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to list reports")

@app.get("/reports/{report_id}/download")
async def download_report(report_id: str):
    """Download report file"""
    try:
        report_data = redis_client.hgetall(f"report:{report_id}")
        if not report_data:
            raise HTTPException(status_code=404, detail="Report not found")
            
        if report_data["status"] != "completed":
            raise HTTPException(status_code=400, detail="Report not ready for download")
            
        file_path = report_data.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Report file not found")
            
        return FileResponse(
            path=file_path,
            filename=f"{report_data['name']}.{report_data['format']}",
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        raise HTTPException(status_code=500, detail="Failed to download report")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)

