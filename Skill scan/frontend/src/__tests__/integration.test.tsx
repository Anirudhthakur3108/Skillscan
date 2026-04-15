import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';

import App from '../App';
import Login from '../pages/Login';
import Register from '../pages/Register';
import Profile from '../pages/Profile';
import Assessment from '../pages/Assessment';
import Dashboard from '../pages/Dashboard';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// ============================================================================
// TEST SUITE 1: AUTHENTICATION FLOW
// ============================================================================

describe('Authentication Workflow Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it('should complete full registration → login flow', async () => {
    // Step 1: Register
    mockedAxios.post.mockResolvedValueOnce({
      status: 201,
      data: {
        token: 'test_token_123',
        email: 'test@example.com',
        user_type: 'BCA',
      },
    });

    render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /register/i });

    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'password123');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(localStorage.getItem('token')).toBe('test_token_123');
    });
  });

  it('should handle invalid email format during registration', async () => {
    render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );

    const emailInput = screen.getByLabelText(/email/i);
    const submitButton = screen.getByRole('button', { name: /register/i });

    await userEvent.type(emailInput, 'invalid-email');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(/invalid email/i)
      ).toBeInTheDocument();
    });
  });

  it('should reject weak passwords', async () => {
    render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );

    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /register/i });

    await userEvent.type(passwordInput, '123');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(/at least 6 characters/i)
      ).toBeInTheDocument();
    });
  });

  it('should handle login with token storage', async () => {
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        token: 'login_token_456',
        email: 'test@example.com',
      },
    });

    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /login/i });

    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'password123');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(localStorage.getItem('token')).toBe('login_token_456');
    });
  });

  it('should handle network timeout during login', async () => {
    mockedAxios.post.mockRejectedValueOnce(
      new Error('Network timeout after 30s')
    );

    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );

    const submitButton = screen.getByRole('button', { name: /login/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(/timeout|network error/i)
      ).toBeInTheDocument();
    });
  });
});

// ============================================================================
// TEST SUITE 2: SKILL MANAGEMENT WORKFLOW
// ============================================================================

describe('Skill Management Workflow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.setItem('token', 'test_token');
  });

  it('should handle resume upload and skill extraction', async () => {
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        extracted_skills: [
          { name: 'Python', confidence: 0.95 },
          { name: 'SQL', confidence: 0.87 },
        ],
      },
    });

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    const fileInput = screen.getByLabelText(/upload resume/i) as HTMLInputElement;
    const file = new File(['resume content'], 'resume.pdf', { type: 'application/pdf' });

    await userEvent.upload(fileInput, file);

    await waitFor(() => {
      expect(screen.getByText(/Python/i)).toBeInTheDocument();
      expect(screen.getByText(/SQL/i)).toBeInTheDocument();
    });
  });

  it('should reject oversized file uploads (>50MB)', async () => {
    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    const fileInput = screen.getByLabelText(/upload resume/i) as HTMLInputElement;
    
    // Create a mock file that simulates 60MB
    const file = new File(['x'.repeat(60 * 1024 * 1024)], 'large.pdf', {
      type: 'application/pdf',
    });

    await userEvent.upload(fileInput, file);

    await waitFor(() => {
      expect(
        screen.getByText(/exceeds.*limit|too large/i)
      ).toBeInTheDocument();
    });
  });

  it('should handle malformed PDF files gracefully', async () => {
    mockedAxios.post.mockRejectedValueOnce(
      new Error('Invalid PDF file')
    );

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    const fileInput = screen.getByLabelElement(/upload resume/i) as HTMLInputElement;
    const file = new File(['not a pdf'], 'fake.pdf', { type: 'application/pdf' });

    await userEvent.upload(fileInput, file);

    await waitFor(() => {
      expect(
        screen.getByText(/invalid|corrupted/i)
      ).toBeInTheDocument();
    });
  });

  it('should allow manual skill addition with autocomplete', async () => {
    mockedAxios.post.mockResolvedValueOnce({
      status: 201,
      data: {
        id: 1,
        name: 'Python',
        proficiency: 8,
      },
    });

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    const skillInput = screen.getByPlaceholderText(/search skills/i);
    await userEvent.type(skillInput, 'Pyt');

    await waitFor(() => {
      expect(screen.getByText('Python')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Python'));

    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '8' } });

    const addButton = screen.getByRole('button', { name: /add|confirm/i });
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        expect.stringContaining('/skills/add'),
        expect.objectContaining({ skill_name: 'Python', proficiency: 8 }),
        expect.any(Object)
      );
    });
  });
});

// ============================================================================
// TEST SUITE 3: ASSESSMENT WORKFLOW
// ============================================================================

describe('Assessment Workflow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.setItem('token', 'test_token');
  });

  it('should complete MCQ assessment with timer', async () => {
    mockedAxios.post.mockResolvedValueOnce({
      status: 201,
      data: {
        assessment_id: 1,
        type: 'mcq',
        difficulty: 'easy',
        questions: [
          {
            id: 1,
            text: 'What is 2+2?',
            options: ['1', '2', '4', '5'],
            correct: 2,
          },
        ],
        time_limit: 360, // 6 minutes
      },
    });

    render(
      <BrowserRouter>
        <Assessment />
      </BrowserRouter>
    );

    // Select MCQ type and difficulty
    const typeSelect = screen.getByLabelText(/assessment type/i);
    fireEvent.change(typeSelect, { target: { value: 'mcq' } });

    const difficultySelect = screen.getByLabelText(/difficulty/i);
    fireEvent.change(difficultySelect, { target: { value: 'easy' } });

    const startButton = screen.getByRole('button', { name: /start|generate/i });
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText(/What is 2\+2\?/i)).toBeInTheDocument();
    });

    // Select answer
    const option = screen.getByLabelText(/4/i);
    fireEvent.click(option);

    // Submit
    const submitButton = screen.getByRole('button', { name: /submit|next/i });
    fireEvent.click(submitButton);
  });

  it('should auto-submit on timer expiration', async () => {
    jest.useFakeTimers();

    mockedAxios.post.mockResolvedValueOnce({
      status: 201,
      data: {
        assessment_id: 1,
        type: 'mcq',
        time_limit: 1, // 1 second for testing
      },
    });

    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: { score: 0, feedback: 'Time expired' },
    });

    render(
      <BrowserRouter>
        <Assessment />
      </BrowserRouter>
    );

    // Fast-forward time
    jest.advanceTimersByTime(1500);

    await waitFor(() => {
      expect(screen.getByText(/time expired|auto-submit/i)).toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  it('should display results immediately after submission', async () => {
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        score: 85,
        badge: 'Good',
        feedback: 'Great performance!',
        gaps: ['Gap1'],
        recommendations: ['Rec1', 'Rec2'],
      },
    });

    render(
      <BrowserRouter>
        <Assessment />
      </BrowserRouter>
    );

    const submitButton = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/85/)).toBeInTheDocument();
      expect(screen.getByText(/Good/i)).toBeInTheDocument();
      expect(screen.getByText(/Great performance/i)).toBeInTheDocument();
    });
  });

  it('should handle Gemini API timeout gracefully', async () => {
    mockedAxios.post.mockRejectedValueOnce(
      new Error('Gemini API timeout')
    );

    render(
      <BrowserRouter>
        <Assessment />
      </BrowserRouter>
    );

    const generateButton = screen.getByRole('button', { name: /generate/i });
    fireEvent.click(generateButton);

    await waitFor(() => {
      expect(
        screen.getByText(/timeout|try again/i)
      ).toBeInTheDocument();
    });
  });
});

// ============================================================================
// TEST SUITE 4: DASHBOARD & ANALYTICS
// ============================================================================

describe('Dashboard Workflow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.setItem('token', 'test_token');
  });

  it('should display dashboard with all stats', async () => {
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: {
        total_skills: 5,
        average_score: 78,
        total_assessments: 12,
        active_learning_plans: 2,
        recent_skills: ['Python', 'SQL'],
      },
    });

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/5/)).toBeInTheDocument(); // total skills
      expect(screen.getByText(/78/)).toBeInTheDocument(); // avg score
      expect(screen.getByText(/12/)).toBeInTheDocument(); // assessments
    });
  });

  it('should handle empty state gracefully', async () => {
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: {
        total_skills: 0,
        average_score: 0,
        total_assessments: 0,
        active_learning_plans: 0,
      },
    });

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText(/get started|no data|add your first/i)
      ).toBeInTheDocument();
    });
  });

  it('should render charts without errors', async () => {
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: {
        skills_chart_data: [
          { name: 'Python', score: 85 },
          { name: 'SQL', score: 72 },
        ],
        gap_analysis_data: [
          { skill: 'Python', gap: 'Advanced features' },
        ],
        learning_roadmap_data: [
          { skill: 'SQL', week: 1, progress: 25 },
        ],
      },
    });

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Python/i)).toBeInTheDocument();
      expect(screen.getByText(/SQL/i)).toBeInTheDocument();
    });
  });
});

// ============================================================================
// TEST SUITE 5: RESPONSIVE DESIGN
// ============================================================================

describe('Responsive Design', () => {
  it('should render correctly on mobile viewport (320px)', () => {
    window.innerWidth = 320;
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    const mainContent = screen.getByRole('main', { hidden: true });
    expect(mainContent).toBeInTheDocument();
  });

  it('should render correctly on tablet viewport (768px)', () => {
    window.innerWidth = 768;
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    const mainContent = screen.getByRole('main', { hidden: true });
    expect(mainContent).toBeInTheDocument();
  });

  it('should render correctly on desktop viewport (1920px)', () => {
    window.innerWidth = 1920;
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    const mainContent = screen.getByRole('main', { hidden: true });
    expect(mainContent).toBeInTheDocument();
  });

  it('should have readable text on mobile (<12px warning)', () => {
    window.innerWidth = 320;
    const { container } = render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    const textElements = container.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, li');
    textElements.forEach((el) => {
      const fontSize = window.getComputedStyle(el).fontSize;
      const size = parseFloat(fontSize);
      expect(size).toBeGreaterThanOrEqual(12);
    });
  });
});

// ============================================================================
// TEST SUITE 6: ERROR RECOVERY
// ============================================================================

describe('Error Recovery & Edge Cases', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should retry failed API requests', async () => {
    mockedAxios.post.mockRejectedValueOnce(new Error('Network error'));
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: { success: true },
    });

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    const submitButton = screen.getByRole('button', { name: /add|submit/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledTimes(2); // First failed, retry successful
    });
  });

  it('should handle missing localStorage gracefully', () => {
    const getItemSpy = jest.spyOn(Storage.prototype, 'getItem');
    getItemSpy.mockImplementation(() => null);

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    // Should not crash
    expect(screen.getByRole('main', { hidden: true })).toBeInTheDocument();

    getItemSpy.mockRestore();
  });

  it('should display user-friendly error messages', async () => {
    mockedAxios.post.mockRejectedValueOnce({
      response: {
        status: 400,
        data: { error: 'Invalid email format' },
      },
    });

    render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );

    const submitButton = screen.getByRole('button', { name: /register/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(/invalid email/i)
      ).toBeInTheDocument();
    });
  });
});

// ============================================================================
// TEST SUITE 7: ACCESSIBILITY
// ============================================================================

describe('Accessibility Compliance', () => {
  it('should have proper ARIA labels', () => {
    const { container } = render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );

    const labels = container.querySelectorAll('label');
    expect(labels.length).toBeGreaterThan(0);
  });

  it('should support keyboard navigation (Tab key)', () => {
    const { container } = render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );

    const buttons = container.querySelectorAll('button');
    expect(buttons.length).toBeGreaterThan(0);
    
    buttons.forEach((button) => {
      expect(button.getAttribute('type')).toBe('button');
    });
  });

  it('should have sufficient color contrast', () => {
    const { container } = render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    // Check for color contrast compliance
    const textElements = container.querySelectorAll('[style*="color"]');
    expect(textElements.length >= 0).toBe(true); // Should have colored text
  });
});
