/**
 * GapAnalysisTable Component
 * Table displaying gaps ranked by priority with action buttons
 */

import React from 'react';
import { Gap, LearningPlanStatus } from '../types/gap';

interface GapAnalysisTableRow extends Gap {
  status?: LearningPlanStatus;
}

interface GapAnalysisTableProps {
  gaps: GapAnalysisTableRow[];
  onViewDetails: (gapId: string) => void;
  onCreatePlan: (gapId: string) => void;
}

const getPriorityBadgeColor = (priority: string): string => {
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

const getStatusBadgeColor = (status?: LearningPlanStatus): string => {
  switch (status) {
    case 'not_started':
      return 'bg-gray-100 text-gray-800';
    case 'in_progress':
      return 'bg-blue-100 text-blue-800';
    case 'completed':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const getStatusLabel = (status?: LearningPlanStatus): string => {
  switch (status) {
    case 'not_started':
      return 'Not Started';
    case 'in_progress':
      return 'In Progress';
    case 'completed':
      return 'Completed';
    default:
      return 'Unknown';
  }
};

export const GapAnalysisTable: React.FC<GapAnalysisTableProps> = ({
  gaps,
  onViewDetails,
  onCreatePlan,
}) => {
  if (gaps.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <p className="text-gray-600">No gaps identified. Great job! 🎉</p>
      </div>
    );
  }

  // Sort by priority and impact
  const sortedGaps = [...gaps].sort((a, b) => {
    const priorityOrder = { high: 0, medium: 1, low: 2 };
    const priorityDiff =
      priorityOrder[a.priority as keyof typeof priorityOrder] -
      priorityOrder[b.priority as keyof typeof priorityOrder];
    if (priorityDiff !== 0) return priorityDiff;
    return b.impact - a.impact;
  });

  return (
    <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">
                Gap Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">
                Priority
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-700">
                Frequency
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-700">
                Impact
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sortedGaps.map((gap) => (
              <tr key={gap.id} className="transition-colors hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div>
                    <p className="font-medium text-gray-900">{gap.name}</p>
                    {gap.description && (
                      <p className="mt-1 text-sm text-gray-600">{gap.description}</p>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span
                    className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium capitalize ${getPriorityBadgeColor(
                      gap.priority
                    )}`}
                  >
                    {gap.priority}
                  </span>
                </td>
                <td className="px-6 py-4 text-center">
                  <span className="inline-flex items-center rounded-lg bg-gray-100 px-3 py-1 text-sm font-medium text-gray-800">
                    {gap.frequency}
                  </span>
                </td>
                <td className="px-6 py-4 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <div className="h-2 w-16 overflow-hidden rounded-full bg-gray-200">
                      <div
                        className={`h-full transition-all ${
                          gap.impact >= 75
                            ? 'bg-red-500'
                            : gap.impact >= 50
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                        }`}
                        style={{ width: `${gap.impact}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold text-gray-700">
                      {gap.impact}%
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span
                    className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${getStatusBadgeColor(
                      gap.status
                    )}`}
                  >
                    {getStatusLabel(gap.status)}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onViewDetails(gap.id)}
                      className="inline-flex items-center rounded-md bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700 transition-colors hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                      aria-label={`View details for ${gap.name}`}
                    >
                      Details
                    </button>
                    {gap.status !== 'completed' && (
                      <button
                        onClick={() => onCreatePlan(gap.id)}
                        className="inline-flex items-center rounded-md bg-green-50 px-3 py-1.5 text-xs font-medium text-green-700 transition-colors hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                        aria-label={`Create plan for ${gap.name}`}
                      >
                        Plan
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div className="border-t border-gray-200 bg-gray-50 px-6 py-3">
        <div className="flex flex-wrap items-center justify-between gap-4 text-sm">
          <span className="text-gray-600">
            <strong>{gaps.length}</strong> total gap{gaps.length !== 1 ? 's' : ''} identified
          </span>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">
              <strong className="text-red-600">
                {gaps.filter((g) => g.priority === 'high').length}
              </strong>{' '}
              high priority
            </span>
            <span className="text-gray-600">
              <strong className="text-yellow-600">
                {gaps.filter((g) => g.priority === 'medium').length}
              </strong>{' '}
              medium priority
            </span>
            <span className="text-gray-600">
              <strong className="text-green-600">
                {gaps.filter((g) => g.priority === 'low').length}
              </strong>{' '}
              low priority
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
