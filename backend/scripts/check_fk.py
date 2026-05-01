import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

db_url = os.getenv('SUPABASE_URL')
try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    print("Checking students table foreign keys...")
    
    cursor.execute("""
        SELECT 
            tc.constraint_name,
            kcu.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND kcu.table_name='students';
    """)
    
    print("\nForeign Key Constraints in students table:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}.{row[2]} -> {row[3]}.{row[4]}")
    
    # Check if users table exists
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema='public' AND table_name='users';
    """)
    
    if cursor.fetchone():
        print("\n✓ 'users' table exists")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='users'
            ORDER BY ordinal_position;
        """)
        print("\nColumns in 'users' table:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]}")
    else:
        print("\n✗ 'users' table does NOT exist")
        print("   The students table has a foreign key to a non-existent users table!")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
