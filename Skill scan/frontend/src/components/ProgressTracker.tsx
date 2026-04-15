/**
 * ProgressTracker Component
 * Displays overall learning plan progress with milestones and timeline
 */

import React from 'react';

interface ProgressTrackerProps {
  completed_weeks: number;
  total_weeks: number;
  current_week: number;
  start_date?: string;
  end_date?: string;
}

const calculateDaysRemaining = (endDate?: string): number | null => {
  if (!endDate) return null;
  const end = new Date(endDate);
  const today = new Date();
  const diffTime = end.getTime() - today.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
};

const getProgressBarColor = (progress: number): string => {
  if (progress >= 80) return 'bg-green-500';
  if (progress >= 60) return 'bg-blue-500';
  if (progress >= 40) return 'bg-yellow-500';
  return 'bg-orange-500';
};

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  completed_weeks,
  total_weeks,
  current_week,
  start_date,
  end_date,
}) => {
  const progress = Math.round((completed_weeks / total_weeks) * 100);
  const daysRemaining = calculateDaysRemaining(end_date);
  const isOverdue = daysRemaining !== null && daysRemaining < 0;

  return (
    <div className="rounded-lg border border-gray-200 bg-gradient-to-br from-blue-50 to-indigo-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Plan Progress</h3>
        <p className="mt-1 text-sm text-gray-600">
          Week {current_week} of {total_weeks}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Overall Progress</span>
          <span className="text-sm font-semibold text-gray-900">{progress}%</span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-gray-200">
          <div
            className={`h-full transition-all duration-500 ${getProgressBarColor(progress)}`}
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
      </div>

      {/* Statistics Grid */}
      <div className="mb-6 grid grid-cols-3 gap-3">
        <div className="rounded-lg bg-white p-3">
          <p className="text-xs text-gray-600">Completed</p>
          <p className="mt-1 text-lg font-bold text-gray-900">
            {completed_weeks}/{total_weeks}
          </p>
          <p className="text-xs text-gray-500">weeks</p>
        </div>

        <div className="rounded-lg bg-white p-3">
          <p className="text-xs text-gray-600">Current</p>
          <p className="mt-1 text-lg font-bold text-blue-600">Week {current_week}</p>
          <p className="text-xs text-gray-500">active</p>
        </div>

        <div className="rounded-lg bg-white p-3">
          <p className="text-xs text-gray-600">Remaining</p>
          <p className="mt-1 text-lg font-bold text-gray-900">
            {total_weeks - completed_weeks}
          </p>
          <p className="text-xs text-gray-500">weeks</p>
        </div>
      </div>

      {/* Timeline Info */}
      {start_date && end_date && (
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-medium text-gray-900">Timeline</p>
            {daysRemaining !== null && (
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  isOverdue
                    ? 'bg-red-100 text-red-800'
                    : daysRemaining <= 7
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-green-100 text-green-800'
                }`}
              >
                {isOverdue
                  ? `${Math.abs(daysRemaining)} days overdue`
                  : `${daysRemaining} days left`}
              </span>
            )}
          </div>

          <div className="flex items-center justify-between text-xs text-gray-600">
            <div>
              <p className="font-medium text-gray-900">
                {new Date(start_date).toLocaleDateString()}
              </p>
              <p className="text-gray-500">Start Date</p>
            </div>

            <div className="flex items-center gap-2 text-gray-400">
              <div className="h-0.5 w-8 bg-gray-300" />
              <span className="text-gray-400">→</span>
              <div className="h-0.5 w-8 bg-gray-300" />
            </div>

            <div className="text-right">
              <p className="font-medium text-gray-900">
                {new Date(end_date).toLocaleDateString()}
              </p>
              <p className="text-gray-500">Target Date</p>
            </div>
          </div>
        </div>
      )}

      {/* Motivation */}
      <div className="mt-4 rounded-lg border-l-4 border-blue-500 bg-blue-50 p-3">
        <p className="text-sm text-blue-900">
          {progress >= 100
            ? '🎉 Congratulations! You have completed this learning plan.'
            : progress >= 75
            ? '💪 You\'re almost there! Keep up the momentum.'
            : progress >= 50
            ? '📚 Halfway through! Great progress so far.'
            : '🚀 Great start! Stay consistent to reach your goals.'}
        </p>
      </div>
    </div>
  );
};
