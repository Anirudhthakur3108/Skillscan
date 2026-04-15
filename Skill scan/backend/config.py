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
    
    # Assessment Configuration
    ASSESSMENT_CONFIG = {
        'mcq': {
            'duration': int(os.getenv('ASSESSMENT_MCQ_DURATION', 360)),  # 6 minutes
            'questions': int(os.getenv('ASSESSMENT_MCQ_QUESTIONS', 5))
        },
        'coding': {
            'duration': int(os.getenv('ASSESSMENT_CODING_DURATION', 3600)),  # 60 minutes
            'questions': int(os.getenv('ASSESSMENT_CODING_QUESTIONS', 2))
        },
        'case_study': {
            'duration': int(os.getenv('ASSESSMENT_CASESTUDY_DURATION', 1800)),  # 30 minutes
            'questions': int(os.getenv('ASSESSMENT_CASESTUDY_QUESTIONS', 1))
        }
    }
    
    # Assessment Scoring
    ASSESSMENT_PASSING_SCORE = int(os.getenv('ASSESSMENT_PASSING_SCORE', 70))
    ASSESSMENT_UNLOCK_THRESHOLD = int(os.getenv('ASSESSMENT_UNLOCK_THRESHOLD', 70))
    
    # Badge Mapping (score ranges)
    ASSESSMENT_BADGE_MAPPING = {
        'excellent': (90, 100),
        'good': (80, 89),
        'fair': (70, 79),
        'needs_work': (0, 69)
    }
    
    # Allowed difficulty levels
    ASSESSMENT_DIFFICULTIES = ['easy', 'medium', 'hard']
    ASSESSMENT_TYPES = ['mcq', 'coding', 'case_study']


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
