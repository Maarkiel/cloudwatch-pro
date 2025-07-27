"""
Moduł uwierzytelniania i autoryzacji dla User Service
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import redis
import json

from database import get_db
from models import User
from config import settings

# Konfiguracja hashowania haseł
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Konfiguracja security
security = HTTPBearer()

# Połączenie z Redis
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Weryfikacja hasła"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashowanie hasła"""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Tworzenie tokenu dostępu JWT"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": "cloudwatch-pro-user-service",
        "aud": "cloudwatch-pro"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Zapisanie tokenu w Redis dla możliwości unieważnienia
    token_key = f"token:{data.get('sub')}:{encoded_jwt[-10:]}"
    redis_client.setex(
        token_key,
        int(expires_delta.total_seconds()) if expires_delta else settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        json.dumps(to_encode)
    )
    
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Weryfikacja tokenu JWT"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Sprawdzenie czy token nie został unieważniony
        token_key = f"token:{payload.get('sub')}:{token[-10:]}"
        if not redis_client.exists(token_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def revoke_token(token: str) -> bool:
    """Unieważnienie tokenu"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_key = f"token:{payload.get('sub')}:{token[-10:]}"
        return redis_client.delete(token_key) > 0
    except JWTError:
        return False

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Pobieranie aktualnie zalogowanego użytkownika"""
    
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Pobieranie aktywnego użytkownika"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def require_role(required_role: str):
    """Dekorator wymagający określonej roli"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role and current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role} role"
            )
        return current_user
    return role_checker

def require_permissions(required_permissions: list):
    """Dekorator wymagający określonych uprawnień"""
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        user_permissions = get_user_permissions(current_user)
        
        for permission in required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Operation requires {permission} permission"
                )
        return current_user
    return permission_checker

def get_user_permissions(user: User) -> list:
    """Pobieranie uprawnień użytkownika na podstawie roli"""
    role_permissions = {
        "viewer": [
            "dashboards:read",
            "alerts:read",
            "reports:read"
        ],
        "user": [
            "dashboards:read",
            "dashboards:write",
            "alerts:read",
            "alerts:write",
            "reports:read",
            "reports:write",
            "profile:write"
        ],
        "admin": [
            "dashboards:read",
            "dashboards:write",
            "dashboards:delete",
            "alerts:read",
            "alerts:write",
            "alerts:delete",
            "reports:read",
            "reports:write",
            "reports:delete",
            "users:read",
            "users:write",
            "organizations:read",
            "organizations:write",
            "config:read"
        ],
        "super_admin": [
            "*"  # Wszystkie uprawnienia
        ]
    }
    
    return role_permissions.get(user.role, [])

def create_refresh_token(user_id: str) -> str:
    """Tworzenie refresh token"""
    data = {
        "sub": user_id,
        "type": "refresh"
    }
    
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    data.update({"exp": expire})
    
    refresh_token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Zapisanie refresh token w Redis
    refresh_key = f"refresh_token:{user_id}"
    redis_client.setex(
        refresh_key,
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        refresh_token
    )
    
    return refresh_token

def verify_refresh_token(refresh_token: str) -> str:
    """Weryfikacja refresh token i zwrócenie user_id"""
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Sprawdzenie czy refresh token istnieje w Redis
        refresh_key = f"refresh_token:{user_id}"
        stored_token = redis_client.get(refresh_key)
        
        if not stored_token or stored_token != refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )
        
        return user_id
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token"
        )

def revoke_refresh_token(user_id: str) -> bool:
    """Unieważnienie refresh token"""
    refresh_key = f"refresh_token:{user_id}"
    return redis_client.delete(refresh_key) > 0

