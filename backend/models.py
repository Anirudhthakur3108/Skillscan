from datetime import datetime
from extensions import db

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.String(36), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)  # Extended for bcrypt hashes
    full_name = db.Column(db.String(100), nullable=True)
    user_type = db.Column(db.String(50), default='student', nullable=False)  # student, educator, admin
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
    question_count = db.Column(db.Integer, default=0)  # Total questions cached for this skill
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudentSkill(db.Model):
    __tablename__ = 'student_skills'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(36), db.ForeignKey('students.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills_taxonomy.id'), nullable=False)
    proficiency_claimed = db.Column(db.Integer, nullable=True)
    source = db.Column(db.String(50)) # manual, resume
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Assessment(db.Model):
    __tablename__ = 'assessments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(36), db.ForeignKey('students.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills_taxonomy.id'), nullable=False)
    assessment_type = db.Column(db.String(50))
    questions = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(50), default='generated') # generated, in_progress, completed
    difficulty_level = db.Column(db.Integer, nullable=False, default=5)  # 1-10
    num_questions = db.Column(db.Integer, nullable=False, default=5)  # auto-set based on difficulty
    time_limit_minutes = db.Column(db.Integer, nullable=False, default=30)  # auto-set based on difficulty
    proficiency_claimed = db.Column(db.Integer, nullable=True)  # user-selected 1-10
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AssessmentResponse(db.Model):
    __tablename__ = 'assessment_responses'
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    student_response = db.Column(db.JSON, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    ai_feedback = db.Column(db.JSON, nullable=True)

class AssessmentScoreDetail(db.Model):
    __tablename__ = 'assessment_score_details'
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    
    # MCQ scores (auto-calculated)
    mcq_count = db.Column(db.Integer, nullable=False)
    mcq_correct = db.Column(db.Integer, nullable=False)
    mcq_score = db.Column(db.Integer, nullable=False)  # 0-10
    
    # Long answer scores (AI-evaluated)
    long_answer_score = db.Column(db.Integer, nullable=True)  # 0-10 from AI
    case_study_score = db.Column(db.Integer, nullable=True)  # 0-10 from AI
    
    # AI feedback breakdown
    mcq_feedback = db.Column(db.JSON, nullable=True)
    long_answer_feedback = db.Column(db.JSON, nullable=True)
    case_study_feedback = db.Column(db.JSON, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SkillScore(db.Model):
    __tablename__ = 'skill_scores'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(36), db.ForeignKey('students.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills_taxonomy.id'), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    ai_reasoning = db.Column(db.Text, nullable=True)
    gap_identified = db.Column(db.Boolean, default=False)
    scored_at = db.Column(db.DateTime, default=datetime.utcnow)

class LearningPlan(db.Model):
    __tablename__ = 'learning_plans'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(36), db.ForeignKey('students.id'), nullable=False)
    skill_gap_id = db.Column(db.Integer, db.ForeignKey('skill_scores.id'), nullable=False)
    recommendations = db.Column(db.JSON, nullable=False)
    estimated_hours = db.Column(db.Integer, nullable=True)
    priority = db.Column(db.Integer, default=3)
    youtube_resources = db.Column(db.JSON, nullable=True)  # [{title, url, duration_minutes}, ...]
    website_resources = db.Column(db.JSON, nullable=True)  # [{title, url, category, estimated_hours}, ...]
    timeline_weeks = db.Column(db.Integer, nullable=True)  # total duration
    is_reusable = db.Column(db.Boolean, default=True)  # can be used for similar gaps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
