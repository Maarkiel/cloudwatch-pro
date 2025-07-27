"""
Konfiguracja bazy danych dla User Service
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

from config import settings

# Tworzenie silnika bazy danych
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

# Tworzenie sesji
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Bazowa klasa dla modeli
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency do pobierania sesji bazy danych"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Tworzenie tabel w bazie danych"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Usuwanie tabel z bazy danych"""
    Base.metadata.drop_all(bind=engine)

