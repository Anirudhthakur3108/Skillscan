from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional, Dict, Any

# ─── Authentication ────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

# ─── Skills ───────────────────────────────────────────────────────────────────

class ManualSkillRequest(BaseModel):
    skill_name: str
    proficiency_claimed: int  # 1–10

    @field_validator('proficiency_claimed')
    @classmethod
    def proficiency_range(cls, v):
        if not 1 <= v <= 10:
            raise ValueError('Proficiency must be between 1 and 10')
        return v

# ─── AI Question Generation (Mistral Output Schemas) ──────────────────────────

class MCQOption(BaseModel):
    id: str          # e.g. "A", "B", "C", "D"
    text: str

class MCQQuestion(BaseModel):
    id: str
    question: str
    options: List[MCQOption]
    correct_option_id: str
    explanation: str
    difficulty: int  # 1–5

class CodingChallenge(BaseModel):
    id: str
    problem_statement: str
    constraints: str
    example_input: str
    example_output: str
    hints: List[str]

class CaseStudyQuestion(BaseModel):
    id: str
    scenario: str
    question: str
    evaluation_criteria: List[str]

class AIAssessmentResponse(BaseModel):
    """Strict Pydantic schema for Mistral's JSON output when generating an assessment."""
    skill_name: str
    mcq: List[MCQQuestion]
    coding: List[CodingChallenge]
    case_study: List[CaseStudyQuestion]

# ─── AI Scoring (Mistral Output Schemas) ──────────────────────────────────────

class ScoredQuestion(BaseModel):
    question_id: str
    score: int          # 0–10
    max_score: int
    feedback: str

class AIScoreResponse(BaseModel):
    """Strict schema for Mistral's scoring output."""
    skill_name: str
    overall_score: int  # 0–10
    questions: List[ScoredQuestion]
    strengths: List[str]
    weaknesses: List[str]
    gap_identified: bool
    reasoning: str

# ─── AI Learning Plan (Mistral Output Schemas) ────────────────────────────────

class LearningResource(BaseModel):
    title: str
    url: str
    type: str           # "course", "article", "video", "practice"
    estimated_hours: int
    platform: str       # e.g. "Coursera", "YouTube", "LeetCode"

class LearningPhase(BaseModel):
    phase_number: int
    title: str
    description: str
    duration_weeks: int
    priority: str       # "High", "Medium", "Low"
    resources: List[LearningResource]
    milestones: List[str]

class AILearningPlanResponse(BaseModel):
    """Strict schema for Mistral's learning plan output."""
    skill_name: str
    total_estimated_hours: int
    phases: List[LearningPhase]
    summary: str
