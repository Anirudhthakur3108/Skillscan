import client from './client';
import { DashboardData, GapAnalysis, LearningRecommendation } from '@types';

export const dashboardAPI = {
  getDashboardData: async (userId: number): Promise<DashboardData> => {
    const response = await client.get(`/dashboard?user_id=${userId}`);
    return response.data;
  },

  getSkillScores: async (userId: number) => {
    const response = await client.get(`/dashboard/skill-scores?user_id=${userId}`);
    return response.data;
  },

  getGapAnalysis: async (userId: number): Promise<GapAnalysis[]> => {
    const response = await client.get(`/dashboard/gap-analysis?user_id=${userId}`);
    return response.data;
  },

  getLearningRecommendations: async (userId: number): Promise<LearningRecommendation[]> => {
    const response = await client.get(`/dashboard/recommendations?user_id=${userId}`);
    return response.data;
  },

  getProgressReport: async (userId: number) => {
    const response = await client.get(`/dashboard/progress?user_id=${userId}`);
    return response.data;
  },

  getComparisonData: async (userId: number) => {
    const response = await client.get(`/dashboard/comparison?user_id=${userId}`);
    return response.data;
  },
};
