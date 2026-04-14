"""
SkillScan MVP - Database Configuration and Connection Setup
Supports both PostgreSQL (Supabase) and SQLite (local development)
"""

import os
from typing import Optional
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from models import Base

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


class DatabaseConfig:
    """Database configuration management"""
    
    # PostgreSQL (Production - Supabase)
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "skillscan")
    
    # SQLite (Development)
    SQLITE_URL = os.getenv("SQLITE_URL", "sqlite:///./skillscan.db")
    
    @staticmethod
    def get_database_url() -> str:
        """Get appropriate database URL based on environment"""
        if DATABASE_URL:
            return DATABASE_URL
        
        if ENVIRONMENT == "production":
            return (
                f"postgresql://{DatabaseConfig.POSTGRES_USER}:"
                f"{DatabaseConfig.POSTGRES_PASSWORD}@"
                f"{DatabaseConfig.POSTGRES_HOST}:"
                f"{DatabaseConfig.POSTGRES_PORT}/"
                f"{DatabaseConfig.POSTGRES_DB}"
            )
        else:
            return DatabaseConfig.SQLITE_URL


class DatabaseManager:
    """Manage database connections and sessions"""
    
    _engine = None
    _session_factory = None
    
    @classmethod
    def initialize(cls, database_url: Optional[str] = None, echo: bool = False):
        """
        Initialize database engine and session factory
        
        Args:
            database_url: Database URL (uses config if None)
            echo: Enable SQL echo for debugging
        """
        if database_url is None:
            database_url = DatabaseConfig.get_database_url()
        
        # Create engine based on database type
        if "postgresql" in database_url:
            # PostgreSQL specific configuration
            cls._engine = create_engine(
                database_url,
                echo=echo,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
            )
        else:
            # SQLite specific configuration
            cls._engine = create_engine(
                database_url,
                echo=echo,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool if ":memory:" in database_url else None,
            )
        
        # Enable foreign keys for SQLite
        if "sqlite" in database_url:
            @event.listens_for(cls._engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        # Create session factory
        cls._session_factory = sessionmaker(bind=cls._engine, expire_on_commit=False)
        
        print(f"[DB] Connected to: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    
    @classmethod
    def get_engine(cls):
        """Get SQLAlchemy engine"""
        if cls._engine is None:
            cls.initialize()
        return cls._engine
    
    @classmethod
    def get_session(cls) -> Session:
        """Get new database session"""
        if cls._session_factory is None:
            cls.initialize()
        return cls._session_factory()
    
    @classmethod
    def create_all_tables(cls):
        """Create all tables in the database"""
        engine = cls.get_engine()
        Base.metadata.create_all(engine)
        print("[DB] All tables created successfully!")
    
    @classmethod
    def drop_all_tables(cls):
        """Drop all tables (use with caution!)"""
        engine = cls.get_engine()
        Base.metadata.drop_all(engine)
        print("[DB] All tables dropped!")
    
    @classmethod
    def close(cls):
        """Close all connections"""
        if cls._engine:
            cls._engine.dispose()
            print("[DB] Database connections closed")


class SessionLocal:
    """
    Dependency injection for Flask routes
    Usage: 
        db = SessionLocal()
        try:
            students = db.query(Student).all()
        finally:
            db.close()
    """
    
    def __init__(self):
        self.session = DatabaseManager.get_session()
    
    def __enter__(self):
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


# Initialize on module import (for development)
if ENVIRONMENT == "development":
    DatabaseManager.initialize(echo=False)
