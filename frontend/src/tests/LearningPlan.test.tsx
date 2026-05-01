import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import LearningPlan from '../pages/LearningPlan';
import * as AuthContext from '../context/AuthContext';
import apiClient from '../api/client';

// Mock the API client
vi.mock('../api/client', () => ({
  default: {
    get: vi.fn(),
  },
}));

const mockUser = {
  id: '1',
  email: 'test@example.com',
  full_name: 'Test User',
};

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    user: mockUser,
    token: 'fake-token',
    isAuthenticated: true,
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }))
}));

describe('LearningPlan Component', () => {
  const renderComponent = () => {
    return render(
      <MemoryRouter initialEntries={['/learning-plan']}>
        <LearningPlan />
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders learning plan correctly', async () => {
    const mockPlansList = {
      data: {
        learning_plans: [
          {
            learning_plan_id: 101,
            skill_name: 'Docker',
            score: 7,
            estimated_hours: 15,
            priority: 1,
            summary: 'Docker fundamentals',
            phases_count: 1,
            created_at: '2023-01-01T00:00:00Z',
          },
        ],
      },
    };

    const mockPlanDetail = {
      data: {
        learning_plan_id: 101,
        timeline_weeks: 3,
        estimated_hours: 15,
        youtube_resources: [
          { title: 'Docker Tutorial', url: 'https://youtube.com/watch?v=123', duration_minutes: 60 },
        ],
        website_resources: [
          { title: 'Docker Docs', url: 'https://docs.docker.com', category: 'Documentation', estimated_hours: 2 },
        ],
        recommendations: {
          summary: 'Docker fundamentals',
          phases: [
            {
              phase_number: 1,
              title: 'Introduction',
              description: 'Learn the basics',
              youtube_resources: [
                { title: 'Docker Tutorial', url: 'https://youtube.com/watch?v=123', duration_minutes: 60 },
              ],
              website_resources: [
                { title: 'Docker Docs', url: 'https://docs.docker.com', category: 'Documentation', estimated_hours: 2 },
              ],
            },
          ],
        },
      },
    };

    // First call is for list, second is for detail
    (apiClient.get as any)
      .mockResolvedValueOnce(mockPlansList)
      .mockResolvedValueOnce(mockPlanDetail);

    renderComponent();

    // Verify it loads correctly
    const dockerElements = await screen.findAllByText(/Docker/i);
    expect(dockerElements.length).toBeGreaterThan(0);
    const summaryElements = await screen.findAllByText(/Docker fundamentals/i);
    expect(summaryElements.length).toBeGreaterThan(0);
    const introElements = await screen.findAllByText(/Introduction/i);
    expect(introElements.length).toBeGreaterThan(0);
    const docsElements = await screen.findAllByText(/Docker Docs/i);
    expect(docsElements.length).toBeGreaterThan(0);
  });

  it('displays error message if plan loading fails', async () => {
    (apiClient.get as any).mockRejectedValueOnce({
      response: { data: { error: 'Failed to load learning plans.' } },
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Failed to load learning plans.')).toBeInTheDocument();
    });
  });
});
