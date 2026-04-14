-- SkillScan MVP - PostgreSQL Database Schema
-- Generated from SQLAlchemy models
-- Compatible with Supabase PostgreSQL

-- Enable UUID extension (optional, for future use)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table 1: students
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    user_type VARCHAR(10) NOT NULL,
    profile_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_students_email ON students(email);
CREATE INDEX idx_students_user_type ON students(user_type);
CREATE INDEX idx_students_created_at ON students(created_at);

-- Table 2: skills_taxonomy
CREATE TABLE IF NOT EXISTS skills_taxonomy (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    industry_benchmark INTEGER NOT NULL CHECK (industry_benchmark >= 1 AND industry_benchmark <= 10),
    subcategories JSONB DEFAULT '[]',
    target_users JSONB DEFAULT '[]'
);

CREATE INDEX idx_skills_taxonomy_name ON skills_taxonomy(name);
CREATE INDEX idx_skills_taxonomy_category ON skills_taxonomy(category);

-- Table 3: student_skills
CREATE TABLE IF NOT EXISTS student_skills (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills_taxonomy(id) ON DELETE CASCADE,
    proficiency_claimed INTEGER NOT NULL CHECK (proficiency_claimed >= 1 AND proficiency_claimed <= 10),
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_student_skill UNIQUE(student_id, skill_id)
);

CREATE INDEX idx_student_skills_student_id ON student_skills(student_id);
CREATE INDEX idx_student_skills_skill_id ON student_skills(skill_id);
CREATE INDEX idx_student_skills_created ON student_skills(student_id, created_at);

-- Table 4: assessments
CREATE TABLE IF NOT EXISTS assessments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills_taxonomy(id) ON DELETE CASCADE,
    assessment_type VARCHAR(50) NOT NULL,
    difficulty_level VARCHAR(20) NOT NULL,
    questions JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assessment_student_skill_difficulty ON assessments(student_id, skill_id, difficulty_level);
CREATE INDEX idx_assessment_status ON assessments(student_id, status);
CREATE INDEX idx_assessment_created ON assessments(student_id, created_at);

-- Table 5: assessment_responses
CREATE TABLE IF NOT EXISTS assessment_responses (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    responses JSONB NOT NULL,
    submitted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assessment_responses_assessment_id ON assessment_responses(assessment_id);
CREATE INDEX idx_assessment_responses_student_id ON assessment_responses(student_id);

-- Table 6: skill_scores
CREATE TABLE IF NOT EXISTS skill_scores (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills_taxonomy(id) ON DELETE CASCADE,
    assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    score INTEGER NOT NULL CHECK (score >= 1 AND score <= 10),
    gaps_identified JSONB DEFAULT '[]',
    reasoning TEXT,
    ai_confidence NUMERIC(3, 2) NOT NULL CHECK (ai_confidence >= 0 AND ai_confidence <= 1),
    scored_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_skill_score_student_skill ON skill_scores(student_id, skill_id);
CREATE INDEX idx_skill_score_timestamp ON skill_scores(student_id, scored_at);

-- Table 7: learning_plans
CREATE TABLE IF NOT EXISTS learning_plans (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills_taxonomy(id) ON DELETE CASCADE,
    gap_category VARCHAR(100) NOT NULL,
    recommendations JSONB DEFAULT '[]',
    estimated_hours INTEGER NOT NULL CHECK (estimated_hours >= 0),
    priority_score INTEGER NOT NULL CHECK (priority_score >= 1 AND priority_score <= 5),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_learning_plan UNIQUE(student_id, skill_id, gap_category)
);

CREATE INDEX idx_learning_plan_priority ON learning_plans(student_id, priority_score);
CREATE INDEX idx_learning_plan_student ON learning_plans(student_id);

-- Table 8: demo_accounts
CREATE TABLE IF NOT EXISTS demo_accounts (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    user_type VARCHAR(10) NOT NULL,
    prefilled_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_demo_accounts_username ON demo_accounts(username);
CREATE INDEX idx_demo_accounts_email ON demo_accounts(email);

-- Foreign key constraints (explicit for clarity)
ALTER TABLE student_skills 
ADD CONSTRAINT fk_student_skills_student_id FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;

ALTER TABLE student_skills 
ADD CONSTRAINT fk_student_skills_skill_id FOREIGN KEY (skill_id) REFERENCES skills_taxonomy(id) ON DELETE CASCADE;

ALTER TABLE assessments 
ADD CONSTRAINT fk_assessments_student_id FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;

ALTER TABLE assessments 
ADD CONSTRAINT fk_assessments_skill_id FOREIGN KEY (skill_id) REFERENCES skills_taxonomy(id) ON DELETE CASCADE;

ALTER TABLE assessment_responses 
ADD CONSTRAINT fk_assessment_responses_assessment_id FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE;

ALTER TABLE assessment_responses 
ADD CONSTRAINT fk_assessment_responses_student_id FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;

ALTER TABLE skill_scores 
ADD CONSTRAINT fk_skill_scores_student_id FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;

ALTER TABLE skill_scores 
ADD CONSTRAINT fk_skill_scores_skill_id FOREIGN KEY (skill_id) REFERENCES skills_taxonomy(id) ON DELETE CASCADE;

ALTER TABLE skill_scores 
ADD CONSTRAINT fk_skill_scores_assessment_id FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE;

ALTER TABLE learning_plans 
ADD CONSTRAINT fk_learning_plans_student_id FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;

ALTER TABLE learning_plans 
ADD CONSTRAINT fk_learning_plans_skill_id FOREIGN KEY (skill_id) REFERENCES skills_taxonomy(id) ON DELETE CASCADE;

-- Create updated_at trigger for students table
CREATE OR REPLACE FUNCTION update_students_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_students_updated_at
BEFORE UPDATE ON students
FOR EACH ROW
EXECUTE FUNCTION update_students_updated_at();

-- Create updated_at trigger for assessments table
CREATE OR REPLACE FUNCTION update_assessments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_assessments_updated_at
BEFORE UPDATE ON assessments
FOR EACH ROW
EXECUTE FUNCTION update_assessments_updated_at();

-- Add comments for documentation
COMMENT ON TABLE students IS 'Stores user profiles and authentication data for MBA and BCA students';
COMMENT ON TABLE skills_taxonomy IS 'Master list of skills with industry benchmarks and categorization';
COMMENT ON TABLE student_skills IS 'Mapping of skills claimed by students from resume or manual entry';
COMMENT ON TABLE assessments IS 'Assessment templates and metadata for skill verification';
COMMENT ON TABLE assessment_responses IS 'Student responses and answers to assessments';
COMMENT ON TABLE skill_scores IS 'AI-generated scores and analysis from completed assessments';
COMMENT ON TABLE learning_plans IS 'Personalized learning recommendations based on skill gaps';
COMMENT ON TABLE demo_accounts IS 'Pre-populated demo accounts for testing and demos';
