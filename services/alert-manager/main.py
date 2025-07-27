"""
CloudWatch Pro - Alert Manager Service
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import uvicorn
import redis
import json
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CloudWatch Pro - Alert Manager",
    description="Alert management and notification service",
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

class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class AlertStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class AlertCondition(str, Enum):
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"

class AlertRule(BaseModel):
    name: str = Field(..., description="Alert rule name")
    description: str = Field(..., description="Alert rule description")
    metric_name: str = Field(..., description="Metric to monitor")
    condition: AlertCondition = Field(..., description="Alert condition")
    threshold: float = Field(..., description="Alert threshold value")
    duration: str = Field(default="5m", description="Duration before triggering")
    severity: AlertSeverity = Field(..., description="Alert severity")
    enabled: bool = Field(default=True, description="Whether rule is enabled")
    tags: Dict[str, str] = Field(default_factory=dict, description="Alert tags")
    notification_channels: List[str] = Field(default_factory=list, description="Notification channels")

class Alert(BaseModel):
    alert_id: str = Field(..., description="Unique alert ID")
    rule_name: str = Field(..., description="Alert rule name")
    description: str = Field(..., description="Alert description")
    severity: AlertSeverity = Field(..., description="Alert severity")
    status: AlertStatus = Field(..., description="Alert status")
    resource_id: str = Field(..., description="Resource ID")
    metric_name: str = Field(..., description="Metric name")
    threshold: float = Field(..., description="Threshold value")
    current_value: float = Field(..., description="Current metric value")
    triggered_at: datetime = Field(..., description="When alert was triggered")
    resolved_at: Optional[datetime] = Field(None, description="When alert was resolved")
    tags: Dict[str, str] = Field(default_factory=dict, description="Alert tags")

class AlertRuleResponse(BaseModel):
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: AlertCondition
    threshold: float
    duration: str
    severity: AlertSeverity
    enabled: bool
    created_at: datetime
    created_by: str
    tags: Dict[str, str]
    notification_channels: List[str]

class AlertResponse(BaseModel):
    alert_id: str
    rule_name: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    resource_id: str
    metric_name: str
    threshold: float
    current_value: float
    triggered_at: datetime
    resolved_at: Optional[datetime]
    last_updated: datetime
    tags: Dict[str, str]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return {"status": "healthy", "service": "alert-manager", "timestamp": datetime.utcnow()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(rule: AlertRule):
    """Create new alert rule"""
    try:
        rule_id = f"rule_{uuid.uuid4().hex[:8]}"
        
        rule_data = {
            "rule_id": rule_id,
            "name": rule.name,
            "description": rule.description,
            "metric_name": rule.metric_name,
            "condition": rule.condition.value,
            "threshold": rule.threshold,
            "duration": rule.duration,
            "severity": rule.severity.value,
            "enabled": rule.enabled,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "system",
            "tags": rule.tags,
            "notification_channels": rule.notification_channels
        }
        
        # Store in Redis
        redis_client.hset(f"alert_rule:{rule_id}", mapping=rule_data)
        redis_client.sadd("alert_rules", rule_id)
        
        logger.info(f"Created alert rule: {rule_id}")
        
        return AlertRuleResponse(
            rule_id=rule_id,
            name=rule.name,
            description=rule.description,
            metric_name=rule.metric_name,
            condition=rule.condition,
            threshold=rule.threshold,
            duration=rule.duration,
            severity=rule.severity,
            enabled=rule.enabled,
            created_at=datetime.fromisoformat(rule_data["created_at"]),
            created_by=rule_data["created_by"],
            tags=rule.tags,
            notification_channels=rule.notification_channels
        )
        
    except Exception as e:
        logger.error(f"Error creating alert rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert rule")

@app.get("/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(enabled: Optional[bool] = None):
    """List all alert rules"""
    try:
        rule_ids = redis_client.smembers("alert_rules")
        rules = []
        
        for rule_id in rule_ids:
            rule_data = redis_client.hgetall(f"alert_rule:{rule_id}")
            if not rule_data:
                continue
                
            if enabled is not None and rule_data.get("enabled") != str(enabled).lower():
                continue
                
            rules.append(AlertRuleResponse(
                rule_id=rule_id,
                name=rule_data["name"],
                description=rule_data["description"],
                metric_name=rule_data["metric_name"],
                condition=AlertCondition(rule_data["condition"]),
                threshold=float(rule_data["threshold"]),
                duration=rule_data["duration"],
                severity=AlertSeverity(rule_data["severity"]),
                enabled=rule_data["enabled"].lower() == "true",
                created_at=datetime.fromisoformat(rule_data["created_at"]),
                created_by=rule_data["created_by"],
                tags=json.loads(rule_data.get("tags", "{}")),
                notification_channels=json.loads(rule_data.get("notification_channels", "[]"))
            ))
            
        return rules
        
    except Exception as e:
        logger.error(f"Error listing alert rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to list alert rules")

@app.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(
    status: Optional[AlertStatus] = None,
    severity: Optional[AlertSeverity] = None,
    limit: int = 100
):
    """List alerts with optional filtering"""
    try:
        alert_ids = redis_client.smembers("alerts")
        alerts = []
        
        for alert_id in list(alert_ids)[:limit]:
            alert_data = redis_client.hgetall(f"alert:{alert_id}")
            if not alert_data:
                continue
                
            if status and alert_data.get("status") != status.value:
                continue
                
            if severity and alert_data.get("severity") != severity.value:
                continue
                
            alerts.append(AlertResponse(
                alert_id=alert_id,
                rule_name=alert_data["rule_name"],
                description=alert_data["description"],
                severity=AlertSeverity(alert_data["severity"]),
                status=AlertStatus(alert_data["status"]),
                resource_id=alert_data["resource_id"],
                metric_name=alert_data["metric_name"],
                threshold=float(alert_data["threshold"]),
                current_value=float(alert_data["current_value"]),
                triggered_at=datetime.fromisoformat(alert_data["triggered_at"]),
                resolved_at=datetime.fromisoformat(alert_data["resolved_at"]) if alert_data.get("resolved_at") else None,
                last_updated=datetime.fromisoformat(alert_data["last_updated"]),
                tags=json.loads(alert_data.get("tags", "{}"))
            ))
            
        return sorted(alerts, key=lambda x: x.triggered_at, reverse=True)
        
    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to list alerts")

@app.put("/alerts/{alert_id}/status")
async def update_alert_status(alert_id: str, status: AlertStatus, resolution_note: Optional[str] = None):
    """Update alert status"""
    try:
        alert_data = redis_client.hgetall(f"alert:{alert_id}")
        if not alert_data:
            raise HTTPException(status_code=404, detail="Alert not found")
            
        alert_data["status"] = status.value
        alert_data["last_updated"] = datetime.utcnow().isoformat()
        
        if status == AlertStatus.RESOLVED:
            alert_data["resolved_at"] = datetime.utcnow().isoformat()
            if resolution_note:
                alert_data["resolution_note"] = resolution_note
                
        redis_client.hset(f"alert:{alert_id}", mapping=alert_data)
        
        logger.info(f"Updated alert {alert_id} status to {status.value}")
        
        return {"message": "Alert status updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert status")

@app.post("/alerts/trigger")
async def trigger_alert(
    rule_name: str,
    resource_id: str,
    current_value: float,
    background_tasks: BackgroundTasks
):
    """Trigger an alert"""
    try:
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"
        
        # Get rule details (simplified - in real implementation would fetch from rules)
        alert_data = {
            "alert_id": alert_id,
            "rule_name": rule_name,
            "description": f"Alert triggered for {rule_name}",
            "severity": "warning",
            "status": "active",
            "resource_id": resource_id,
            "metric_name": "cpu_usage",
            "threshold": 80.0,
            "current_value": current_value,
            "triggered_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "tags": "{}"
        }
        
        # Store alert
        redis_client.hset(f"alert:{alert_id}", mapping=alert_data)
        redis_client.sadd("alerts", alert_id)
        
        # Add background task for notifications
        background_tasks.add_task(send_alert_notification, alert_id, alert_data)
        
        logger.info(f"Triggered alert: {alert_id}")
        
        return {"alert_id": alert_id, "message": "Alert triggered successfully"}
        
    except Exception as e:
        logger.error(f"Error triggering alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger alert")

async def send_alert_notification(alert_id: str, alert_data: Dict[str, Any]):
    """Send alert notification (background task)"""
    try:
        # Simulate notification sending
        logger.info(f"Sending notification for alert {alert_id}")
        await asyncio.sleep(1)  # Simulate async notification
        logger.info(f"Notification sent for alert {alert_id}")
    except Exception as e:
        logger.error(f"Failed to send notification for alert {alert_id}: {e}")

@app.get("/metrics")
async def get_alert_metrics():
    """Get alert metrics and statistics"""
    try:
        alert_ids = redis_client.smembers("alerts")
        
        total_alerts = len(alert_ids)
        active_alerts = 0
        critical_alerts = 0
        warning_alerts = 0
        
        for alert_id in alert_ids:
            alert_data = redis_client.hgetall(f"alert:{alert_id}")
            if alert_data.get("status") == "active":
                active_alerts += 1
            if alert_data.get("severity") == "critical":
                critical_alerts += 1
            elif alert_data.get("severity") == "warning":
                warning_alerts += 1
                
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "resolved_alerts": total_alerts - active_alerts,
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts,
            "info_alerts": total_alerts - critical_alerts - warning_alerts
        }
        
    except Exception as e:
        logger.error(f"Error getting alert metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert metrics")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)


@app.get("/health")
async def health():
    return {"status": "healthy"}
