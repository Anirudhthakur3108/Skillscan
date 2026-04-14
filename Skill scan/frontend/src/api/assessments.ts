import client from './client';
import { Assessment, AssessmentSubmission, ApiResponse } from '@types';

export const assessmentsAPI = {
  getAssessments: async (userId: number): Promise<Assessment[]> => {
    const response = await client.get(`/assessments?user_id=${userId}`);
    return response.data;
  },

  getAssessmentById: async (assessmentId: number): Promise<Assessment> => {
    const response = await client.get(`/assessments/${assessmentId}`);
    return response.data;
  },

  getAssessmentBySkill: async (userId: number, skillId: number): Promise<Assessment> => {
    const response = await client.get(`/assessments/skill/${skillId}?user_id=${userId}`);
    return response.data;
  },

  startAssessment: async (userId: number, skillId: number, difficultyLevel: string): Promise<Assessment> => {
    const response = await client.post('/assessments/start', {
      user_id: userId,
      skill_id: skillId,
      difficulty_level: difficultyLevel,
    });
    return response.data;
  },

  submitAssessment: async (submission: AssessmentSubmission): Promise<ApiResponse<any>> => {
    const response = await client.post('/assessments/submit', submission);
    return response.data;
  },

  getAssessmentResult: async (assessmentId: number): Promise<any> => {
    const response = await client.get(`/assessments/${assessmentId}/result`);
    return response.data;
  },

  saveProgress: async (assessmentId: number, currentQuestion: number, responses: any[]): Promise<void> => {
    await client.post(`/assessments/${assessmentId}/progress`, {
      current_question: currentQuestion,
      responses,
    });
  },
};
