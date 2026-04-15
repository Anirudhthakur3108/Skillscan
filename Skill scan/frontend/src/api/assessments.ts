/**
 * Assessment API Integration for SkillScan MVP
 * Handles API calls for generating, submitting, and tracking assessment progress
 */

import axios, { AxiosError } from 'axios';
import {
  Assessment,
  AssessmentResult,
  AssessmentProgress,
  AssessmentSubmission,
  DifficultyLevel,
  AssessmentType,
  MCQQuestion,
  CodingProblem,
  CaseStudyScenario,
  TestCase,
  Recommendation,
} from '../types/assessment';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Mock data generator for demo/testing
const generateMockMCQAssessment = (skillId: number, difficulty: DifficultyLevel): MCQQuestion[] => {
  const questions: MCQQuestion[] = [
    {
      id: 'mcq-1',
      question: 'What is the primary purpose of data normalization in databases?',
      options: [
        'To increase database size',
        'To eliminate data redundancy and improve data integrity',
        'To slow down query performance',
        'To make backups easier',
      ],
      correct_answer: 'To eliminate data redundancy and improve data integrity',
      explanation: 'Data normalization reduces redundancy and ensures data consistency by organizing data into related tables.',
    },
    {
      id: 'mcq-2',
      question: 'Which SQL clause is used to filter groups?',
      options: ['WHERE', 'HAVING', 'GROUP BY', 'FILTER'],
      correct_answer: 'HAVING',
      explanation: 'HAVING is used to filter groups in SQL queries, similar to how WHERE filters individual rows.',
    },
    {
      id: 'mcq-3',
      question: 'What does ACID stand for in database transactions?',
      options: [
        'Atomicity, Consistency, Isolation, Durability',
        'Application, Connection, Integration, Data',
        'Availability, Concurrency, Index, Distribution',
        'Access, Cache, Insert, Delete',
      ],
      correct_answer: 'Atomicity, Consistency, Isolation, Durability',
      explanation:
        'ACID properties ensure reliable database transactions: A=all-or-nothing, C=valid state, I=isolated execution, D=permanent storage.',
    },
    {
      id: 'mcq-4',
      question: 'Which of the following is a NoSQL database?',
      options: ['PostgreSQL', 'MySQL', 'MongoDB', 'SQLite'],
      correct_answer: 'MongoDB',
      explanation: 'MongoDB is a document-based NoSQL database, while PostgreSQL, MySQL, and SQLite are relational databases.',
    },
    {
      id: 'mcq-5',
      question: 'What is an index in a database?',
      options: [
        'A table of contents for the entire database',
        'A data structure that improves data retrieval speed',
        'A backup copy of the database',
        'A list of all tables in the database',
      ],
      correct_answer: 'A data structure that improves data retrieval speed',
      explanation: 'Database indexes create structures (like B-trees) that enable faster lookups, at the cost of additional storage and write overhead.',
    },
    {
      id: 'mcq-6',
      question: 'What is a foreign key?',
      options: [
        'A key that opens multiple databases',
        'A column that references a primary key in another table',
        'A temporary key used for sessions',
        'A key that encrypts sensitive data',
      ],
      correct_answer: 'A column that references a primary key in another table',
      explanation: 'Foreign keys maintain referential integrity by ensuring that values in one table reference valid values in another table.',
    },
  ];

  return questions.slice(0, difficulty === 'easy' ? 4 : difficulty === 'medium' ? 5 : 6);
};

const generateMockCodingAssessment = (skillId: number, difficulty: DifficultyLevel): CodingProblem[] => {
  const problems: CodingProblem[] = [
    {
      id: 'code-1',
      title: 'Two Sum',
      description: 'Given an array of integers nums and an integer target, return the indices of the two numbers that add up to target.',
      starter_code: `def twoSum(nums, target):
    """
    Args:
        nums: List of integers
        target: Target sum
    Returns:
        List of two indices
    """
    # Your code here
    pass`,
      test_cases: [
        {
          id: 'test-1',
          input: 'nums = [2, 7, 11, 15], target = 9',
          expected_output: '[0, 1]',
          description: 'Basic case',
        },
        {
          id: 'test-2',
          input: 'nums = [3, 2, 4], target = 6',
          expected_output: '[1, 2]',
          description: 'Another case',
        },
      ],
    },
    {
      id: 'code-2',
      title: 'Reverse a String',
      description: 'Write a function that reverses a string.',
      starter_code: `def reverseString(s):
    """Reverse the input string"""
    pass`,
      test_cases: [
        {
          id: 'test-1',
          input: 's = "hello"',
          expected_output: '"olleh"',
          description: 'Basic reverse',
        },
      ],
    },
  ];

  return problems.slice(0, difficulty === 'easy' ? 1 : difficulty === 'medium' ? 2 : 2);
};

const generateMockCaseStudyAssessment = (skillId: number, difficulty: DifficultyLevel): CaseStudyScenario[] => {
  const scenarios: CaseStudyScenario[] = [
    {
      id: 'case-1',
      title: 'E-Commerce Database Design',
      description:
        'You are designing a database for an e-commerce platform. The system needs to handle products, orders, customers, and inventory across multiple warehouses.',
      context: 'Consider scalability, performance, and data integrity requirements.',
      questions: [
        'How would you structure the database schema to normalize data and prevent redundancy?',
        'What indexes would you create and why?',
        'How would you handle inventory management across multiple warehouses?',
      ],
    },
    {
      id: 'case-2',
      title: 'Analytics Data Pipeline',
      description: 'Design a data pipeline for analyzing user behavior across a web application with millions of daily users.',
      context: 'The data must be available for real-time dashboards and historical analysis.',
      questions: [
        'Would you use SQL or NoSQL for this use case and why?',
        'How would you handle data from different sources (web, mobile, API)?',
        'What performance considerations are important?',
      ],
    },
  ];

  return scenarios.slice(0, difficulty === 'easy' ? 1 : difficulty === 'medium' ? 2 : 2);
};

// API Client Methods
export const assessmentAPI = {
  /**
   * Generate a new assessment
   */
  generateAssessment: async (
    skillId: number,
    difficulty: DifficultyLevel,
    assessmentType: AssessmentType
  ): Promise<Assessment> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/assessments/generate`, {
        skill_id: skillId,
        difficulty,
        assessment_type: assessmentType,
      });

      // For MVP, ensure we have data even if API returns incomplete
      const assessment = response.data as Assessment;
      return {
        ...assessment,
        questions: assessment.questions || generateMockMCQAssessment(skillId, difficulty),
        problems: assessment.problems || generateMockCodingAssessment(skillId, difficulty),
        scenarios: assessment.scenarios || generateMockCaseStudyAssessment(skillId, difficulty),
      };
    } catch (error) {
      console.error('Failed to generate assessment:', error);
      // Fall back to mock data for MVP
      const mockAssessment: Assessment = {
        id: `assessment-${Date.now()}`,
        skill_id: skillId,
        difficulty,
        assessment_type: assessmentType,
        questions: assessmentType === 'mcq' ? generateMockMCQAssessment(skillId, difficulty) : undefined,
        problems: assessmentType === 'coding' ? generateMockCodingAssessment(skillId, difficulty) : undefined,
        scenarios: assessmentType === 'casestudy' ? generateMockCaseStudyAssessment(skillId, difficulty) : undefined,
        timer_seconds: difficulty === 'easy' ? 360 : difficulty === 'medium' ? 1800 : 3600,
        created_at: new Date().toISOString(),
      };
      return mockAssessment;
    }
  },

  /**
   * Submit assessment responses
   */
  submitAssessment: async (submission: AssessmentSubmission): Promise<AssessmentResult> => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/assessments/${submission.assessment_id}/submit`,
        submission
      );
      return response.data as AssessmentResult;
    } catch (error) {
      const axiosError = error as AxiosError;
      console.error('Failed to submit assessment:', axiosError);
      throw new Error(`Failed to submit assessment: ${axiosError.message}`);
    }
  },

  /**
   * Get assessment progress for a skill
   */
  getAssessmentProgress: async (skillId: number): Promise<AssessmentProgress> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/assessments/${skillId}/progress`);
      return response.data as AssessmentProgress;
    } catch (error) {
      console.error('Failed to get assessment progress:', error);
      // Return default progress if API fails
      return {
        skill_id: skillId,
        easy: { completed: false, attempts: 0 },
        medium: { completed: false, attempts: 0 },
        hard: { completed: false, attempts: 0 },
      };
    }
  },

  /**
   * Get a specific assessment result
   */
  getAssessmentResult: async (resultId: string): Promise<AssessmentResult> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/assessment-results/${resultId}`);
      return response.data as AssessmentResult;
    } catch (error) {
      const axiosError = error as AxiosError;
      console.error('Failed to get assessment result:', axiosError);
      throw new Error(`Failed to get assessment result: ${axiosError.message}`);
    }
  },
};

export default assessmentAPI;
