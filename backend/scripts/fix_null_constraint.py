import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

db_url = os.getenv('SUPABASE_URL')
try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Drop NOT NULL from student_id
    cursor.execute("""
        ALTER TABLE assessment_responses ALTER COLUMN student_id DROP NOT NULL;
    """)
    
    conn.commit()
    print("student_id made nullable successfully")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
