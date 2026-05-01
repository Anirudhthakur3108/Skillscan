#!/usr/bin/env python3
"""Fix missing columns in SkillTaxonomy table."""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text, inspect
from extensions import db
from models import SkillTaxonomy

load_dotenv()

def fix_skill_taxonomy_schema():
    """Check and add missing columns to skills_taxonomy table."""
    from app import create_app
    
    app = create_app()
    with app.app_context():
        # Get database inspector
        inspector = inspect(db.engine)
        
        # Check if table exists
        if 'skills_taxonomy' not in inspector.get_table_names():
            print("✗ skills_taxonomy table does not exist!")
            return False
        
        # Get existing columns
        existing_columns = [col['name'] for col in inspector.get_columns('skills_taxonomy')]
        print(f"📋 Existing columns in skills_taxonomy: {existing_columns}")
        
        # Expected columns from model
        expected_columns = {
            'skill_name': 'VARCHAR(100) NOT NULL',
            'category': 'VARCHAR(50)',
            'industry_benchmark': 'INTEGER',
            'subcategories': 'JSONB'
        }
        
        # Add missing columns
        missing_columns = [col for col in expected_columns.keys() if col not in existing_columns]
        
        if not missing_columns:
            print("✓ All columns exist!")
            return True
        
        print(f"\n📝 Adding missing columns: {missing_columns}")
        
        try:
            for column_name, column_def in expected_columns.items():
                if column_name not in existing_columns:
                    # Special handling for subcategories (JSONB might need to be JSON or TEXT)
                    if column_name == 'subcategories':
                        column_def = 'JSON'
                    
                    sql = f"ALTER TABLE skills_taxonomy ADD COLUMN IF NOT EXISTS {column_name} {column_def};"
                    print(f"  Running: {sql}")
                    db.session.execute(text(sql))
                    print(f"  ✓ {column_name} added")
            
            db.session.commit()
            print("\n✓ All missing columns added successfully!")
            
            # Verify
            inspector = inspect(db.engine)
            final_columns = [col['name'] for col in inspector.get_columns('skills_taxonomy')]
            print(f"✓ Final columns: {final_columns}")
            return True
            
        except Exception as e:
            print(f"\n✗ Error adding columns: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    if fix_skill_taxonomy_schema():
        print("\n✓ Database schema fixed!")
        sys.exit(0)
    else:
        print("\n✗ Failed to fix database schema!")
        sys.exit(1)
