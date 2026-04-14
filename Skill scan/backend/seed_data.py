#!/usr/bin/env python3
"""
Seed Data Population Script for SkillScan MVP
Populates skills_taxonomy and creates demo user accounts with pre-filled skills.

Usage:
    python seed_data.py

Features:
    - Idempotent: Can be run multiple times safely
    - Comprehensive: 18 skills (9 MBA + 9 BCA)
    - Secure: Uses bcrypt for password hashing
    - Flexible: Works with both SQLite and PostgreSQL
"""

import bcrypt
import json
import sys
from datetime import datetime
from typing import List, Dict, Tuple

from app import create_app
from models import Student, SkillsTaxonomy, StudentSkill, db

# ============================================================================
# SKILL TAXONOMY DATA: 9 MBA + 9 BCA Skills
# ============================================================================

SKILLS_DATA = [
    # ===== MBA BUSINESS ANALYTICS SKILLS (9) =====
    {
        "name": "Python",
        "category": "Programming",
        "industry_benchmark": 7,
        "description": "Python programming language for data analysis",
        "subcategories": ["OOP", "Pandas", "NumPy", "Data Processing", "Automation"],
        "target_users": ["MBA_Analytics", "BCA"],
        "user_type": "MBA_Analytics"
    },
    {
        "name": "SQL",
        "category": "Databases",
        "industry_benchmark": 8,
        "description": "SQL for database queries and management",
        "subcategories": ["SELECT/WHERE", "JOINs", "Aggregation", "Subqueries", "Optimization"],
        "target_users": ["MBA_Analytics"],
        "user_type": "MBA_Analytics"
    },
    {
        "name": "Excel/VBA",
        "category": "Business Tools",
        "industry_benchmark": 7,
        "description": "Advanced Excel and VBA macro programming",
        "subcategories": ["Formulas", "Pivot Tables", "VLOOKUP", "VBA", "Dashboards"],
        "target_users": ["MBA_Analytics"],
        "user_type": "MBA_Analytics"
    },
    {
        "name": "Tableau",
        "category": "Visualization",
        "industry_benchmark": 6,
        "description": "Data visualization using Tableau",
        "subcategories": ["Dashboard Creation", "Data Sources", "Calculations", "Storytelling"],
        "target_users": ["MBA_Analytics"],
        "user_type": "MBA_Analytics"
    },
    {
        "name": "Power BI",
        "category": "Visualization",
        "industry_benchmark": 6,
        "description": "Business intelligence and data visualization with Power BI",
        "subcategories": ["DAX", "Power Query", "Dashboard Design", "Data Modeling"],
        "target_users": ["MBA_Analytics"],
        "user_type": "MBA_Analytics"
    },
    {
        "name": "Statistics",
        "category": "Data Science",
        "industry_benchmark": 7,
        "description": "Statistical analysis and inference",
        "subcategories": ["Descriptive Stats", "Hypothesis Testing", "Probability", "Distributions"],
        "target_users": ["MBA_Analytics"],
        "user_type": "MBA_Analytics"
    },
    {
        "name": "Data Analysis",
        "category": "Data Science",
        "industry_benchmark": 7,
        "description": "Data analysis and business analytics methodology",
        "subcategories": ["Data Exploration", "Analysis", "Insights", "Reporting", "Business Context"],
        "target_users": ["MBA_Analytics"],
        "user_type": "MBA_Analytics"
    },
    {
        "name": "R",
        "category": "Programming",
        "industry_benchmark": 6,
        "description": "R programming for statistical computing",
        "subcategories": ["ggplot2", "dplyr", "tidyr", "Statistical Models"],
        "target_users": ["MBA_Analytics"],
        "user_type": "MBA_Analytics"
    },
    {
        "name": "Machine Learning (Intro)",
        "category": "Data Science",
        "industry_benchmark": 5,
        "description": "Introduction to machine learning concepts and algorithms",
        "subcategories": ["Supervised Learning", "Unsupervised Learning", "Model Evaluation", "Preprocessing"],
        "target_users": ["MBA_Analytics"],
        "user_type": "MBA_Analytics"
    },
    # ===== BCA COMPUTER SCIENCE SKILLS (9) =====
    {
        "name": "Java",
        "category": "Programming",
        "industry_benchmark": 8,
        "description": "Java programming language for enterprise applications",
        "subcategories": ["OOP", "Collections", "Exceptions", "Multithreading", "Spring Framework"],
        "target_users": ["BCA"],
        "user_type": "BCA"
    },
    {
        "name": "C++",
        "category": "Programming",
        "industry_benchmark": 7,
        "description": "C++ systems programming language",
        "subcategories": ["Pointers", "Memory Management", "STL", "OOP", "Optimization"],
        "target_users": ["BCA"],
        "user_type": "BCA"
    },
    {
        "name": "JavaScript",
        "category": "Frontend",
        "industry_benchmark": 7,
        "description": "JavaScript for web development",
        "subcategories": ["ES6+", "DOM", "Async/Await", "Events", "APIs"],
        "target_users": ["BCA"],
        "user_type": "BCA"
    },
    {
        "name": "React",
        "category": "Frontend",
        "industry_benchmark": 6,
        "description": "React JavaScript library for UI development",
        "subcategories": ["Hooks", "State Management", "Component Design", "Routing", "Performance"],
        "target_users": ["BCA"],
        "user_type": "BCA"
    },
    {
        "name": "Web Development",
        "category": "Backend",
        "industry_benchmark": 6,
        "description": "Full-stack web development concepts",
        "subcategories": ["HTTP/REST", "HTML/CSS", "Backend Frameworks", "Databases", "Deployment"],
        "target_users": ["BCA"],
        "user_type": "BCA"
    },
    {
        "name": "SQL/Databases",
        "category": "Databases",
        "industry_benchmark": 7,
        "description": "SQL and relational database design",
        "subcategories": ["Normalization", "Query Optimization", "Indexing", "Transactions", "Design Patterns"],
        "target_users": ["BCA"],
        "user_type": "BCA"
    },
    {
        "name": "Data Structures",
        "category": "Core CS",
        "industry_benchmark": 8,
        "description": "Data structures and algorithms",
        "subcategories": ["Arrays/Linked Lists", "Trees/Graphs", "Sorting/Searching", "Complexity Analysis", "Design Patterns"],
        "target_users": ["BCA"],
        "user_type": "BCA"
    },
    {
        "name": "System Design",
        "category": "Architecture",
        "industry_benchmark": 6,
        "description": "Software architecture and system design",
        "subcategories": ["Design Patterns", "Scalability", "Microservices", "Caching", "Database Design"],
        "target_users": ["BCA"],
        "user_type": "BCA"
    },
]

# ============================================================================
# DEMO ACCOUNTS DATA
# ============================================================================

DEMO_ACCOUNTS = [
    {
        "email": "demo_mba@skillscan.com",
        "password": "demo123",
        "full_name": "Arjun Sharma",
        "user_type": "MBA_Analytics",
        "skills": [
            ("Python", 6),
            ("SQL", 5),
            ("Tableau", 3)
        ]
    },
    {
        "email": "demo_bca@skillscan.com",
        "password": "demo123",
        "full_name": "Priya Gupta",
        "user_type": "BCA",
        "skills": [
            ("Python", 7),
            ("Java", 6),
            ("React", 4)
        ]
    }
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def skill_exists(skill_name: str) -> bool:
    """Check if skill already exists in database."""
    return db.session.query(SkillsTaxonomy).filter_by(name=skill_name).first() is not None


def student_exists(email: str) -> bool:
    """Check if student already exists in database."""
    return db.session.query(Student).filter_by(email=email).first() is not None


def get_skill_by_name(skill_name: str) -> SkillsTaxonomy:
    """Retrieve skill by name."""
    return db.session.query(SkillsTaxonomy).filter_by(name=skill_name).first()


# ============================================================================
# SEEDING FUNCTIONS
# ============================================================================

def seed_skills() -> int:
    """
    Populate skills_taxonomy table with all 18 skills.
    
    Returns:
        Number of skills added (skips duplicates)
    """
    print("\n" + "="*70)
    print("SEEDING SKILLS TAXONOMY")
    print("="*70)
    
    skills_added = 0
    
    for skill_data in SKILLS_DATA:
        skill_name = skill_data["name"]
        
        if skill_exists(skill_name):
            print(f"⏭️  SKIP: {skill_name} (already exists)")
            continue
        
        try:
            skill = SkillsTaxonomy(
                name=skill_name,
                category=skill_data["category"],
                industry_benchmark=skill_data["industry_benchmark"],
                description=skill_data["description"],
                subcategories=json.dumps(skill_data["subcategories"]),
            )
            db.session.add(skill)
            skills_added += 1
            print(f"✅ ADDED: {skill_name} ({skill_data['category']})")
        
        except Exception as e:
            print(f"❌ ERROR adding {skill_name}: {str(e)}")
            db.session.rollback()
            return 0
    
    try:
        db.session.commit()
        print(f"\n✨ Successfully added {skills_added} new skills")
        return skills_added
    except Exception as e:
        print(f"❌ ERROR committing skills: {str(e)}")
        db.session.rollback()
        return 0


def seed_demo_accounts() -> int:
    """
    Create demo user accounts with pre-filled skills.
    
    Returns:
        Number of accounts added
    """
    print("\n" + "="*70)
    print("SEEDING DEMO ACCOUNTS")
    print("="*70)
    
    accounts_added = 0
    
    for account_data in DEMO_ACCOUNTS:
        email = account_data["email"]
        
        if student_exists(email):
            print(f"⏭️  SKIP: {email} (account already exists)")
            continue
        
        try:
            # Create student account
            hashed_password = hash_password(account_data["password"])
            student = Student(
                email=email,
                password_hash=hashed_password,
                full_name=account_data["full_name"],
                user_type=account_data["user_type"],
                is_verified=True,
                created_at=datetime.utcnow()
            )
            db.session.add(student)
            db.session.flush()  # Get the student ID
            
            print(f"✅ CREATED: {account_data['full_name']} ({email})")
            
            # Add pre-filled skills
            for skill_name, proficiency_level in account_data["skills"]:
                skill = get_skill_by_name(skill_name)
                
                if not skill:
                    print(f"⚠️  WARNING: Skill '{skill_name}' not found")
                    continue
                
                student_skill = StudentSkill(
                    student_id=student.id,
                    skill_id=skill.id,
                    proficiency_level=proficiency_level,
                    source="self_reported",
                    verified=False,
                    created_at=datetime.utcnow()
                )
                db.session.add(student_skill)
                print(f"  └─ Added skill: {skill_name} (Level: {proficiency_level}/10)")
            
            accounts_added += 1
        
        except Exception as e:
            print(f"❌ ERROR creating account {email}: {str(e)}")
            db.session.rollback()
            return 0
    
    try:
        db.session.commit()
        print(f"\n✨ Successfully added {accounts_added} demo accounts")
        return accounts_added
    except Exception as e:
        print(f"❌ ERROR committing accounts: {str(e)}")
        db.session.rollback()
        return 0


def print_summary():
    """Print database summary after seeding."""
    print("\n" + "="*70)
    print("DATABASE SUMMARY")
    print("="*70)
    
    skill_count = db.session.query(SkillsTaxonomy).count()
    student_count = db.session.query(Student).count()
    student_skill_count = db.session.query(StudentSkill).count()
    
    print(f"📊 Total Skills: {skill_count}")
    print(f"👤 Total Students: {student_count}")
    print(f"🎯 Student-Skill Mappings: {student_skill_count}")
    
    if student_count > 0:
        print("\n📝 Demo Accounts:")
        students = db.session.query(Student).all()
        for student in students:
            skills_count = len(student.skills)
            print(f"  • {student.full_name} ({student.email})")
            print(f"    Type: {student.user_type} | Skills: {skills_count}")


def main():
    """Main seeding function."""
    print("\n" + "🌱 "*20)
    print("SKILLSCAN MVP - DATABASE SEEDING")
    print("🌱 "*20)
    print(f"Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables (if they don't exist)
            print("\n🔧 Creating database tables...")
            db.create_all()
            print("✅ Database tables ready")
            
            # Seed skills
            skills_added = seed_skills()
            
            # Seed demo accounts
            if skills_added > 0 or skill_exists("Python"):
                accounts_added = seed_demo_accounts()
            else:
                print("\n⚠️  Skipping demo accounts (no skills in database)")
                accounts_added = 0
            
            # Print summary
            print_summary()
            
            # Final status
            print("\n" + "="*70)
            if skills_added > 0 or accounts_added > 0:
                print("✅ SEEDING COMPLETED SUCCESSFULLY!")
            else:
                print("ℹ️  Database already seeded (no new data added)")
            print("="*70 + "\n")
            
            return 0
        
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: {str(e)}")
            print("="*70 + "\n")
            return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
