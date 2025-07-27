"""
CloudWatch Pro - Metrics Collector Configuration
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "CloudWatch Pro - Metrics Collector"
    version: str = "1.0.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", 8002))
    
    # InfluxDB
    influxdb_url: str = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
    influxdb_token: str = os.getenv("INFLUXDB_TOKEN", "cloudwatch-super-secret-token")
    influxdb_org: str = os.getenv("INFLUXDB_ORG", "cloudwatch-pro")
    influxdb_bucket: str = os.getenv("INFLUXDB_BUCKET", "metrics")
    
    # Redis
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    redis_db: int = int(os.getenv("REDIS_DB", 0))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    
    # Kafka
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    
    # Metrics Collection
    collection_interval: int = int(os.getenv("COLLECTION_INTERVAL", 60))
    metrics_retention_days: int = int(os.getenv("METRICS_RETENTION_DAYS", 30))
    
    # CORS
    allowed_origins: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

