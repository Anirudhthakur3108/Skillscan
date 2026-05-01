#!/usr/bin/env python3
"""Migrate SkillTaxonomy table to match model expectations."""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text, inspect
from extensions import db

load_dotenv()

def migrate_skill_taxonomy():
    """Rename 'name' column to 'skill_name' and add missing columns."""
    from app import create_app
    
    app = create_app()
    with app.app_context():
        # Get database inspector
        inspector = inspect(db.engine)
        
        # Get existing columns
        existing_columns = [col['name'] for col in inspector.get_columns('skills_taxonomy')]
        print(f"📋 Current columns: {existing_columns}")
        
        try:
            # Step 1: Check if 'name' column exists and needs to be renamed
            if 'name' in existing_columns and 'skill_name' not in existing_columns:
                print("\n📝 Step 1: Renaming 'name' column to 'skill_name'...")
                sql = "ALTER TABLE skills_taxonomy RENAME COLUMN name TO skill_name;"
                print(f"  Running: {sql}")
                db.session.execute(text(sql))
                db.session.commit()
                print("  ✓ Column renamed")
            
            # Refresh inspector
            inspector = inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('skills_taxonomy')]
            print(f"\n📋 Columns after rename: {existing_columns}")
            
            # Step 2: Add missing columns (nullable versions to avoid constraint violations)
            missing_columns = {
                'industry_benchmark': 'INTEGER',
                'subcategories': 'JSON'
            }
            
            print("\n📝 Step 2: Adding missing columns...")
            for column_name, column_type in missing_columns.items():
                if column_name not in existing_columns:
                    sql = f"ALTER TABLE skills_taxonomy ADD COLUMN IF NOT EXISTS {column_name} {column_type};"
                    print(f"  Running: {sql}")
                    db.session.execute(text(sql))
                    print(f"  ✓ {column_name} added")
            
            db.session.commit()
            print("\n✓ All migrations completed successfully!")
            
            # Verify final state
            inspector = inspect(db.engine)
            final_columns = [col['name'] for col in inspector.get_columns('skills_taxonomy')]
            print(f"✓ Final columns: {final_columns}")
            
            # Check constraint on skill_name
            constraints = inspector.get_columns('skills_taxonomy')
            for col in constraints:
                if col['name'] == 'skill_name':
                    print(f"✓ skill_name column nullable: {col['nullable']}")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error during migration: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == "__main__":
    if migrate_skill_taxonomy():
        print("\n✓ Database migration successful!")
        sys.exit(0)
    else:
        print("\n✗ Database migration failed!")
        sys.exit(1)
