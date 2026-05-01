import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

db_url = os.getenv('SUPABASE_URL')
try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    print("Dropping foreign key constraint from students table...")
    
    # Find and drop the foreign key constraint
    cursor.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name='students' AND constraint_type='FOREIGN KEY';
    """)
    
    constraints = cursor.fetchall()
    print(f"\nFound {len(constraints)} foreign key constraint(s):")
    
    for (constraint_name,) in constraints:
        print(f"  - Dropping constraint: {constraint_name}")
        cursor.execute(f"""
            ALTER TABLE students DROP CONSTRAINT "{constraint_name}";
        """)
    
    conn.commit()
    print("\n✓ Foreign key constraints dropped successfully!")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
