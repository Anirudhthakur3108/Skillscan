/**
 * AssessmentTimer Component
 * Countdown timer with visual feedback (MM:SS format, color changes, flashing)
 */

import React, { useEffect, useState } from 'react';
import { TimerProps } from '../../types/assessment';

interface DisplayTime {
  minutes: number;
  seconds: number;
}

const AssessmentTimer: React.FC<TimerProps> = ({ totalSeconds, onTimeExpire, isPaused = false }) => {
  const [remainingSeconds, setRemainingSeconds] = useState<number>(totalSeconds);
  const [isWarning, setIsWarning] = useState<boolean>(false);
  const [isCritical, setIsCritical] = useState<boolean>(false);

  // Format time to MM:SS
  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate percentage for visual feedback
  const getTimePercentage = (): number => {
    return Math.max(0, (remainingSeconds / totalSeconds) * 100);
  };

  // Determine color based on remaining time
  const getTimerColor = (): string => {
    if (isCritical) return 'text-red-600';
    if (isWarning) return 'text-yellow-600';
    return 'text-gray-700';
  };

  // Countdown timer effect
  useEffect(() => {
    if (isPaused || remainingSeconds <= 0) return;

    const interval = setInterval(() => {
      setRemainingSeconds((prev) => {
        const next = prev - 1;

        // Update warning states
        if (next === 60) setIsWarning(true);
        if (next === 10) setIsCritical(true);
        if (next <= 0) {
          clearInterval(interval);
          onTimeExpire();
          return 0;
        }

        return next;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isPaused, remainingSeconds, onTimeExpire]);

  // Animation class for flashing effect when critical
  const flashingClass = isCritical && remainingSeconds % 2 === 0 ? 'animate-pulse' : '';

  return (
    <div className="w-full">
      {/* Warning message */}
      {isWarning && (
        <div className="mb-4 p-3 rounded-lg bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm font-medium">
          ⏰ Less than 1 minute remaining
        </div>
      )}

      {/* Timer display */}
      <div className={`flex items-center justify-center p-4 rounded-lg ${flashingClass}`}>
        <div className={`text-center transition-all duration-300`}>
          {/* Large timer display */}
          <div className={`text-4xl font-bold font-mono ${getTimerColor()} transition-colors duration-300`}>
            {formatTime(remainingSeconds)}
          </div>

          {/* Progress bar */}
          <div className="mt-3 w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                isCritical ? 'bg-red-500' : isWarning ? 'bg-yellow-500' : 'bg-green-500'
              }`}
              style={{ width: `${getTimePercentage()}%` }}
            />
          </div>

          {/* Status text */}
          <div className="mt-3 text-sm text-gray-600">
            {isCritical && <span className="font-semibold text-red-600">⚠️ Critical - Submit soon!</span>}
            {isWarning && !isCritical && <span className="font-semibold text-yellow-600">⏱️ Time running low</span>}
            {!isWarning && <span>Time remaining</span>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssessmentTimer;
