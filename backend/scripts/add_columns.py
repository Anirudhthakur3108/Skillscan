import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

db_url = os.getenv('SUPABASE_URL')
try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Add password_hash column if it doesn't exist
    cursor.execute("""
        ALTER TABLE students 
        ADD COLUMN IF NOT EXISTS password_hash VARCHAR(256);
    """)
    
    # Add user_type column if it doesn't exist  
    cursor.execute("""
        ALTER TABLE students 
        ADD COLUMN IF NOT EXISTS user_type VARCHAR(50) DEFAULT 'student';
    """)
    
    conn.commit()
    print("? Columns added successfully")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
