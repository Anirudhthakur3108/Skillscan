# Backend Database Configuration

## Environment Variables (.env file)

```env
# Database Configuration
ENVIRONMENT=development

# PostgreSQL (Supabase)
DATABASE_URL=postgresql://[USER]:[PASSWORD]@[HOST]:[PORT]/[DATABASE]
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=skillscan

# SQLite (Local Development)
SQLITE_URL=sqlite:///./skillscan.db
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Create Tables
```bash
cd backend
python __init__.py --init
```

### 3. Create Tables + Demo Data
```bash
python __init__.py --demo
```

### 4. Verify Schema
```bash
python __init__.py --verify
```

### 5. Drop Tables (Caution!)
```bash
python __init__.py --drop
```

## Database Connection Examples

### Using DatabaseManager in Flask Routes

```python
from database import DatabaseManager
from models import Student

db = DatabaseManager.get_session()
try:
    students = db.query(Student).all()
finally:
    db.close()
```

### Using Context Manager

```python
from database import SessionLocal

with SessionLocal() as db:
    students = db.query(Student).all()
```

## SQLAlchemy Model Overview

### Available Models:
1. **Student** - User accounts (MBA/BCA)
2. **SkillsTaxonomy** - Skill definitions & benchmarks
3. **StudentSkill** - Skills claimed by students
4. **Assessment** - Assessment templates
5. **AssessmentResponse** - Student answers
6. **SkillScore** - Assessment results & AI analysis
7. **LearningPlan** - Personalized recommendations
8. **DemoAccount** - Pre-populated test accounts

### Key Features:
- ✓ Full ORM relationships with cascading deletes
- ✓ Automatic timestamp management (created_at, updated_at)
- ✓ Model validation (email, scores, proficiency, etc.)
- ✓ JSON columns for flexible data storage
- ✓ Unique constraints (student_skill, learning_plan)
- ✓ Optimized indexes for query performance
- ✓ __repr__ methods for debugging
- ✓ PostgreSQL and SQLite support

## Schema Files

- **models.py** - SQLAlchemy ORM definitions (All 8 models)
- **database.py** - Connection management & initialization
- **schema.sql** - PostgreSQL DDL statements
- **__init__.py** - Database setup CLI tool
