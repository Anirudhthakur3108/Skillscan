/**
 * ProgressBar Component
 * Visual progress indicator with dynamic coloring
 */

import React, { useMemo } from 'react';
import { ProgressBarProps } from '../../types/assessment';

const ProgressBar: React.FC<ProgressBarProps> = ({
  current,
  total,
  showLabel = true,
  className = '',
}) => {
  // Calculate percentage
  const percentage = useMemo(() => {
    if (total === 0) return 0;
    return Math.min(100, (current / total) * 100);
  }, [current, total]);

  // Determine color based on progress
  const getProgressColor = (): string => {
    if (percentage === 100) return 'bg-green-500';
    if (percentage >= 70) return 'bg-green-400';
    if (percentage >= 50) return 'bg-yellow-400';
    if (percentage >= 30) return 'bg-orange-400';
    return 'bg-red-400';
  };

  // Determine background color
  const getBackgroundColor = (): string => {
    if (percentage === 100) return 'bg-green-100';
    if (percentage >= 70) return 'bg-green-50';
    if (percentage >= 50) return 'bg-yellow-50';
    if (percentage >= 30) return 'bg-orange-50';
    return 'bg-red-50';
  };

  return (
    <div className={`w-full ${className}`}>
      {/* Background bar container */}
      <div className={`relative w-full h-3 rounded-full bg-gray-200 overflow-hidden ${getBackgroundColor()}`}>
        {/* Progress fill */}
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${getProgressColor()}`}
          style={{ width: `${percentage}%` }}
        />

        {/* Animated shine effect */}
        <div
          className="absolute top-0 left-0 h-full w-1/3 opacity-30 animate-pulse"
          style={{
            background: 'linear-gradient(90deg, transparent, white, transparent)',
          }}
        />
      </div>

      {/* Optional label */}
      {showLabel && (
        <div className="mt-2 flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Progress</span>
          <span className="text-sm font-semibold text-gray-900">
            {current} / {total}
          </span>
        </div>
      )}

      {/* Percentage text */}
      <div className="mt-1 text-xs text-gray-600">
        {Math.round(percentage)}% Complete
      </div>
    </div>
  );
};

export default ProgressBar;
