/**
 * Learning Plan API Functions
 * Handles all learning plan related API calls with error handling
 */

import {
  LearningPlan,
  LearningPlanResponse,
  LearningPlansResponse,
  GenerateLearningPlanRequest,
  UpdatePlanProgressRequest,
} from '../types/gap';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

/**
 * Generate a new learning plan for a skill
 * @param payload - Request containing skill_id, gap_ids, and duration_weeks
 * @throws Error if the API call fails
 */
export async function generateLearningPlan(
  payload: GenerateLearningPlanRequest
): Promise<LearningPlan> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/learning-plans/generate`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify(payload),
      }
    );

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Unauthorized - Please log in again');
      }
      if (response.status === 400) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Invalid request parameters');
      }
      throw new Error(`API error: ${response.statusText}`);
    }

    const data: LearningPlanResponse = await response.json();
    if (!data.success || !data.data) {
      throw new Error(data.error || 'Failed to generate learning plan');
    }

    return data.data;
  } catch (error) {
    console.error('Error generating learning plan:', error);
    throw error instanceof Error 
      ? error 
      : new Error('Failed to generate learning plan');
  }
}

/**
 * Fetch a specific learning plan
 * @param planId - The ID of the learning plan
 * @throws Error if the API call fails
 */
export async function getLearningPlan(planId: string): Promise<LearningPlan> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/learning-plans/${planId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
      }
    );

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Unauthorized - Please log in again');
      }
      if (response.status === 404) {
        throw new Error('Learning plan not found');
      }
      throw new Error(`API error: ${response.statusText}`);
    }

    const data: LearningPlanResponse = await response.json();
    if (!data.success || !data.data) {
      throw new Error(data.error || 'Failed to fetch learning plan');
    }

    return data.data;
  } catch (error) {
    console.error('Error fetching learning plan:', error);
    throw error instanceof Error 
      ? error 
      : new Error('Failed to fetch learning plan');
  }
}

/**
 * Update learning plan progress
 * @param payload - Request containing plan_id and completed_milestone_weeks
 * @throws Error if the API call fails
 */
export async function updateProgress(
  payload: UpdatePlanProgressRequest
): Promise<LearningPlan> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/learning-plans/${payload.plan_id}/progress`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({
          completed_milestone_weeks: payload.completed_milestone_weeks,
          completed_hours: payload.completed_hours,
        }),
      }
    );

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Unauthorized - Please log in again');
      }
      if (response.status === 404) {
        throw new Error('Learning plan not found');
      }
      throw new Error(`API error: ${response.statusText}`);
    }

    const data: LearningPlanResponse = await response.json();
    if (!data.success || !data.data) {
      throw new Error(data.error || 'Failed to update plan progress');
    }

    return data.data;
  } catch (error) {
    console.error('Error updating plan progress:', error);
    throw error instanceof Error 
      ? error 
      : new Error('Failed to update plan progress');
  }
}

/**
 * Fetch all active learning plans for the current user
 * @throws Error if the API call fails
 */
export async function getActivePlans(): Promise<LearningPlan[]> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/learning-plans?status=in_progress`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
      }
    );

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Unauthorized - Please log in again');
      }
      throw new Error(`API error: ${response.statusText}`);
    }

    const data: LearningPlansResponse = await response.json();
    if (!data.success || !Array.isArray(data.data)) {
      throw new Error(data.error || 'Failed to fetch active plans');
    }

    return data.data || [];
  } catch (error) {
    console.error('Error fetching active plans:', error);
    throw error instanceof Error 
      ? error 
      : new Error('Failed to fetch active plans');
  }
}

/**
 * Fetch all learning plans for the current user
 * @param status - Optional filter by status (not_started, in_progress, completed)
 * @throws Error if the API call fails
 */
export async function getAllPlans(
  status?: 'not_started' | 'in_progress' | 'completed'
): Promise<LearningPlan[]> {
  try {
    const url = status
      ? `${API_BASE_URL}/learning-plans?status=${status}`
      : `${API_BASE_URL}/learning-plans`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Unauthorized - Please log in again');
      }
      throw new Error(`API error: ${response.statusText}`);
    }

    const data: LearningPlansResponse = await response.json();
    if (!data.success || !Array.isArray(data.data)) {
      throw new Error(data.error || 'Failed to fetch plans');
    }

    return data.data || [];
  } catch (error) {
    console.error('Error fetching plans:', error);
    throw error instanceof Error 
      ? error 
      : new Error('Failed to fetch plans');
  }
}

/**
 * Delete a learning plan
 * @param planId - The ID of the learning plan to delete
 * @throws Error if the API call fails
 */
export async function deleteLearningPlan(planId: string): Promise<void> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/learning-plans/${planId}`,
      {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
      }
    );

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Unauthorized - Please log in again');
      }
      if (response.status === 404) {
        throw new Error('Learning plan not found');
      }
      throw new Error(`API error: ${response.statusText}`);
    }
  } catch (error) {
    console.error('Error deleting learning plan:', error);
    throw error instanceof Error 
      ? error 
      : new Error('Failed to delete learning plan');
  }
}

/**
 * Export learning plan as PDF
 * @param planId - The ID of the learning plan
 * @returns Blob containing the PDF file
 */
export async function exportLearningPlanPDF(planId: string): Promise<Blob> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/learning-plans/${planId}/export/pdf`,
      {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return await response.blob();
  } catch (error) {
    console.error('Error exporting PDF:', error);
    throw error instanceof Error 
      ? error 
      : new Error('Failed to export PDF');
  }
}
