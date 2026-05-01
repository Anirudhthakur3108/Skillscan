import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

db_url = os.getenv('SUPABASE_URL')
try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    print("Adding missing columns to students table...")
    
    # Add all missing columns
    columns_to_add = [
        ("password_hash", "VARCHAR(256)"),
        ("full_name", "VARCHAR(100)"),
        ("user_type", "VARCHAR(50) DEFAULT 'student'"),
        ("profile_data", "JSONB"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"""
                ALTER TABLE students 
                ADD COLUMN IF NOT EXISTS {col_name} {col_type};
            """)
            print(f"  ✓ Added column: {col_name}")
        except Exception as e:
            print(f"  ! Column {col_name} might already exist: {e}")
    
    conn.commit()
    print("\n✓ Database schema updated successfully!")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
