/**
 * ResourceCard Component
 * Displays learning resource with type, platform, and duration information
 */

import React from 'react';
import { Resource, ResourceType } from '../types/gap';

interface ResourceCardProps {
  resource: Resource;
  onOpen: (link: string) => void;
}

const getResourceTypeIcon = (type: ResourceType): string => {
  switch (type) {
    case 'course':
      return '📚';
    case 'project':
      return '🔧';
    case 'video':
      return '▶️';
    case 'documentation':
      return '📄';
    default:
      return '📌';
  }
};

const getResourceTypeLabel = (type: ResourceType): string => {
  return type.charAt(0).toUpperCase() + type.slice(1);
};

const getDifficultyColor = (difficulty: string): string => {
  switch (difficulty) {
    case 'easy':
      return 'bg-green-100 text-green-800';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800';
    case 'hard':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const getPriorityBadgeColor = (priority: string): string => {
  switch (priority) {
    case 'high':
      return 'bg-red-100 text-red-800';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800';
    case 'low':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export const ResourceCard: React.FC<ResourceCardProps> = ({
  resource,
  onOpen,
}) => {
  return (
    <div className="flex flex-col rounded-lg border border-gray-200 bg-white p-4 transition-shadow hover:shadow-md">
      <div className="mb-3 flex items-start justify-between">
        <div className="flex items-start gap-3">
          <span className="text-2xl">{getResourceTypeIcon(resource.type)}</span>
          <div className="flex-1">
            <h4 className="font-semibold text-gray-900">{resource.title}</h4>
            <p className="text-sm text-gray-600">{resource.platform}</p>
          </div>
        </div>
        {resource.completed && (
          <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
            ✓ Done
          </span>
        )}
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
          {getResourceTypeLabel(resource.type)}
        </span>
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getDifficultyColor(
            resource.difficulty
          )}`}
        >
          {resource.difficulty.charAt(0).toUpperCase() +
            resource.difficulty.slice(1)}
        </span>
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getPriorityBadgeColor(
            resource.priority
          )}`}
        >
          {resource.priority.charAt(0).toUpperCase() +
            resource.priority.slice(1)}
        </span>
      </div>

      <p className="mb-4 text-xs text-gray-600">⏱️ {resource.duration}</p>

      <button
        onClick={() => onOpen(resource.link)}
        className="mt-auto w-full rounded-lg bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        aria-label={`Open ${resource.title}`}
      >
        Open Resource
      </button>
    </div>
  );
};
