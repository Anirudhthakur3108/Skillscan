/**
 * LearningRoadmap Component
 * Timeline visualization of learning plans with progress tracking
 */

import React, { useMemo } from 'react';
import { LearningPlan } from '../types/gap';

interface LearningRoadmapProps {
  plans: LearningPlan[];
  onPlanClick: (planId: string) => void;
}

const getProgressColor = (progress: number): string => {
  if (progress >= 80) return 'bg-green-500';
  if (progress >= 60) return 'bg-blue-500';
  if (progress >= 40) return 'bg-yellow-500';
  return 'bg-orange-500';
};

const getProgressTextColor = (progress: number): string => {
  if (progress >= 80) return 'text-green-700';
  if (progress >= 60) return 'text-blue-700';
  if (progress >= 40) return 'text-yellow-700';
  return 'text-orange-700';
};

const getStatusColor = (progress: number): string => {
  if (progress === 100) return 'bg-green-100 text-green-800';
  if (progress > 0) return 'bg-blue-100 text-blue-800';
  return 'bg-gray-100 text-gray-800';
};

const getStatusLabel = (progress: number): string => {
  if (progress === 100) return 'Completed';
  if (progress > 0) return 'In Progress';
  return 'Not Started';
};

export const LearningRoadmap: React.FC<LearningRoadmapProps> = ({
  plans,
  onPlanClick,
}) => {
  const sortedPlans = useMemo(
    () =>
      [...plans].sort((a, b) => {
        const dateA = new Date(a.start_date || '').getTime();
        const dateB = new Date(b.start_date || '').getTime();
        return dateA - dateB;
      }),
    [plans]
  );

  const getTimelinePosition = (planIndex: number, totalPlans: number): number => {
    return (planIndex / totalPlans) * 100;
  };

  const calculateDaysRemaining = (endDate?: string): number | null => {
    if (!endDate) return null;
    const end = new Date(endDate);
    const today = new Date();
    const diffTime = end.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : null;
  };

  if (plans.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <p className="text-gray-600">No learning plans yet. Start by creating your first plan! 🚀</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      {/* Header */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900">Learning Roadmap</h3>
        <p className="mt-1 text-sm text-gray-600">
          {plans.length} active plan{plans.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Timeline */}
      <div className="space-y-6">
        {sortedPlans.map((plan, index) => {
          const daysRemaining = calculateDaysRemaining(plan.target_completion_date);
          const isOverdue =
            plan.target_completion_date &&
            new Date(plan.target_completion_date) < new Date() &&
            plan.progress < 100;

          return (
            <div
              key={plan.id}
              onClick={() => onPlanClick(plan.id)}
              className="cursor-pointer rounded-lg border border-gray-200 bg-gradient-to-r from-gray-50 to-white p-4 transition-all hover:shadow-md hover:border-blue-300"
            >
              {/* Timeline Indicator */}
              <div className="mb-3 flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100">
                  <span className="text-xs font-semibold text-blue-800">{index + 1}</span>
                </div>
                <span
                  className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${getStatusColor(
                    plan.progress
                  )}`}
                >
                  {getStatusLabel(plan.progress)}
                </span>
                {isOverdue && (
                  <span className="inline-flex items-center rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-800">
                    ⚠️ Overdue
                  </span>
                )}
              </div>

              {/* Plan Details */}
              <div className="mb-4">
                <h4 className="font-semibold text-gray-900">{plan.skill_name}</h4>
                <p className="mt-1 text-sm text-gray-600">
                  {plan.gap_ids.length} gap{plan.gap_ids.length !== 1 ? 's' : ''} being addressed • {plan.duration_weeks}-week plan
                </p>
              </div>

              {/* Dates */}
              {plan.start_date && plan.target_completion_date && (
                <div className="mb-4 flex items-center justify-between text-xs text-gray-600">
                  <div>
                    <p className="font-medium text-gray-900">
                      {new Date(plan.start_date).toLocaleDateString()}
                    </p>
                    <p className="text-gray-500">Start</p>
                  </div>
                  <div className="flex-1 mx-3 h-0.5 bg-gray-300" />
                  <div className="text-right">
                    <p className="font-medium text-gray-900">
                      {new Date(plan.target_completion_date).toLocaleDateString()}
                    </p>
                    <p className="text-gray-500">Target</p>
                  </div>
                  {daysRemaining && (
                    <div className="ml-3 text-right">
                      <p className="font-medium text-gray-900">{daysRemaining}d</p>
                      <p className="text-gray-500">remaining</p>
                    </div>
                  )}
                </div>
              )}

              {/* Progress Bar */}
              <div className="mb-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs font-medium text-gray-700">Progress</span>
                  <span className={`text-xs font-semibold ${getProgressTextColor(plan.progress)}`}>
                    {plan.progress}%
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
                  <div
                    className={`h-full transition-all duration-300 ${getProgressColor(
                      plan.progress
                    )}`}
                    style={{ width: `${Math.min(plan.progress, 100)}%` }}
                  />
                </div>
              </div>

              {/* Milestone Info */}
              <div className="flex items-center justify-between text-xs text-gray-600">
                <span>
                  Week {plan.milestones.filter((m) => m.completed).length}/{plan.duration_weeks} completed
                </span>
                <span className="font-medium text-gray-900">
                  {Math.round(plan.completed_hours || 0)} / {Math.round(plan.total_hours)} hours
                </span>
              </div>

              {/* Hover Hint */}
              <div className="mt-3 flex items-center text-xs text-blue-600">
                <span>Click to view details →</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary Stats */}
      <div className="mt-6 border-t border-gray-200 pt-4">
        <div className="grid grid-cols-4 gap-3 text-center text-xs">
          <div>
            <p className="text-gray-600">Total Plans</p>
            <p className="mt-1 text-lg font-bold text-gray-900">{plans.length}</p>
          </div>
          <div>
            <p className="text-gray-600">In Progress</p>
            <p className="mt-1 text-lg font-bold text-blue-600">
              {plans.filter((p) => p.progress > 0 && p.progress < 100).length}
            </p>
          </div>
          <div>
            <p className="text-gray-600">Completed</p>
            <p className="mt-1 text-lg font-bold text-green-600">
              {plans.filter((p) => p.progress === 100).length}
            </p>
          </div>
          <div>
            <p className="text-gray-600">Avg Progress</p>
            <p className="mt-1 text-lg font-bold text-gray-900">
              {Math.round(plans.reduce((sum, p) => sum + p.progress, 0) / plans.length)}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
