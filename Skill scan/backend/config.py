"""
Configuration management for SkillScan Flask application.
Supports development, production, and testing environments.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class with common settings."""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', os.urandom(32).hex())
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # CORS
    CORS_ORIGINS = [os.getenv('REACT_APP_URL', 'http://localhost:3000')]


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'sqlite:///skillscan.db'
    )


class ProductionConfig(Config):
    """Production environment configuration."""
    
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'postgresql://user:password@localhost/skillscan'
    )
    
    # Ensure critical keys are set in production
    if not os.getenv('SECRET_KEY') or not os.getenv('JWT_SECRET_KEY'):
        raise ValueError(
            'SECRET_KEY and JWT_SECRET_KEY must be set in production'
        )


class TestingConfig(Config):
    """Testing environment configuration."""
    
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_EXPIRATION_HOURS = 1


# Configuration dictionary for factory pattern
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name='development'):
    """
    Get configuration class by name.
    
    Args:
        config_name (str): Configuration environment name.
        
    Returns:
        Config: Configuration class for the specified environment.
    """
    return config.get(config_name, config['default'])
