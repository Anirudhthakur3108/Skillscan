/**
 * GapCard Component
 * Displays individual gap information with priority badge and actions
 */

import React from 'react';
import { Gap, PriorityLevel } from '../types/gap';

interface GapCardProps {
  gap: Gap;
  onCreatePlan: (gapId: string) => void;
}

const getPriorityColor = (priority: PriorityLevel): string => {
  switch (priority) {
    case 'high':
      return 'bg-red-100 text-red-800 border-red-300';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    case 'low':
      return 'bg-green-100 text-green-800 border-green-300';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300';
  }
};

const getPriorityBgColor = (priority: PriorityLevel): string => {
  switch (priority) {
    case 'high':
      return 'bg-red-50 hover:bg-red-100';
    case 'medium':
      return 'bg-yellow-50 hover:bg-yellow-100';
    case 'low':
      return 'bg-green-50 hover:bg-green-100';
    default:
      return 'bg-gray-50 hover:bg-gray-100';
  }
};

export const GapCard: React.FC<GapCardProps> = ({ gap, onCreatePlan }) => {
  const impactPercentage = gap.impact;
  const impactColor =
    impactPercentage >= 75
      ? 'text-red-600'
      : impactPercentage >= 50
      ? 'text-yellow-600'
      : 'text-green-600';

  return (
    <div
      className={`rounded-lg border border-gray-200 p-4 transition-colors ${getPriorityBgColor(
        gap.priority
      )}`}
    >
      <div className="mb-3 flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{gap.name}</h3>
          {gap.description && (
            <p className="mt-1 text-sm text-gray-600">{gap.description}</p>
          )}
        </div>
        <span
          className={`ml-2 inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium capitalize ${getPriorityColor(
            gap.priority
          )}`}
        >
          {gap.priority} Priority
        </span>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded bg-white/50 px-3 py-2">
          <p className="text-xs text-gray-600">Frequency</p>
          <p className="mt-1 font-semibold text-gray-900">
            {gap.frequency} assessment{gap.frequency !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="rounded bg-white/50 px-3 py-2">
          <p className="text-xs text-gray-600">Impact Score</p>
          <p className={`mt-1 font-semibold ${impactColor}`}>
            {impactPercentage}%
          </p>
        </div>
      </div>

      {gap.recommendations.length > 0 && (
        <div className="mb-4">
          <p className="mb-2 text-xs font-medium text-gray-700">
            Recommendations:
          </p>
          <ul className="space-y-1">
            {gap.recommendations.slice(0, 2).map((rec, idx) => (
              <li key={idx} className="flex items-start text-xs text-gray-700">
                <span className="mr-2 text-gray-400">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        onClick={() => onCreatePlan(gap.id)}
        className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        aria-label={`Create learning plan for ${gap.name}`}
      >
        Create Learning Plan
      </button>
    </div>
  );
};
