import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

db_url = os.getenv('SUPABASE_URL')
try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    print("Fixing students table ID sequence...")
    
    # Check current table structure
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name='students'
        ORDER BY ordinal_position;
    """)
    
    print("\nCurrent columns in students table:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
    
    # Drop and recreate ID column with SERIAL/BIGSERIAL type
    print("\nRecreating ID column with auto-increment...")
    
    # First, check if we need to drop a sequence
    cursor.execute("""
        SELECT sequence_name 
        FROM information_schema.sequences 
        WHERE sequence_name LIKE 'students_%_seq%'
        LIMIT 1;
    """)
    
    # Attempt to create a sequence for the id column if it doesn't exist
    cursor.execute("""
        CREATE SEQUENCE IF NOT EXISTS students_id_seq;
    """)
    
    # Update the id column to use the sequence as default
    cursor.execute("""
        ALTER TABLE students 
        ALTER COLUMN id SET DEFAULT nextval('students_id_seq');
    """)
    
    # Set the sequence to start after the highest existing ID
    cursor.execute("""
        SELECT COALESCE(MAX(id), 0) FROM students;
    """)
    max_id = cursor.fetchone()[0]
    
    cursor.execute(f"""
        SELECT setval('students_id_seq', {max_id + 1});
    """)
    
    conn.commit()
    print(f"✓ ID sequence fixed! Next ID will be: {max_id + 1}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
