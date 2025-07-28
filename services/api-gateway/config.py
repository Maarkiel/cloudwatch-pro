"""
CloudWatch Pro - API Gateway Configuration
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "CloudWatch Pro - API Gateway"
    version: str = "1.0.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", 8000))
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-super-secret-key-for-development-only")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    redis_db: int = int(os.getenv("REDIS_DB", 0))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    
    # Rate Limiting
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", 1000))
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", 3600))
    
    # Service URLs
    user_service_url: str = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
    metrics_service_url: str = os.getenv("METRICS_SERVICE_URL", "http://metrics-collector:8002")
    
    # CORS
    allowed_origins: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
