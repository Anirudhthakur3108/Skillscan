/**
 * Gap Analysis & Learning Plan Type Definitions
 * Production-ready TypeScript interfaces for SkillScan MVP
 */

export type PriorityLevel = 'high' | 'medium' | 'low';
export type DifficultyLevel = 'easy' | 'medium' | 'hard';
export type ResourceType = 'course' | 'project' | 'video' | 'documentation';
export type LearningPlanStatus = 'not_started' | 'in_progress' | 'completed';

/**
 * Individual skill gap identified during assessment
 */
export interface Gap {
  id: string;
  name: string;
  priority: PriorityLevel;
  frequency: number; // Number of assessments where this gap appeared
  impact: number; // 0-100 impact score
  recommendations: string[];
  description?: string;
}

/**
 * Complete gap analysis for a specific skill
 */
export interface GapAnalysis {
  skill_id: number;
  skill_name: string;
  current_score: number; // 0-100
  benchmark_score: number; // 0-100
  percentile: number; // 0-100
  gaps: Gap[];
  weak_areas: string[];
  assessment_date?: string;
  assessment_count?: number;
}

/**
 * Single learning resource for a milestone
 */
export interface Resource {
  id: string;
  type: ResourceType;
  title: string;
  platform: string;
  duration: string; // e.g., "2 hours", "4 weeks"
  difficulty: DifficultyLevel;
  link: string;
  priority: PriorityLevel;
  completed?: boolean;
}

/**
 * Weekly milestone within a learning plan
 */
export interface Milestone {
  week: number;
  title: string;
  description: string;
  success_criteria: string[];
  estimated_hours: number;
  resources: Resource[];
  completed: boolean;
  completion_date?: string;
}

/**
 * Complete learning plan for a skill gap
 */
export interface LearningPlan {
  id: string;
  skill_id: number;
  skill_name: string;
  gap_ids: string[]; // IDs of gaps being addressed
  duration_weeks: number; // User selected duration (2, 3, 4, or 6)
  recommended_duration: number; // System recommended duration
  recommendation_reason: string; // e.g., "Score 78% - 4-week intensive plan recommended"
  milestones: Milestone[];
  resources: Resource[];
  progress: number; // 0-100
  status: LearningPlanStatus;
  created_at: string;
  start_date?: string;
  target_completion_date?: string;
  completion_date?: string;
  total_hours: number;
  completed_hours: number;
}

/**
 * Overview statistics for dashboard
 */
export interface DashboardStats {
  total_skills: number;
  assessments_taken: number;
  average_score: number;
  active_plans: number;
  completed_plans: number;
}

/**
 * Skill score for dashboard chart
 */
export interface SkillScore {
  skill_id: number;
  skill_name: string;
  score: number; // 0-100
  last_assessed: string; // ISO date
  trend?: 'up' | 'down' | 'stable';
}

/**
 * API response for gap analysis
 */
export interface GapAnalysisResponse {
  success: boolean;
  data?: GapAnalysis;
  error?: string;
  timestamp: string;
}

/**
 * API response for learning plan
 */
export interface LearningPlanResponse {
  success: boolean;
  data?: LearningPlan;
  error?: string;
  timestamp: string;
}

/**
 * API response for multiple learning plans
 */
export interface LearningPlansResponse {
  success: boolean;
  data?: LearningPlan[];
  error?: string;
  count?: number;
  timestamp: string;
}

/**
 * Request body for generating a learning plan
 */
export interface GenerateLearningPlanRequest {
  skill_id: number;
  gap_ids: string[];
  duration_weeks: 2 | 3 | 4 | 6;
  user_level?: DifficultyLevel;
}

/**
 * Request body for updating plan progress
 */
export interface UpdatePlanProgressRequest {
  plan_id: string;
  completed_milestone_weeks: number[];
  completed_hours?: number;
}

/**
 * Benchmark data for skills
 */
export interface SkillBenchmark {
  skill_id: number;
  skill_name: string;
  average_score: number;
  median_score: number;
  percentile_ranges: {
    level: string;
    min_score: number;
    max_score: number;
    percentage: number;
  }[];
}
