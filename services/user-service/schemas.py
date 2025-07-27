"""
Schematy Pydantic dla walidacji danych w User Service
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    """Bazowy schemat użytkownika"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)

class UserCreate(UserBase):
    """Schemat tworzenia użytkownika"""
    password: str = Field(..., min_length=8, max_length=128)
    role: Optional[str] = Field("user", regex="^(user|admin|super_admin|viewer)$")

class UserUpdate(BaseModel):
    """Schemat aktualizacji użytkownika"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    preferences: Optional[Dict[str, Any]] = None

class UserResponse(UserBase):
    """Schemat odpowiedzi z danymi użytkownika"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    preferences: Dict[str, Any] = {}

class UserLogin(BaseModel):
    """Schemat logowania użytkownika"""
    username: str = Field(..., description="Username lub email")
    password: str = Field(..., min_length=1)

class Token(BaseModel):
    """Schemat tokenu dostępu"""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None

class TokenData(BaseModel):
    """Dane zawarte w tokenie"""
    username: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None

class OrganizationBase(BaseModel):
    """Bazowy schemat organizacji"""
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    """Schemat tworzenia organizacji"""
    settings: Optional[Dict[str, Any]] = {}

class OrganizationUpdate(BaseModel):
    """Schemat aktualizacji organizacji"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class OrganizationResponse(OrganizationBase):
    """Schemat odpowiedzi z danymi organizacji"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any] = {}

class UserOrganizationResponse(BaseModel):
    """Schemat relacji użytkownik-organizacja"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: UUID
    organization_id: UUID
    role: str
    joined_at: datetime

class APIKeyCreate(BaseModel):
    """Schemat tworzenia klucza API"""
    name: str = Field(..., min_length=2, max_length=255)
    permissions: List[str] = []
    expires_at: Optional[datetime] = None
    organization_id: Optional[UUID] = None

class APIKeyResponse(BaseModel):
    """Schemat odpowiedzi z kluczem API"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    permissions: List[str]
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    last_used: Optional[datetime]

class UserSessionResponse(BaseModel):
    """Schemat sesji użytkownika"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    expires_at: datetime
    is_active: bool

class PasswordChange(BaseModel):
    """Schemat zmiany hasła"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

class PasswordReset(BaseModel):
    """Schemat resetowania hasła"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Schemat potwierdzenia resetowania hasła"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

class UserPermissions(BaseModel):
    """Schemat uprawnień użytkownika"""
    permissions: List[str]
    role: str
    organization_roles: Dict[str, str] = {}

class HealthCheck(BaseModel):
    """Schemat health check"""
    status: str
    timestamp: datetime
    version: str
    database_status: str
    redis_status: str

class ErrorResponse(BaseModel):
    """Schemat odpowiedzi błędu"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime

