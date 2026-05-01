import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

db_url = os.getenv('SUPABASE_URL')
try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    print("Adding missing columns to database tables...")
    
    # Add missing columns to assessments table
    assessments_columns = [
        ("student_id", "VARCHAR(36)"),
        ("assessment_type", "VARCHAR(50)"),
        ("questions", "JSONB"),
        ("status", "VARCHAR(50) DEFAULT 'generated'"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ]
    
    for col_name, col_type in assessments_columns:
        try:
            cursor.execute(f"""
                ALTER TABLE assessments 
                ADD COLUMN IF NOT EXISTS {col_name} {col_type};
            """)
            print(f"  ✓ assessments.{col_name} added")
        except Exception as e:
            print(f"  ! assessments.{col_name} error: {e}")
    
    # Add missing columns to student_skills table
    student_skills_columns = [
        ("proficiency_claimed", "INTEGER"),
        ("source", "VARCHAR(50)"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ]
    
    for col_name, col_type in student_skills_columns:
        try:
            cursor.execute(f"""
                ALTER TABLE student_skills 
                ADD COLUMN IF NOT EXISTS {col_name} {col_type};
            """)
            print(f"  ✓ student_skills.{col_name} added")
        except Exception as e:
            print(f"  ! student_skills.{col_name} error: {e}")
    
    # Add missing columns to skill_scores table
    skill_scores_columns = [
        ("ai_reasoning", "TEXT"),
        ("gap_identified", "BOOLEAN DEFAULT FALSE"),
        ("scored_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ]
    
    for col_name, col_type in skill_scores_columns:
        try:
            cursor.execute(f"""
                ALTER TABLE skill_scores 
                ADD COLUMN IF NOT EXISTS {col_name} {col_type};
            """)
            print(f"  ✓ skill_scores.{col_name} added")
        except Exception as e:
            print(f"  ! skill_scores.{col_name} error: {e}")
    
    conn.commit()
    print("\n✓ Database schema updated successfully!")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
