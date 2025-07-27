"""
Konfiguracja aplikacji User Service
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Ustawienia aplikacji"""
    
    # Podstawowe ustawienia aplikacji
    APP_NAME: str = "CloudWatch Pro - User Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Ustawienia bazy danych
    DATABASE_URL: str = "postgresql://cloudwatch:cloudwatch123@localhost:5432/cloudwatch_users"
    
    # Ustawienia Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Ustawienia JWT
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Ustawienia CORS
    ALLOWED_ORIGINS: list = ["*"]
    
    # Ustawienia email (dla resetowania haseł)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    # Ustawienia rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 godzina
    
    # Ustawienia logowania
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Ustawienia bezpieczeństwa
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Ustawienia sesji
    SESSION_EXPIRE_HOURS: int = 24
    MAX_SESSIONS_PER_USER: int = 5
    
    # Ustawienia API
    API_V1_PREFIX: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Instancja ustawień
settings = Settings()

# Walidacja ustawień
def validate_settings():
    """Walidacja ustawień aplikacji"""
    errors = []
    
    if not settings.SECRET_KEY or settings.SECRET_KEY == "your-super-secret-key-change-this-in-production":
        errors.append("SECRET_KEY must be set to a secure value in production")
    
    if len(settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY should be at least 32 characters long")
    
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL must be set")
    
    if errors:
        raise ValueError("Configuration errors: " + "; ".join(errors))

# Walidacja przy imporcie
if not settings.DEBUG:
    validate_settings()

