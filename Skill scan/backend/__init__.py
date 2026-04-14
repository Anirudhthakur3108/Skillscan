"""
SkillScan MVP - Database Initialization Script
Use this to create tables and verify database setup
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from database import DatabaseManager
from models import Base, Student, SkillsTaxonomy, StudentSkill, Assessment, AssessmentResponse, SkillScore, LearningPlan, DemoAccount


def initialize_database(environment: str = "development", echo: bool = False):
    """Initialize database with all tables"""
    print(f"[INIT] Starting database initialization for {environment}...")
    
    # Initialize database manager
    DatabaseManager.initialize(echo=echo)
    
    # Create all tables
    DatabaseManager.create_all_tables()
    
    print("[INIT] Database initialization complete!")
    print("\nTables created:")
    print("  ✓ students")
    print("  ✓ skills_taxonomy")
    print("  ✓ student_skills")
    print("  ✓ assessments")
    print("  ✓ assessment_responses")
    print("  ✓ skill_scores")
    print("  ✓ learning_plans")
    print("  ✓ demo_accounts")


def drop_database():
    """Drop all tables (WARNING: Data loss!)"""
    response = input("⚠️  WARNING: This will delete ALL data! Type 'yes' to confirm: ")
    if response.lower() == "yes":
        DatabaseManager.drop_all_tables()
        print("[DROP] All tables dropped successfully")
    else:
        print("[DROP] Operation cancelled")


def create_demo_data():
    """Create sample demo accounts and skills"""
    print("[DEMO] Creating demo data...")
    
    db = DatabaseManager.get_session()
    
    try:
        # Demo skills
        demo_skills = [
            {
                "name": "Python Programming",
                "category": "Technical",
                "description": "Core Python programming skills including OOP, data structures, and libraries",
                "industry_benchmark": 8,
                "subcategories": ["OOP", "Data Structures", "Libraries"],
                "target_users": ["BCA", "MBA"]
            },
            {
                "name": "Data Analysis",
                "category": "Analytics",
                "description": "Data analysis using Python, pandas, and statistical methods",
                "industry_benchmark": 7,
                "subcategories": ["Pandas", "Statistics", "Visualization"],
                "target_users": ["MBA", "BCA"]
            },
            {
                "name": "SQL Database Design",
                "category": "Technical",
                "description": "SQL query writing, database design, and optimization",
                "industry_benchmark": 8,
                "subcategories": ["Query Writing", "Schema Design", "Optimization"],
                "target_users": ["BCA"]
            },
            {
                "name": "Business Analytics",
                "category": "Analytics",
                "description": "Business intelligence, data-driven decision making",
                "industry_benchmark": 7,
                "subcategories": ["BI Tools", "Dashboards", "KPIs"],
                "target_users": ["MBA"]
            },
        ]
        
        for skill_data in demo_skills:
            skill = SkillsTaxonomy(**skill_data)
            db.add(skill)
        
        db.commit()
        print(f"[DEMO] Created {len(demo_skills)} demo skills")
        
        # Demo accounts
        from werkzeug.security import generate_password_hash
        
        demo_accounts = [
            {
                "username": "mba_student_001",
                "email": "mba.student@skillscan.demo",
                "password_hash": generate_password_hash("demo_password_123"),
                "user_type": "MBA",
                "prefilled_data": {
                    "skills": ["Data Analysis", "Business Analytics"],
                    "created_at": "2026-04-01"
                }
            },
            {
                "username": "bca_student_001",
                "email": "bca.student@skillscan.demo",
                "password_hash": generate_password_hash("demo_password_123"),
                "user_type": "BCA",
                "prefilled_data": {
                    "skills": ["Python Programming", "SQL Database Design"],
                    "created_at": "2026-04-01"
                }
            },
        ]
        
        for account_data in demo_accounts:
            account = DemoAccount(**account_data)
            db.add(account)
        
        db.commit()
        print(f"[DEMO] Created {len(demo_accounts)} demo accounts")
        print("\nDemo credentials:")
        print("  MBA: mba.student@skillscan.demo / demo_password_123")
        print("  BCA: bca.student@skillscan.demo / demo_password_123")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to create demo data: {e}")
    finally:
        db.close()


def verify_schema():
    """Verify schema and display table info"""
    print("[VERIFY] Checking database schema...")
    
    db = DatabaseManager.get_session()
    
    try:
        # Check table existence
        inspector_tables = [
            "students",
            "skills_taxonomy",
            "student_skills",
            "assessments",
            "assessment_responses",
            "skill_scores",
            "learning_plans",
            "demo_accounts"
        ]
        
        print("\nTable Status:")
        for table_name in inspector_tables:
            try:
                result = db.execute(f"SELECT COUNT(*) FROM {table_name}").scalar()
                print(f"  ✓ {table_name:30} ({result} rows)")
            except:
                print(f"  ✗ {table_name:30} (NOT FOUND)")
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SkillScan Database Setup")
    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--drop", action="store_true", help="Drop all tables")
    parser.add_argument("--demo", action="store_true", help="Create demo data")
    parser.add_argument("--verify", action="store_true", help="Verify schema")
    parser.add_argument("--env", default="development", help="Environment (development/production)")
    parser.add_argument("--echo", action="store_true", help="Echo SQL queries")
    
    args = parser.parse_args()
    
    if args.init:
        initialize_database(args.env, args.echo)
    elif args.drop:
        drop_database()
    elif args.demo:
        initialize_database(args.env, args.echo)
        create_demo_data()
    elif args.verify:
        verify_schema()
    else:
        # Default: initialize
        initialize_database(args.env, args.echo)
