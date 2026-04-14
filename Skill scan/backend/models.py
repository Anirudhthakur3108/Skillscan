"""
SkillScan MVP - SQLAlchemy ORM Models
Database models for all 8 tables with relationships, validation, and indexes
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, Text, Float, 
    ForeignKey, UniqueConstraint, Index, Boolean, Numeric, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from decimal import Decimal

Base = declarative_base()


class Student(Base):
    """Students table - stores user profile and authentication"""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    user_type = Column(String(10), nullable=False)  # MBA or BCA
    profile_data = Column(JSON, default=dict)  # Flexible JSON for additional user info
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    student_skills = relationship("StudentSkill", back_populates="student", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="student", cascade="all, delete-orphan")
    assessment_responses = relationship("AssessmentResponse", back_populates="student", cascade="all, delete-orphan")
    skill_scores = relationship("SkillScore", back_populates="student", cascade="all, delete-orphan")
    learning_plans = relationship("LearningPlan", back_populates="student", cascade="all, delete-orphan")

    # Validations
    @validates("user_type")
    def validate_user_type(self, key, value):
        if value not in ["MBA", "BCA"]:
            raise ValueError("user_type must be 'MBA' or 'BCA'")
        return value

    @validates("email")
    def validate_email(self, key, value):
        if "@" not in value or "." not in value:
            raise ValueError("Invalid email format")
        return value.lower()

    def __repr__(self):
        return f"<Student(id={self.id}, email='{self.email}', name='{self.full_name}', type='{self.user_type}')>"


class SkillsTaxonomy(Base):
    """Skills taxonomy table - stores skill definitions and benchmarks"""
    __tablename__ = "skills_taxonomy"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    industry_benchmark = Column(Integer, nullable=False)  # 1-10 scale
    subcategories = Column(JSON, default=list)  # JSON array of subcategories
    target_users = Column(JSON, default=list)  # JSON array: ["MBA", "BCA"] or specific

    # Relationships
    student_skills = relationship("StudentSkill", back_populates="skill", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="skill", cascade="all, delete-orphan")
    skill_scores = relationship("SkillScore", back_populates="skill", cascade="all, delete-orphan")
    learning_plans = relationship("LearningPlan", back_populates="skill", cascade="all, delete-orphan")

    # Validations
    @validates("industry_benchmark")
    def validate_benchmark(self, key, value):
        if not (1 <= value <= 10):
            raise ValueError("industry_benchmark must be between 1-10")
        return value

    def __repr__(self):
        return f"<SkillsTaxonomy(id={self.id}, name='{self.name}', category='{self.category}', benchmark={self.industry_benchmark})>"


class StudentSkill(Base):
    """Student skills mapping - tracks skills claimed by students"""
    __tablename__ = "student_skills"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills_taxonomy.id", ondelete="CASCADE"), nullable=False, index=True)
    proficiency_claimed = Column(Integer, nullable=False)  # 1-10 scale
    source = Column(String(50), nullable=False)  # resume, manual, assessment
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Unique constraint: one skill per student
    __table_args__ = (
        UniqueConstraint("student_id", "skill_id", name="uq_student_skill"),
        Index("idx_student_skills_created", "student_id", "created_at"),
    )

    # Relationships
    student = relationship("Student", back_populates="student_skills")
    skill = relationship("SkillsTaxonomy", back_populates="student_skills")

    # Validations
    @validates("proficiency_claimed")
    def validate_proficiency(self, key, value):
        if not (1 <= value <= 10):
            raise ValueError("proficiency_claimed must be between 1-10")
        return value

    @validates("source")
    def validate_source(self, key, value):
        if value not in ["resume", "manual", "assessment"]:
            raise ValueError("source must be 'resume', 'manual', or 'assessment'")
        return value

    def __repr__(self):
        return f"<StudentSkill(id={self.id}, student_id={self.student_id}, skill_id={self.skill_id}, proficiency={self.proficiency_claimed})>"


class Assessment(Base):
    """Assessments table - stores assessment templates and status"""
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills_taxonomy.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_type = Column(String(50), nullable=False)  # mcq, coding, case_study
    difficulty_level = Column(String(20), nullable=False)  # easy, medium, hard
    questions = Column(JSON, nullable=False)  # JSON array of questions
    status = Column(String(50), nullable=False)  # generated, in_progress, completed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Indexes for frequently queried columns
    __table_args__ = (
        Index("idx_assessment_student_skill_difficulty", "student_id", "skill_id", "difficulty_level"),
        Index("idx_assessment_status", "student_id", "status"),
        Index("idx_assessment_created", "student_id", "created_at"),
    )

    # Relationships
    student = relationship("Student", back_populates="assessments")
    skill = relationship("SkillsTaxonomy", back_populates="assessments")
    responses = relationship("AssessmentResponse", back_populates="assessment", cascade="all, delete-orphan")
    skill_scores = relationship("SkillScore", back_populates="assessment", cascade="all, delete-orphan")

    # Validations
    @validates("assessment_type")
    def validate_type(self, key, value):
        if value not in ["mcq", "coding", "case_study"]:
            raise ValueError("assessment_type must be 'mcq', 'coding', or 'case_study'")
        return value

    @validates("difficulty_level")
    def validate_difficulty(self, key, value):
        if value not in ["easy", "medium", "hard"]:
            raise ValueError("difficulty_level must be 'easy', 'medium', or 'hard'")
        return value

    @validates("status")
    def validate_status(self, key, value):
        if value not in ["generated", "in_progress", "completed"]:
            raise ValueError("status must be 'generated', 'in_progress', or 'completed'")
        return value

    def __repr__(self):
        return f"<Assessment(id={self.id}, student_id={self.student_id}, skill_id={self.skill_id}, type='{self.assessment_type}', status='{self.status}')>"


class AssessmentResponse(Base):
    """Assessment responses table - stores student answers to assessments"""
    __tablename__ = "assessment_responses"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    responses = Column(JSON, nullable=False)  # JSON object with student answers
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    assessment = relationship("Assessment", back_populates="responses")
    student = relationship("Student", back_populates="assessment_responses")

    def __repr__(self):
        return f"<AssessmentResponse(id={self.id}, assessment_id={self.assessment_id}, student_id={self.student_id}, submitted_at='{self.submitted_at}')>"


class SkillScore(Base):
    """Skill scores table - stores assessment results and AI analysis"""
    __tablename__ = "skill_scores"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills_taxonomy.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Integer, nullable=False)  # 1-10 scale
    gaps_identified = Column(JSON, default=list)  # JSON array of identified gaps
    reasoning = Column(Text, nullable=True)  # AI reasoning for the score
    ai_confidence = Column(Numeric(precision=3, scale=2), nullable=False)  # 0-1 decimal
    scored_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Indexes for frequently queried columns
    __table_args__ = (
        Index("idx_skill_score_student_skill", "student_id", "skill_id"),
        Index("idx_skill_score_timestamp", "student_id", "scored_at"),
    )

    # Relationships
    student = relationship("Student", back_populates="skill_scores")
    skill = relationship("SkillsTaxonomy", back_populates="skill_scores")
    assessment = relationship("Assessment", back_populates="skill_scores")

    # Validations
    @validates("score")
    def validate_score(self, key, value):
        if not (1 <= value <= 10):
            raise ValueError("score must be between 1-10")
        return value

    @validates("ai_confidence")
    def validate_confidence(self, key, value):
        if not (0 <= float(value) <= 1):
            raise ValueError("ai_confidence must be between 0-1")
        return value

    def __repr__(self):
        return f"<SkillScore(id={self.id}, student_id={self.student_id}, skill_id={self.skill_id}, score={self.score}, confidence={self.ai_confidence})>"


class LearningPlan(Base):
    """Learning plans table - stores personalized learning recommendations"""
    __tablename__ = "learning_plans"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills_taxonomy.id", ondelete="CASCADE"), nullable=False, index=True)
    gap_category = Column(String(100), nullable=False)  # Type of gap identified
    recommendations = Column(JSON, default=list)  # JSON array with type/title/provider/duration
    estimated_hours = Column(Integer, nullable=False)  # Total hours to close gap
    priority_score = Column(Integer, nullable=False)  # 1-5 scale
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Unique constraint: one plan per student per skill per gap_category
    __table_args__ = (
        UniqueConstraint("student_id", "skill_id", "gap_category", name="uq_learning_plan"),
        Index("idx_learning_plan_priority", "student_id", "priority_score"),
    )

    # Relationships
    student = relationship("Student", back_populates="learning_plans")
    skill = relationship("SkillsTaxonomy", back_populates="learning_plans")

    # Validations
    @validates("priority_score")
    def validate_priority(self, key, value):
        if not (1 <= value <= 5):
            raise ValueError("priority_score must be between 1-5")
        return value

    @validates("estimated_hours")
    def validate_hours(self, key, value):
        if value < 0:
            raise ValueError("estimated_hours must be non-negative")
        return value

    def __repr__(self):
        return f"<LearningPlan(id={self.id}, student_id={self.student_id}, skill_id={self.skill_id}, gap='{self.gap_category}', priority={self.priority_score})>"


class DemoAccount(Base):
    """Demo accounts table - pre-populated accounts for testing"""
    __tablename__ = "demo_accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    user_type = Column(String(10), nullable=False)  # MBA or BCA
    prefilled_data = Column(JSON, default=dict)  # Skills, assessments, scores
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Validations
    @validates("user_type")
    def validate_user_type(self, key, value):
        if value not in ["MBA", "BCA"]:
            raise ValueError("user_type must be 'MBA' or 'BCA'")
        return value

    @validates("email")
    def validate_email(self, key, value):
        if "@" not in value or "." not in value:
            raise ValueError("Invalid email format")
        return value.lower()

    def __repr__(self):
        return f"<DemoAccount(id={self.id}, username='{self.username}', email='{self.email}', type='{self.user_type}')>"
