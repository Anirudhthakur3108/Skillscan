"""
Database Initialization Script

Connects to Supabase PostgreSQL and creates all tables based on SQLAlchemy models.
Run this once to initialize the database.

Usage:
    python db_init.py
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import inspect, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
load_dotenv()

# Import Flask and extensions
from flask import Flask
from extensions import db

def create_minimal_app():
    """Create Flask app without loading routes that depend on mistralai."""
    app = Flask(__name__)
    # Don't initialize db here - do it after config is set
    return app

def get_database_url():
    """Get database URL from environment."""
    db_url = os.getenv('SUPABASE_URL')
    if not db_url:
        raise ValueError('SUPABASE_URL environment variable not set. Check your .env file.')
    return db_url

def check_tables_exist(engine):
    """
    Check which tables already exist in the database.
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        Dict with table names and existence status
    """
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    expected_tables = {
        'students',
        'skills_taxonomy',
        'student_skills',
        'question_bank',
        'assessments',
        'assessment_responses',
        'skill_scores',
        'learning_plans',
        'alembic_version'  # Migration tracking table
    }
    
    status = {
        'existing': [t for t in existing_tables if t in expected_tables],
        'missing': [t for t in expected_tables if t not in existing_tables],
        'all_existing': set(existing_tables)
    }
    
    return status

def create_all_tables(app):
    """
    Create all tables in the database using SQLAlchemy ORM.
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        try:
            print('\n📦 Importing models and creating database tables...\n')
            # Import models only within app context
            from models import (
                Student, SkillTaxonomy, StudentSkill, QuestionBank,
                Assessment, AssessmentResponse, SkillScore, LearningPlan
            )
            
            db.create_all()
            print('✅ All tables created successfully!\n')
            return True
        except Exception as e:
            print(f'❌ Error creating tables: {str(e)}\n')
            import traceback
            traceback.print_exc()
            return False

def verify_tables(engine):
    """
    Verify all tables were created with correct structure.
    
    Args:
        engine: SQLAlchemy engine
    """
    inspector = inspect(engine)
    
    print('\n📋 Verifying table structure:\n')
    
    tables_to_check = [
        'students',
        'skills_taxonomy',
        'student_skills',
        'question_bank',
        'assessments',
        'assessment_responses',
        'skill_scores',
        'learning_plans'
    ]
    
    for table_name in tables_to_check:
        if table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            col_names = [col['name'] for col in columns]
            print(f'✅ {table_name}: {len(col_names)} columns')
            print(f'   Columns: {", ".join(col_names[:5])}...')
        else:
            print(f'❌ {table_name}: MISSING')

def test_connection(db_url):
    """
    Test connection to the database.
    
    Args:
        db_url: Database URL
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        print('\n🔗 Testing database connection...\n')
        engine = create_engine(db_url, echo=False)
        
        with engine.connect() as connection:
            result = connection.execute(text('SELECT 1'))
            print(f'✅ Connection successful!')
            print(f'   Database: {db_url.split("/")[-1]}\n')
            return True
    except Exception as e:
        print(f'❌ Connection failed: {str(e)}\n')
        return False

def main():
    """Main initialization flow."""
    print('\n' + '='*60)
    print('🚀 Supabase PostgreSQL Database Initialization')
    print('='*60)
    
    # Get database URL
    try:
        db_url = get_database_url()
        print(f'\n📍 Database: {db_url.split("@")[-1]}')
    except ValueError as e:
        print(f'\n❌ Error: {str(e)}')
        print('   Set SUPABASE_URL in .env file')
        return False
    
    # Test connection
    if not test_connection(db_url):
        print('   Troubleshooting:')
        print('   1. Check SUPABASE_URL in .env file')
        print('   2. Verify Supabase credentials')
        print('   3. Ensure database is accessible')
        return False
    
    # Check existing tables
    try:
        engine = create_engine(db_url, echo=False)
        status = check_tables_exist(engine)
        
        print('\n📊 Table Status:\n')
        if status['existing']:
            print(f'✅ Existing tables ({len(status["existing"])}):\n')
            for table in status['existing']:
                print(f'   • {table}')
        
        if status['missing']:
            print(f'\n⚠️  Missing tables ({len(status["missing"])}):\n')
            for table in status['missing']:
                print(f'   • {table}')
        
        if not status['missing']:
            print('\n✅ All tables already exist!')
            print('   Verifying structure...\n')
            verify_tables(engine)
            return True
    
    except SQLAlchemyError as e:
        print(f'❌ Error checking tables: {str(e)}')
        return False
    
    # Create missing tables
    try:
        print('\n' + '-'*60)
        app = create_minimal_app()
        
        # Configure database
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize db with the configured app
        db.init_app(app)
        
        if create_all_tables(app):
            verify_tables(engine)
            print('\n' + '='*60)
            print('✅ Database initialization complete!')
            print('='*60 + '\n')
            return True
        else:
            return False
    
    except Exception as e:
        print(f'❌ Initialization failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

