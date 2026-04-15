/**
 * LearningPlan Page
 * Displays generated learning plan with milestones and duration selection
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  LearningPlan as LearningPlanType,
  GenerateLearningPlanRequest,
  DifficultyLevel,
} from '../types/gap';
import {
  generateLearningPlan,
  getLearningPlan,
  updateProgress,
  getActivePlans,
} from '../api/learningPlan';
import { getGapAnalysis } from '../api/gap';
import { MilestoneCard } from '../components/MilestoneCard';
import { ProgressTracker } from '../components/ProgressTracker';

type DurationWeeks = 2 | 3 | 4 | 6;

const getDurationRecommendation = (score: number): { weeks: DurationWeeks; reason: string } => {
  if (score >= 90) {
    return {
      weeks: 2,
      reason: `Score ${Math.round(score)}% - You're highly skilled! Fast-track 2-week plan.`,
    };
  }
  if (score >= 80) {
    return {
      weeks: 3,
      reason: `Score ${Math.round(score)}% - 3-week plan recommended for quick mastery.`,
    };
  }
  if (score >= 60) {
    return {
      weeks: 4,
      reason: `Score ${Math.round(score)}% - 4-week intensive plan recommended.`,
    };
  }
  return {
    weeks: 6,
    reason: `Score ${Math.round(score)}% - 6-week comprehensive plan recommended.`,
  };
};

export const LearningPlan: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const skillId = searchParams.get('skill_id')
    ? parseInt(searchParams.get('skill_id')!)
    : null;
  const initialGapId = searchParams.get('gap_id');

  const [learningPlan, setLearningPlan] = useState<LearningPlanType | null>(null);
  const [recommendedDuration, setRecommendedDuration] = useState<DurationWeeks>(4);
  const [selectedDuration, setSelectedDuration] = useState<DurationWeeks>(4);
  const [userLevel, setUserLevel] = useState<DifficultyLevel>('medium');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentWeek, setCurrentWeek] = useState(1);
  const [showRecommendation, setShowRecommendation] = useState(true);

  // Fetch and generate plan
  useEffect(() => {
    const initializePlan = async () => {
      if (!skillId) return;

      setLoading(true);
      setError(null);

      try {
        // Get gap analysis to calculate recommendation
        const gapAnalysis = await getGapAnalysis(skillId);
        const { weeks, reason } = getDurationRecommendation(
          gapAnalysis.current_score
        );
        setRecommendedDuration(weeks);
        setSelectedDuration(weeks);

        // Generate learning plan
        const request: GenerateLearningPlanRequest = {
          skill_id: skillId,
          gap_ids: gapAnalysis.gaps.map((g) => g.id),
          duration_weeks: weeks,
          user_level: userLevel,
        };

        const plan = await generateLearningPlan(request);
        setLearningPlan(plan);
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : 'Failed to generate learning plan';
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    initializePlan();
  }, [skillId, userLevel]);

  const handleDurationChange = (duration: DurationWeeks) => {
    setSelectedDuration(duration);
  };

  const handleMilestoneUpdate = useCallback(
    async (week: number, completed: boolean) => {
      if (!learningPlan) return;

      try {
        const completedWeeks = completed
          ? [...(learningPlan.milestones
              .filter((m) => m.completed)
              .map((m) => m.week) || []), week]
          : learningPlan.milestones
              .filter((m) => m.completed && m.week !== week)
              .map((m) => m.week);

        const updated = await updateProgress({
          plan_id: learningPlan.id,
          completed_milestone_weeks: completedWeeks,
        });

        setLearningPlan(updated);
        setCurrentWeek(Math.max(...completedWeeks) + 1);
      } catch (err) {
        console.error('Error updating milestone:', err);
      }
    },
    [learningPlan]
  );

  const handleStartPlan = async () => {
    if (!learningPlan) return;

    try {
      setLoading(true);

      // If duration changed, regenerate plan
      if (selectedDuration !== learningPlan.duration_weeks && skillId) {
        const gapAnalysis = await getGapAnalysis(skillId);
        const request: GenerateLearningPlanRequest = {
          skill_id: skillId,
          gap_ids: gapAnalysis.gaps.map((g) => g.id),
          duration_weeks: selectedDuration,
          user_level: userLevel,
        };

        const newPlan = await generateLearningPlan(request);
        setLearningPlan(newPlan);
        setCurrentWeek(1);
      }

      navigate(`/learning-plan/${learningPlan.id}`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to start plan'
      );
    } finally {
      setLoading(false);
    }
  };

  if (!skillId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="mx-auto max-w-4xl px-4 py-8">
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
            <p className="text-gray-600">
              No skill selected. Please go back and select a skill.
            </p>
            <button
              onClick={() => navigate('/gap-analysis')}
              className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
              Back to Gap Analysis
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/gap-analysis')}
            className="mb-4 flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
          >
            ← Back to Gap Analysis
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Learning Plan</h1>
          {learningPlan && (
            <p className="mt-2 text-lg text-gray-600">
              {learningPlan.skill_name} • {learningPlan.gap_ids.length} gap
              {learningPlan.gap_ids.length !== 1 ? 's' : ''} to address
            </p>
          )}
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
            <div className="inline-flex h-8 w-8 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
            <p className="mt-3 text-gray-600">Generating your learning plan...</p>
          </div>
        )}

        {learningPlan && !loading && (
          <>
            {/* Recommendation Alert */}
            {showRecommendation && (
              <div className="mb-6 rounded-lg border-l-4 border-blue-500 bg-blue-50 p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-blue-900">
                      💡 Recommended Duration
                    </p>
                    <p className="mt-1 text-sm text-blue-800">
                      {learningPlan.recommendation_reason}
                    </p>
                  </div>
                  <button
                    onClick={() => setShowRecommendation(false)}
                    className="text-blue-400 hover:text-blue-600"
                  >
                    ✕
                  </button>
                </div>
              </div>
            )}

            {/* Duration Selector */}
            <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900">
                Select Learning Duration
              </h2>
              <p className="mt-1 text-sm text-gray-600">
                Recommended: {recommendedDuration} weeks
              </p>

              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                {[2, 3, 4, 6].map((weeks) => (
                  <button
                    key={weeks}
                    onClick={() => handleDurationChange(weeks as DurationWeeks)}
                    className={`rounded-lg border-2 px-4 py-3 text-center font-semibold transition-all ${
                      selectedDuration === weeks
                        ? 'border-blue-600 bg-blue-50 text-blue-900'
                        : 'border-gray-200 bg-white text-gray-700 hover:border-blue-300'
                    }`}
                  >
                    <span className="block text-2xl">{weeks}</span>
                    <span className="text-xs text-gray-600">
                      week{weeks > 1 ? 's' : ''}
                    </span>
                  </button>
                ))}
              </div>

              {selectedDuration !== recommendedDuration && (
                <p className="mt-3 text-xs text-yellow-700 bg-yellow-50 rounded px-3 py-2">
                  ⚠️ You've selected {selectedDuration} weeks instead of the
                  recommended {recommendedDuration} weeks. The plan will be{' '}
                  {selectedDuration > recommendedDuration ? 'more gradual' : 'more intensive'}.
                </p>
              )}
            </div>

            {/* Progress Tracker */}
            <div className="mb-6">
              <ProgressTracker
                completed_weeks={
                  learningPlan.milestones.filter((m) => m.completed).length
                }
                total_weeks={learningPlan.duration_weeks}
                current_week={currentWeek}
                start_date={learningPlan.start_date}
                end_date={learningPlan.target_completion_date}
              />
            </div>

            {/* Milestones Section */}
            <div className="mb-6">
              <h2 className="mb-4 text-xl font-semibold text-gray-900">
                Weekly Milestones
              </h2>
              <div className="space-y-4">
                {learningPlan.milestones.map((milestone) => (
                  <MilestoneCard
                    key={milestone.week}
                    milestone={milestone}
                    onUpdate={handleMilestoneUpdate}
                  />
                ))}
              </div>
            </div>

            {/* Summary Stats */}
            <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
              <div className="rounded-lg border border-gray-200 bg-white p-4">
                <p className="text-xs text-gray-600">Total Hours</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {learningPlan.total_hours}
                </p>
              </div>
              <div className="rounded-lg border border-gray-200 bg-white p-4">
                <p className="text-xs text-gray-600">Total Resources</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {learningPlan.resources.length}
                </p>
              </div>
              <div className="rounded-lg border border-gray-200 bg-white p-4">
                <p className="text-xs text-gray-600">Resource Mix</p>
                <div className="mt-2 space-y-1 text-xs">
                  <p>📚 40% Courses</p>
                  <p>🔧 35% Projects</p>
                </div>
              </div>
              <div className="rounded-lg border border-gray-200 bg-white p-4">
                <p className="text-xs text-gray-600">Additional</p>
                <div className="mt-2 space-y-1 text-xs">
                  <p>▶️ 15% Videos</p>
                  <p>📄 10% Docs</p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-3 sm:flex-row">
              <button
                onClick={handleStartPlan}
                className="flex-1 rounded-lg bg-blue-600 px-6 py-3 text-center font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
              >
                🚀 Start Learning Plan
              </button>
              <button
                onClick={() => navigate('/gap-analysis')}
                className="flex-1 rounded-lg border border-gray-200 bg-white px-6 py-3 text-center font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
              >
                Adjust Plan
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
