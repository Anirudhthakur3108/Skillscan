/**
 * Gap Analysis API Functions
 * Handles all gap analysis related API calls with error handling
 */

import {
  GapAnalysis,
  GapAnalysisResponse,
  SkillBenchmark,
} from '../types/gap';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

/**
 * Fetch gap analysis for a specific skill
 * @param skillId - The ID of the skill to analyze
 * @throws Error if the API call fails
 */
export async function getGapAnalysis(skillId: number): Promise<GapAnalysis> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/gap-analysis/skill/${skillId}`,
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
        throw new Error('Gap analysis not found for this skill');
      }
      throw new Error(`API error: ${response.statusText}`);
    }

    const data: GapAnalysisResponse = await response.json();
    if (!data.success || !data.data) {
      throw new Error(data.error || 'Failed to fetch gap analysis');
    }

    return data.data;
  } catch (error) {
    console.error('Error fetching gap analysis:', error);
    throw error instanceof Error 
      ? error 
      : new Error('Failed to fetch gap analysis');
  }
}

/**
 * Fetch full detailed gap analysis report
 * @throws Error if the API call fails
 */
export async function getFullReport(): Promise<GapAnalysis[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/gap-analysis/report`, {
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

    const data = await response.json();
    if (!data.success || !Array.isArray(data.data)) {
      throw new Error(data.error || 'Failed to fetch full report');
    }

    return data.data;
  } catch (error) {
    console.error('Error fetching full report:', error);
    throw error instanceof Error 
      ? error 
      : new Error('Failed to fetch full report');
  }
}

/**
 * Fetch industry benchmark data for a skill
 * @param skillId - The ID of the skill
 * @throws Error if the API call fails
 */
export async function getBenchmarks(skillId: number): Promise<SkillBenchmark> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/gap-analysis/benchmarks/${skillId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Benchmark data not found');
      }
      throw new Error(`API error: ${response.statusText}`);
    }

    const data = await response.json();
    if (!data.success || !data.data) {
      throw new Error(data.error || 'Failed to fetch benchmarks');
    }

    return data.data;
  } catch (error) {
    console.error('Error fetching benchmarks:', error);
    throw error instanceof Error 
      ? error 
      : new Error('Failed to fetch benchmarks');
  }
}

/**
 * Fetch gap analysis trends over time
 * @throws Error if the API call fails
 */
export async function getTrends(): Promise<
  { skill_id: number; skill_name: string; scores: { date: string; score: number }[] }[]
> {
  try {
    const response = await fetch(`${API_BASE_URL}/gap-analysis/trends`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const data = await response.json();
    if (!data.success || !Array.isArray(data.data)) {
      throw new Error(data.error || 'Failed to fetch trends');
    }

    return data.data;
  } catch (error) {
    console.error('Error fetching trends:', error);
    throw error instanceof Error 
      ? error 
      : new Error('Failed to fetch trends');
  }
}

/**
 * Export gap analysis as PDF
 * @param skillId - The ID of the skill (optional - if not provided, exports all)
 * @returns Blob containing the PDF file
 */
export async function exportGapAnalysisPDF(skillId?: number): Promise<Blob> {
  try {
    const url = skillId 
      ? `${API_BASE_URL}/gap-analysis/export/${skillId}/pdf`
      : `${API_BASE_URL}/gap-analysis/export/pdf`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
      },
    });

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
