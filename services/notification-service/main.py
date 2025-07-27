"""
CloudWatch Pro - Notification Service
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
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
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CloudWatch Pro - Notification Service",
    description="Notification and alerting service",
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

class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    WEBHOOK = "webhook"
    PUSH = "push"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationRequest(BaseModel):
    type: NotificationType = Field(..., description="Notification type")
    recipient: str = Field(..., description="Notification recipient")
    subject: str = Field(..., description="Notification subject")
    message: str = Field(..., description="Notification message")
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class NotificationChannel(BaseModel):
    name: str = Field(..., description="Channel name")
    type: NotificationType = Field(..., description="Channel type")
    config: Dict[str, Any] = Field(..., description="Channel configuration")
    enabled: bool = Field(default=True)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return {"status": "healthy", "service": "notification-service", "timestamp": datetime.utcnow()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/send")
async def send_notification(
    notification: NotificationRequest,
    background_tasks: BackgroundTasks
):
    """Send notification"""
    try:
        notification_id = f"notif_{uuid.uuid4().hex[:8]}"
        
        # Store notification
        notification_data = {
            "notification_id": notification_id,
            "type": notification.type.value,
            "recipient": notification.recipient,
            "subject": notification.subject,
            "message": notification.message,
            "priority": notification.priority.value,
            "metadata": json.dumps(notification.metadata),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        redis_client.hset(f"notification:{notification_id}", mapping=notification_data)
        redis_client.sadd("notifications", notification_id)
        
        # Send notification in background
        background_tasks.add_task(
            process_notification,
            notification_id,
            notification
        )
        
        return {
            "notification_id": notification_id,
            "status": "queued",
            "message": "Notification queued for delivery"
        }
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")

async def process_notification(notification_id: str, notification: NotificationRequest):
    """Process notification (background task)"""
    try:
        logger.info(f"Processing notification {notification_id}")
        
        # Simulate notification sending
        await asyncio.sleep(2)
        
        # Update status
        redis_client.hset(
            f"notification:{notification_id}",
            mapping={
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Notification {notification_id} sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to process notification {notification_id}: {e}")
        redis_client.hset(
            f"notification:{notification_id}",
            mapping={
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            }
        )

@app.get("/notifications")
async def list_notifications(limit: int = 100):
    """List notifications"""
    try:
        notification_ids = list(redis_client.smembers("notifications"))[:limit]
        notifications = []
        
        for notification_id in notification_ids:
            notification_data = redis_client.hgetall(f"notification:{notification_id}")
            if notification_data:
                notifications.append({
                    "notification_id": notification_id,
                    "type": notification_data["type"],
                    "recipient": notification_data["recipient"],
                    "subject": notification_data["subject"],
                    "status": notification_data["status"],
                    "priority": notification_data["priority"],
                    "created_at": notification_data["created_at"],
                    "sent_at": notification_data.get("sent_at")
                })
                
        return {"notifications": notifications}
        
    except Exception as e:
        logger.error(f"Error listing notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to list notifications")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8007)

