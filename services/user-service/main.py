"""
CloudWatch Pro - User Service
Mikrousługa odpowiedzialna za zarządzanie użytkownikami, uwierzytelnianie i autoryzację.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import os
from datetime import datetime, timedelta

from database import get_db, engine, Base
from models import User, Organization, UserOrganization
from schemas import (
    UserCreate, UserResponse, UserLogin, Token, 
    OrganizationCreate, OrganizationResponse
)
from auth import (
    create_access_token, verify_token, get_password_hash, 
    verify_password, get_current_user
)
from config import settings

# Tworzenie tabel w bazie danych
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CloudWatch Pro - User Service",
    description="Mikrousługa zarządzania użytkownikami i uwierzytelniania",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Konfiguracja CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # W produkcji należy ograniczyć do konkretnych domen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

@app.get("/")
async def root():
    """Endpoint sprawdzający status serwisu"""
    return {
        "service": "CloudWatch Pro - User Service",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint dla Kubernetes"""
    return {"status": "healthy"}

@app.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Rejestracja nowego użytkownika"""
    
    # Sprawdzenie czy użytkownik już istnieje
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Hashowanie hasła
    hashed_password = get_password_hash(user_data.password)
    
    # Tworzenie nowego użytkownika
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role or "user"
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse.from_orm(db_user)

@app.post("/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Logowanie użytkownika"""
    
    # Znajdowanie użytkownika po email lub username
    user = db.query(User).filter(
        (User.email == user_credentials.username) | 
        (User.username == user_credentials.username)
    ).first()
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    # Aktualizacja czasu ostatniego logowania
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Tworzenie tokenu dostępu
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role}
    )
    
    return Token(access_token=access_token, token_type="bearer")

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Pobieranie informacji o aktualnie zalogowanym użytkowniku"""
    return UserResponse.from_orm(current_user)

@app.put("/users/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aktualizacja profilu użytkownika"""
    
    # Aktualizacja danych użytkownika
    if user_update.first_name:
        current_user.first_name = user_update.first_name
    if user_update.last_name:
        current_user.last_name = user_update.last_name
    if user_update.email and user_update.email != current_user.email:
        # Sprawdzenie czy nowy email nie jest już zajęty
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.from_orm(current_user)

@app.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista użytkowników (tylko dla administratorów)"""
    
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.from_orm(user) for user in users]

@app.post("/organizations", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tworzenie nowej organizacji"""
    
    # Tworzenie organizacji
    db_org = Organization(
        name=org_data.name,
        description=org_data.description
    )
    
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    
    # Dodanie twórcy jako właściciela organizacji
    user_org = UserOrganization(
        user_id=current_user.id,
        organization_id=db_org.id,
        role="owner"
    )
    
    db.add(user_org)
    db.commit()
    
    return OrganizationResponse.from_orm(db_org)

@app.get("/organizations", response_model=List[OrganizationResponse])
async def list_user_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista organizacji użytkownika"""
    
    user_orgs = db.query(UserOrganization).filter(
        UserOrganization.user_id == current_user.id
    ).all()
    
    organizations = []
    for user_org in user_orgs:
        org = db.query(Organization).filter(
            Organization.id == user_org.organization_id
        ).first()
        if org:
            organizations.append(OrganizationResponse.from_orm(org))
    
    return organizations

@app.get("/auth/verify")
async def verify_token_endpoint(current_user: User = Depends(get_current_user)):
    """Weryfikacja tokenu (dla innych mikrousług)"""
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        reload=True
    )

