"""
CloudWatch Pro - API Gateway Authentication Middleware
"""

import time
import redis
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional, Dict, Any
import logging

from config import settings

logger = logging.getLogger(__name__)

# Redis client for rate limiting and token blacklist
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password if settings.redis_password else None,
    decode_responses=True
)

security = HTTPBearer()


async def verify_token(request: Request) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token from request headers
    """
    try:
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        token = authorization.split(" ")[1]
        
        # Check if token is blacklisted
        if redis_client.get(f"blacklist:{token}"):
            raise HTTPException(status_code=401, detail="Token has been revoked")
        
        # Decode and verify token
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Check token expiration
        exp = payload.get("exp")
        if exp and time.time() > exp:
            raise HTTPException(status_code=401, detail="Token has expired")
        
        return payload
        
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def rate_limit_middleware(request: Request) -> None:
    """
    Rate limiting middleware
    """
    try:
        # Get client IP
        client_ip = request.client.host
        
        # Create rate limit key
        rate_limit_key = f"rate_limit:{client_ip}"
        
        # Get current request count
        current_requests = redis_client.get(rate_limit_key)
        
        if current_requests is None:
            # First request from this IP
            redis_client.setex(
                rate_limit_key, 
                settings.rate_limit_window, 
                1
            )
        else:
            current_requests = int(current_requests)
            
            if current_requests >= settings.rate_limit_requests:
                raise HTTPException(
                    status_code=429, 
                    detail="Rate limit exceeded"
                )
            
            # Increment request count
            redis_client.incr(rate_limit_key)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limiting error: {e}")
        # Don't block requests if rate limiting fails
        pass


def create_access_token(data: Dict[str, Any]) -> str:
    """
    Create JWT access token
    """
    to_encode = data.copy()
    expire = time.time() + (settings.access_token_expire_minutes * 60)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def blacklist_token(token: str) -> None:
    """
    Add token to blacklist
    """
    try:
        # Decode token to get expiration
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm],
            options={"verify_exp": False}
        )
        
        exp = payload.get("exp", time.time() + 3600)
        ttl = max(int(exp - time.time()), 1)
        
        # Add to blacklist with TTL
        redis_client.setex(f"blacklist:{token}", ttl, "1")
        
    except Exception as e:
        logger.error(f"Error blacklisting token: {e}")


class RateLimitExceeded(Exception):
    """Rate limit exceeded exception"""
    pass


class AuthenticationFailed(Exception):
    """Authentication failed exception"""
    pass

