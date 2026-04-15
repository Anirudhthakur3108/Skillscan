/**
 * Dashboard Page
 * Main dashboard with overview stats, skill charts, and learning roadmap
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  DashboardStats,
  SkillScore,
  LearningPlan as LearningPlanType,
} from '../types/gap';
import { getActivePlans } from '../api/learningPlan';
import { SkillScoreChart } from '../components/SkillScoreChart';
import { GapAnalysisTable } from '../components/GapAnalysisTable';
import { LearningRoadmap } from '../components/LearningRoadmap';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const [stats, setStats] = useState<DashboardStats>({
    total_skills: 0,
    assessments_taken: 0,
    average_score: 0,
    active_plans: 0,
    completed_plans: 0,
  });
  const [skills, setSkills] = useState<SkillScore[]>([]);
  const [learningPlans, setLearningPlans] = useState<LearningPlanType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      setError(null);

      try {
        // Fetch stats
        const statsResponse = await fetch(
          `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/dashboard/stats`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
            },
          }
        );

        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          setStats(statsData.data || {});
        }

        // Fetch skills
        const skillsResponse = await fetch(
          `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/skills/scores`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
            },
          }
        );

        if (skillsResponse.ok) {
          const skillsData = await skillsResponse.json();
          setSkills(skillsData.data || []);
        }

        // Fetch active plans
        const plans = await getActivePlans();
        setLearningPlans(plans);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const handleSkillClick = (skillId: number) => {
    navigate(`/gap-analysis?skill_id=${skillId}`);
  };

  const handleStartAssessment = () => {
    navigate('/assessment');
  };

  const handleViewLearningPlans = () => {
    navigate('/learning-plans');
  };

  const handlePlanClick = (planId: string) => {
    navigate(`/learning-plan/${planId}`);
  };

  const getScoreLevelLabel = (score: number): string => {
    if (score >= 90) return 'Excellent';
    if (score >= 80) return 'Very Good';
    if (score >= 70) return 'Good';
    if (score >= 60) return 'Fair';
    return 'Needs Work';
  };

  const getScoreLevelColor = (score: number): string => {
    if (score >= 90) return 'text-green-600 bg-green-50';
    if (score >= 80) return 'text-blue-600 bg-blue-50';
    if (score >= 70) return 'text-yellow-600 bg-yellow-50';
    if (score >= 60) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome to SkillScan
          </h1>
          <p className="mt-2 text-gray-600">
            Track your skills, identify gaps, and create learning plans
          </p>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Stats Cards */}
        {!loading && (
          <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Total Skills */}
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Skills</p>
                  <p className="mt-2 text-3xl font-bold text-gray-900">
                    {stats.total_skills}
                  </p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100">
                  <span className="text-xl">📊</span>
                </div>
              </div>
            </div>

            {/* Assessments Taken */}
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    Assessments Taken
                  </p>
                  <p className="mt-2 text-3xl font-bold text-gray-900">
                    {stats.assessments_taken}
                  </p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-100">
                  <span className="text-xl">✅</span>
                </div>
              </div>
            </div>

            {/* Average Score */}
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    Average Score
                  </p>
                  <p className="mt-2 text-3xl font-bold text-gray-900">
                    {Math.round(stats.average_score)}%
                  </p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100">
                  <span className="text-xl">⭐</span>
                </div>
              </div>
            </div>

            {/* Active Plans */}
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    Active Plans
                  </p>
                  <p className="mt-2 text-3xl font-bold text-gray-900">
                    {stats.active_plans}
                  </p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-orange-100">
                  <span className="text-xl">🎯</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Loading State for Stats */}
        {loading && (
          <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="rounded-lg border border-gray-200 bg-white p-6 animate-pulse"
              >
                <div className="h-4 w-20 rounded bg-gray-200 mb-4" />
                <div className="h-8 w-32 rounded bg-gray-200" />
              </div>
            ))}
          </div>
        )}

        {/* Quick Actions */}
        <div className="mb-8 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <button
            onClick={handleStartAssessment}
            className="rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          >
            📝 Start Assessment
          </button>
          <button
            onClick={() => navigate('/gap-analysis')}
            className="rounded-lg bg-purple-600 px-4 py-3 text-sm font-medium text-white hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors"
          >
            🔍 View Gap Analysis
          </button>
          <button
            onClick={handleViewLearningPlans}
            className="rounded-lg bg-green-600 px-4 py-3 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors"
          >
            📚 View Learning Plans
          </button>
        </div>

        {/* Main Content Grid */}
        <div className="space-y-8">
          {/* Skill Scores Chart */}
          {!loading && skills.length > 0 && (
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <SkillScoreChart
                skills={skills}
                onSkillClick={handleSkillClick}
              />
            </div>
          )}

          {/* Learning Roadmap */}
          {!loading && (
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <LearningRoadmap
                plans={learningPlans}
                onPlanClick={handlePlanClick}
              />
            </div>
          )}

          {/* Gap Analysis Table */}
          {!loading && (
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">
                Recent Gaps Identified
              </h3>
              {skills.length > 0 ? (
                <GapAnalysisTable
                  gaps={[]} // Would be populated from gap analysis API
                  onViewDetails={(gapId) => console.log('View gap:', gapId)}
                  onCreatePlan={(gapId) => console.log('Create plan:', gapId)}
                />
              ) : (
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
                  <p className="text-gray-600">
                    No gaps identified yet. Complete an assessment to get started.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Overall Progress */}
          {!loading && learningPlans.length > 0 && (
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">
                Overall Progress
              </h3>
              <div className="space-y-4">
                {learningPlans.map((plan) => {
                  const progress = plan.progress;
                  return (
                    <div key={plan.id} className="border-b border-gray-200 pb-4 last:border-b-0 last:pb-0">
                      <div className="mb-2 flex items-center justify-between">
                        <p className="font-medium text-gray-900">
                          {plan.skill_name}
                        </p>
                        <span className="text-sm font-semibold text-gray-700">
                          {progress}%
                        </span>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
                        <div
                          className={`h-full transition-all ${
                            progress >= 80
                              ? 'bg-green-500'
                              : progress >= 60
                              ? 'bg-blue-500'
                              : progress >= 40
                              ? 'bg-yellow-500'
                              : 'bg-orange-500'
                          }`}
                          style={{ width: `${Math.min(progress, 100)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Empty State */}
        {!loading && stats.total_skills === 0 && (
          <div className="rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-12 text-center">
            <p className="mb-4 text-lg font-medium text-gray-900">
              Get Started with SkillScan
            </p>
            <p className="mb-6 text-gray-600">
              Start by taking an assessment to evaluate your skills
            </p>
            <button
              onClick={handleStartAssessment}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              📝 Take Your First Assessment
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
