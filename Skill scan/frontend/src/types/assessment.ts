/**
 * Assessment Type Definitions for SkillScan MVP
 * Covers MCQ, Coding, and Case Study assessment types
 */

// MCQ Assessment Types
export interface MCQQuestion {
  id: string;
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
}

// Coding Assessment Types
export interface TestCase {
  id: string;
  input: string;
  expected_output: string;
  description: string;
}

export interface CodingProblem {
  id: string;
  title: string;
  description: string;
  starter_code?: string;
  test_cases?: TestCase[];
  difficulty_level?: string;
}

// Case Study Assessment Types
export interface CaseStudyScenario {
  id: string;
  title: string;
  description: string;
  context?: string;
  questions: string[];
}

// Main Assessment Interface
export type AssessmentType = 'mcq' | 'coding' | 'casestudy';
export type DifficultyLevel = 'easy' | 'medium' | 'hard';

export interface Assessment {
  id: string;
  skill_id: number;
  difficulty: DifficultyLevel;
  assessment_type: AssessmentType;
  questions?: MCQQuestion[];
  problems?: CodingProblem[];
  scenarios?: CaseStudyScenario[];
  timer_seconds: number;
  created_at: string;
}

// Assessment Result Types
export interface Recommendation {
  id: string;
  title: string;
  description: string;
  url?: string;
  duration?: string;
  type: 'course' | 'article' | 'video' | 'practice';
}

export type PerformanceBadge = 'Excellent' | 'Good' | 'Fair' | 'Needs Work';

export interface AssessmentResult {
  id: string;
  assessment_id: string;
  skill_id: number;
  score: number;
  total_points: number;
  percentage: number;
  difficulty: DifficultyLevel;
  assessment_type: AssessmentType;
  feedback: string;
  gaps: string[];
  badge: PerformanceBadge;
  recommendations: Recommendation[];
  wrong_answers?: WrongAnswer[];
  submitted_at: string;
}

export interface WrongAnswer {
  question_id: string;
  question: string;
  user_answer: string;
  correct_answer: string;
  explanation: string;
}

// Assessment Progress Type
export interface AssessmentProgress {
  skill_id: number;
  easy: {
    completed: boolean;
    score?: number;
    attempts: number;
    last_attempted?: string;
  };
  medium: {
    completed: boolean;
    score?: number;
    attempts: number;
    last_attempted?: string;
  };
  hard: {
    completed: boolean;
    score?: number;
    attempts: number;
    last_attempted?: string;
  };
}

// User Response Types
export interface MCQResponse {
  question_id: string;
  selected_option: string;
  time_spent?: number;
}

export interface CodingResponse {
  problem_id: string;
  code: string;
  language?: string;
  test_results?: TestResult[];
  time_spent?: number;
}

export interface TestResult {
  test_case_id: string;
  passed: boolean;
  expected_output: string;
  actual_output: string;
}

export interface CaseStudyResponse {
  scenario_id: string;
  responses: {
    question_index: number;
    response: string;
  }[];
  time_spent?: number;
}

// Combined Response Type
export type AssessmentSubmission = {
  assessment_id: string;
  assessment_type: AssessmentType;
  responses: MCQResponse[] | CodingResponse[] | CaseStudyResponse[];
  time_spent: number;
};

// Skill Information
export interface Skill {
  id: number;
  name: string;
  description: string;
  category: string;
}

// Assessment Form Props
export interface AssessmentFormProps {
  assessment: Assessment;
  onSubmit: (submission: AssessmentSubmission) => Promise<void>;
  onTimeout: () => void;
  isSubmitting?: boolean;
}

// Timer Props
export interface TimerProps {
  totalSeconds: number;
  onTimeExpire: () => void;
  isPaused?: boolean;
}

// Progress Bar Props
export interface ProgressBarProps {
  current: number;
  total: number;
  showLabel?: boolean;
  className?: string;
}

// Difficulty Selector Props
export interface DifficultySelectorProps {
  skillId: number;
  selectedDifficulty: DifficultyLevel | null;
  onSelect: (difficulty: DifficultyLevel) => void;
  isLoading?: boolean;
}
