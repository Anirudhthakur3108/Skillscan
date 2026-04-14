import client from './client';
import { Skill, SkillWithScore, PaginatedResponse } from '@types';

export const skillsAPI = {
  getSkills: async (userId: number): Promise<Skill[]> => {
    const response = await client.get(`/skills?user_id=${userId}`);
    return response.data;
  },

  getSkillsWithScores: async (userId: number): Promise<SkillWithScore[]> => {
    const response = await client.get(`/skills/with-scores?user_id=${userId}`);
    return response.data;
  },

  getSkillById: async (skillId: number): Promise<Skill> => {
    const response = await client.get(`/skills/${skillId}`);
    return response.data;
  },

  addSkill: async (userId: number, skillData: Partial<Skill>): Promise<Skill> => {
    const response = await client.post('/skills', { user_id: userId, ...skillData });
    return response.data;
  },

  updateSkill: async (skillId: number, skillData: Partial<Skill>): Promise<Skill> => {
    const response = await client.put(`/skills/${skillId}`, skillData);
    return response.data;
  },

  deleteSkill: async (skillId: number): Promise<void> => {
    await client.delete(`/skills/${skillId}`);
  },

  getAllSkillsDirectory: async (pagination?: { page: number; limit: number }): Promise<PaginatedResponse<Skill>> => {
    const params = pagination ? `?page=${pagination.page}&limit=${pagination.limit}` : '';
    const response = await client.get(`/skills/directory${params}`);
    return response.data;
  },
};
