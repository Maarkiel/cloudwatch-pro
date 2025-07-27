"""
CloudWatch Pro - Configuration Service
"""

from fastapi import FastAPI, HTTPException
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
    title="CloudWatch Pro - Configuration Service",
    description="System configuration management service",
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

class ConfigType(str, Enum):
    SYSTEM = "system"
    USER = "user"
    SERVICE = "service"
    ALERT = "alert"

class Configuration(BaseModel):
    key: str = Field(..., description="Configuration key")
    value: Any = Field(..., description="Configuration value")
    type: ConfigType = Field(..., description="Configuration type")
    description: str = Field(..., description="Configuration description")
    is_sensitive: bool = Field(default=False, description="Whether config is sensitive")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return {"status": "healthy", "service": "configuration-service", "timestamp": datetime.utcnow()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/config")
async def get_all_configs(config_type: Optional[ConfigType] = None):
    """Get all configurations"""
    try:
        config_keys = redis_client.smembers("config_keys")
        configs = []
        
        for key in config_keys:
            config_data = redis_client.hgetall(f"config:{key}")
            if not config_data:
                continue
                
            if config_type and config_data.get("type") != config_type.value:
                continue
                
            # Don't expose sensitive values
            value = config_data["value"]
            if config_data.get("is_sensitive", "false").lower() == "true":
                value = "***HIDDEN***"
                
            configs.append({
                "key": key,
                "value": json.loads(value) if value != "***HIDDEN***" else value,
                "type": config_data["type"],
                "description": config_data["description"],
                "is_sensitive": config_data.get("is_sensitive", "false").lower() == "true",
                "updated_at": config_data.get("updated_at")
            })
            
        return {"configurations": configs}
        
    except Exception as e:
        logger.error(f"Error getting configurations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get configurations")

@app.get("/config/{key}")
async def get_config(key: str):
    """Get specific configuration"""
    try:
        config_data = redis_client.hgetall(f"config:{key}")
        if not config_data:
            raise HTTPException(status_code=404, detail="Configuration not found")
            
        # Don't expose sensitive values
        value = config_data["value"]
        if config_data.get("is_sensitive", "false").lower() == "true":
            value = "***HIDDEN***"
            
        return {
            "key": key,
            "value": json.loads(value) if value != "***HIDDEN***" else value,
            "type": config_data["type"],
            "description": config_data["description"],
            "is_sensitive": config_data.get("is_sensitive", "false").lower() == "true",
            "updated_at": config_data.get("updated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to get configuration")

@app.post("/config")
async def set_config(config: Configuration):
    """Set configuration"""
    try:
        config_data = {
            "key": config.key,
            "value": json.dumps(config.value),
            "type": config.type.value,
            "description": config.description,
            "is_sensitive": str(config.is_sensitive).lower(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        redis_client.hset(f"config:{config.key}", mapping=config_data)
        redis_client.sadd("config_keys", config.key)
        
        logger.info(f"Set configuration: {config.key}")
        
        return {"message": "Configuration set successfully"}
        
    except Exception as e:
        logger.error(f"Error setting configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to set configuration")

@app.delete("/config/{key}")
async def delete_config(key: str):
    """Delete configuration"""
    try:
        if not redis_client.exists(f"config:{key}"):
            raise HTTPException(status_code=404, detail="Configuration not found")
            
        redis_client.delete(f"config:{key}")
        redis_client.srem("config_keys", key)
        
        logger.info(f"Deleted configuration: {key}")
        
        return {"message": "Configuration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete configuration")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009)

