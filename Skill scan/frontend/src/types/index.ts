// User types
export interface User {
  id: number;
  email: string;
  full_name: string;
  user_type: 'MBA' | 'BCA';
  created_at: string;
  updated_at: string;
}

// Authentication
export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  user_type: 'MBA' | 'BCA';
}

// Skills
export interface Skill {
  id: number;
  name: string;
  category: string;
  industry_benchmark: number;
  created_at: string;
  updated_at: string;
}

export interface SkillWithScore extends Skill {
  user_score: number;
  gap: number;
}

// Assessments
export type AssessmentType = 'mcq' | 'coding' | 'case_study';
export type DifficultyLevel = 'easy' | 'medium' | 'hard';
export type AssessmentStatus = 'pending' | 'in_progress' | 'completed' | 'submitted';

export interface Question {
  id: number;
  question_text: string;
  type: AssessmentType;
  difficulty_level: DifficultyLevel;
  options?: string[];
  correct_answer?: string | number;
  time_limit?: number;
}

export interface Assessment {
  id: number;
  assessment_type: AssessmentType;
  skill_id: number;
  difficulty_level: DifficultyLevel;
  questions: Question[];
  status: AssessmentStatus;
  score?: number;
  time_taken?: number;
  created_at: string;
  updated_at: string;
}

export interface AssessmentResponse {
  question_id: number;
  answer: string | number;
  time_spent: number;
}

export interface AssessmentSubmission {
  assessment_id: number;
  responses: AssessmentResponse[];
  total_time: number;
}

// Dashboard
export interface SkillScore {
  skill_name: string;
  user_score: number;
  industry_benchmark: number;
}

export interface GapAnalysis {
  skill_id: number;
  skill_name: string;
  current_score: number;
  benchmark: number;
  gap: number;
  priority: 'high' | 'medium' | 'low';
}

export interface LearningRecommendation {
  id: number;
  skill_id: number;
  skill_name: string;
  recommendation_text: string;
  estimated_duration: string;
  priority: 'high' | 'medium' | 'low';
}

export interface DashboardData {
  overall_score: number;
  completed_assessments: number;
  total_skills: number;
  skill_scores: SkillScore[];
  gap_analysis: GapAnalysis[];
  recommendations: LearningRecommendation[];
}

// API Response
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  error?: string;
}

// Pagination
export interface PaginationParams {
  page: number;
  limit: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}
