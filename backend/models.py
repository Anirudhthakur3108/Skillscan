from datetime import datetime
from extensions import db

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    profile_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SkillTaxonomy(db.Model):
    __tablename__ = 'skills_taxonomy'
    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    industry_benchmark = db.Column(db.Integer)
    subcategories = db.Column(db.JSON, nullable=True)

class QuestionBank(db.Model):
    __tablename__ = 'question_bank'
    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills_taxonomy.id'), nullable=False)
    question_type = db.Column(db.String(50), nullable=False) # MCQ, Coding, CaseStudy
    difficulty_level = db.Column(db.Integer, nullable=True)
    question_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudentSkill(db.Model):
    __tablename__ = 'student_skills'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills_taxonomy.id'), nullable=False)
    proficiency_claimed = db.Column(db.Integer, nullable=True)
    source = db.Column(db.String(50)) # manual, resume
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Assessment(db.Model):
    __tablename__ = 'assessments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills_taxonomy.id'), nullable=False)
    assessment_type = db.Column(db.String(50))
    questions = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(50), default='generated') # generated, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AssessmentResponse(db.Model):
    __tablename__ = 'assessment_responses'
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    student_response = db.Column(db.JSON, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    ai_feedback = db.Column(db.JSON, nullable=True)

class SkillScore(db.Model):
    __tablename__ = 'skill_scores'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills_taxonomy.id'), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    ai_reasoning = db.Column(db.Text, nullable=True)
    gap_identified = db.Column(db.Boolean, default=False)
    scored_at = db.Column(db.DateTime, default=datetime.utcnow)

class LearningPlan(db.Model):
    __tablename__ = 'learning_plans'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    skill_gap_id = db.Column(db.Integer, db.ForeignKey('skill_scores.id'), nullable=False)
    recommendations = db.Column(db.JSON, nullable=False)
    estimated_hours = db.Column(db.Integer, nullable=True)
    priority = db.Column(db.Integer, default=3)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
