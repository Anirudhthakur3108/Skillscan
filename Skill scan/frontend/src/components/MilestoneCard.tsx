/**
 * MilestoneCard Component
 * Displays weekly milestone with success criteria and resources
 */

import React, { useState } from 'react';
import { Milestone } from '../types/gap';
import { ResourceCard } from './ResourceCard';

interface MilestoneCardProps {
  milestone: Milestone;
  onUpdate: (week: number, completed: boolean) => void;
}

export const MilestoneCard: React.FC<MilestoneCardProps> = ({
  milestone,
  onUpdate,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showResources, setShowResources] = useState(false);

  const handleToggleComplete = (e: React.ChangeEvent<HTMLInputElement>) => {
    onUpdate(milestone.week, e.target.checked);
  };

  const handleResourceOpen = (link: string) => {
    window.open(link, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white transition-all hover:shadow-md">
      <div
        className="cursor-pointer p-4"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={milestone.completed}
                onChange={handleToggleComplete}
                onClick={(e) => e.stopPropagation()}
                className="h-5 w-5 cursor-pointer rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                aria-label={`Mark week ${milestone.week} as complete`}
              />
              <span className="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-sm font-semibold text-blue-800">
                Week {milestone.week}
              </span>
              {milestone.completed && (
                <span className="text-lg">✓</span>
              )}
            </div>
            <h3
              className={`mt-2 text-lg font-semibold ${
                milestone.completed ? 'text-gray-500 line-through' : 'text-gray-900'
              }`}
            >
              {milestone.title}
            </h3>
            <p className="mt-1 text-sm text-gray-600">{milestone.description}</p>
          </div>
          <button
            className="ml-2 text-gray-400 transition-colors hover:text-gray-600"
            aria-label={isExpanded ? 'Collapse milestone' : 'Expand milestone'}
          >
            <svg
              className={`h-5 w-5 transform transition-transform ${
                isExpanded ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 14l-7 7m0 0l-7-7m7 7V3"
              />
            </svg>
          </button>
        </div>

        <div className="mt-3 flex items-center justify-between text-sm">
          <span className="text-gray-600">
            ⏱️ {milestone.estimated_hours} hours
          </span>
          <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
            {milestone.resources.length} resource
            {milestone.resources.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {isExpanded && (
        <div className="border-t border-gray-200 bg-gray-50 p-4">
          {/* Success Criteria */}
          <div className="mb-6">
            <h4 className="mb-3 font-semibold text-gray-900">Success Criteria</h4>
            <ul className="space-y-2">
              {milestone.success_criteria.map((criterion, idx) => (
                <li key={idx} className="flex items-start gap-3 text-sm">
                  <input
                    type="checkbox"
                    className="mt-0.5 h-4 w-4 cursor-pointer rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    aria-label={`Criteria: ${criterion}`}
                  />
                  <span className="text-gray-700">{criterion}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Toggle */}
          <div>
            <button
              onClick={() => setShowResources(!showResources)}
              className="mb-3 flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700"
            >
              <svg
                className={`h-4 w-4 transform transition-transform ${
                  showResources ? 'rotate-90' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
              {milestone.resources.length} Learning Resource
              {milestone.resources.length !== 1 ? 's' : ''}
            </button>

            {showResources && (
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {milestone.resources.map((resource) => (
                  <ResourceCard
                    key={resource.id}
                    resource={resource}
                    onOpen={handleResourceOpen}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
