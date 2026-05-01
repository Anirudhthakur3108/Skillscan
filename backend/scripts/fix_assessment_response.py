import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

db_url = os.getenv('SUPABASE_URL')
try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Add columns to assessment_responses
    cursor.execute("""
        ALTER TABLE assessment_responses 
        ADD COLUMN IF NOT EXISTS student_response JSONB,
        ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP,
        ADD COLUMN IF NOT EXISTS ai_feedback JSONB;
    """)

    # Add columns to skill_scores
    cursor.execute("""
        ALTER TABLE skill_scores 
        ADD COLUMN IF NOT EXISTS ai_reasoning TEXT,
        ADD COLUMN IF NOT EXISTS gap_identified BOOLEAN,
        ADD COLUMN IF NOT EXISTS scored_at TIMESTAMP;
    """)

    # Add columns to assessments
    cursor.execute("""
        ALTER TABLE assessments
        ADD COLUMN IF NOT EXISTS assessment_type VARCHAR(50),
        ADD COLUMN IF NOT EXISTS questions JSONB,
        ADD COLUMN IF NOT EXISTS status VARCHAR(50),
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP,
        ADD COLUMN IF NOT EXISTS difficulty_level INTEGER DEFAULT 5,
        ADD COLUMN IF NOT EXISTS num_questions INTEGER DEFAULT 5,
        ADD COLUMN IF NOT EXISTS time_limit_minutes INTEGER DEFAULT 30,
        ADD COLUMN IF NOT EXISTS proficiency_claimed INTEGER;
    """)

    # Add columns to question_bank
    cursor.execute("""
        ALTER TABLE question_bank
        ADD COLUMN IF NOT EXISTS question_count INTEGER DEFAULT 0;
    """)

    conn.commit()
    print("Columns added successfully")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
