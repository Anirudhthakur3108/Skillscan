/**
 * DifficultySelector Component
 * Displays Easy, Medium, Hard difficulty levels with unlock logic
 */

import React, { useEffect, useState } from 'react';
import { DifficultyLevel, AssessmentProgress } from '../../types/assessment';
import { assessmentAPI } from '../../api/assessments';
import { DifficultySelectorProps } from '../../types/assessment';

const DifficultySelector: React.FC<DifficultySelectorProps> = ({
  skillId,
  selectedDifficulty,
  onSelect,
  isLoading = false,
}) => {
  const [progress, setProgress] = useState<AssessmentProgress | null>(null);
  const [loadingProgress, setLoadingProgress] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch progress on mount
  useEffect(() => {
    const fetchProgress = async () => {
      try {
        setLoadingProgress(true);
        const data = await assessmentAPI.getAssessmentProgress(skillId);
        setProgress(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch progress:', err);
        setError('Failed to load progress');
        // Set default progress on error
        setProgress({
          skill_id: skillId,
          easy: { completed: false, attempts: 0 },
          medium: { completed: false, attempts: 0 },
          hard: { completed: false, attempts: 0 },
        });
      } finally {
        setLoadingProgress(false);
      }
    };

    fetchProgress();
  }, [skillId]);

  // Determine if a difficulty level is unlocked
  const isUnlocked = (difficulty: DifficultyLevel): boolean => {
    if (!progress) return difficulty === 'easy';

    if (difficulty === 'easy') return true;
    if (difficulty === 'medium') {
      return progress.easy.completed && (progress.easy.score || 0) >= 70;
    }
    if (difficulty === 'hard') {
      return progress.medium.completed && (progress.medium.score || 0) >= 70;
    }
    return false;
  };

  // Get unlock message
  const getUnlockMessage = (difficulty: DifficultyLevel): string => {
    if (difficulty === 'medium') {
      return 'Pass Easy (70%+) to unlock';
    }
    if (difficulty === 'hard') {
      return 'Pass Medium (70%+) to unlock';
    }
    return '';
  };

  // Get score if completed
  const getScore = (difficulty: DifficultyLevel): number | null => {
    if (!progress) return null;

    if (difficulty === 'easy' && progress.easy.completed) {
      return progress.easy.score || null;
    }
    if (difficulty === 'medium' && progress.medium.completed) {
      return progress.medium.score || null;
    }
    if (difficulty === 'hard' && progress.hard.completed) {
      return progress.hard.score || null;
    }
    return null;
  };

  // Get attempts if any
  const getAttempts = (difficulty: DifficultyLevel): number => {
    if (!progress) return 0;

    if (difficulty === 'easy') return progress.easy.attempts;
    if (difficulty === 'medium') return progress.medium.attempts;
    if (difficulty === 'hard') return progress.hard.attempts;
    return 0;
  };

  // Check if completed
  const isCompleted = (difficulty: DifficultyLevel): boolean => {
    if (!progress) return false;

    if (difficulty === 'easy') return progress.easy.completed;
    if (difficulty === 'medium') return progress.medium.completed;
    if (difficulty === 'hard') return progress.hard.completed;
    return false;
  };

  const difficulties: DifficultyLevel[] = ['easy', 'medium', 'hard'];

  return (
    <div className="w-full">
      {/* Error message */}
      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm">
          {error}
        </div>
      )}

      {/* Difficulty selector grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {difficulties.map((difficulty) => {
          const unlocked = isUnlocked(difficulty);
          const completed = isCompleted(difficulty);
          const score = getScore(difficulty);
          const attempts = getAttempts(difficulty);

          return (
            <button
              key={difficulty}
              onClick={() => unlocked && onSelect(difficulty)}
              disabled={!unlocked || isLoading || loadingProgress}
              className={`relative p-6 rounded-lg border-2 transition-all duration-300 ${
                !unlocked
                  ? 'border-gray-300 bg-gray-100 cursor-not-allowed opacity-60'
                  : selectedDifficulty === difficulty
                    ? 'border-blue-500 bg-blue-50 shadow-lg'
                    : 'border-gray-300 bg-white hover:border-blue-400 hover:shadow-md'
              }`}
            >
              {/* Difficulty name */}
              <div className="text-lg font-bold capitalize text-gray-900 mb-2">
                {difficulty}
              </div>

              {/* Status indicators */}
              <div className="space-y-2">
                {/* Lock icon for locked levels */}
                {!unlocked && (
                  <div className="flex items-center text-gray-600 text-sm">
                    <span className="mr-2">🔒</span>
                    <span>{getUnlockMessage(difficulty)}</span>
                  </div>
                )}

                {/* Completed checkmark */}
                {unlocked && completed && (
                  <div className="flex items-center text-green-600 text-sm font-semibold">
                    <span className="mr-2">✅</span>
                    <span>Completed</span>
                  </div>
                )}

                {/* Score if completed */}
                {unlocked && completed && score !== null && (
                  <div className="text-sm text-gray-700">
                    <span className="font-semibold">Best Score:</span> {score}%
                  </div>
                )}

                {/* Attempts count */}
                {unlocked && attempts > 0 && (
                  <div className="text-xs text-gray-600">
                    {attempts} attempt{attempts !== 1 ? 's' : ''}
                  </div>
                )}

                {/* Not attempted yet */}
                {unlocked && !completed && (
                  <div className="text-sm text-gray-600">Not attempted yet</div>
                )}
              </div>

              {/* Selected indicator */}
              {selectedDifficulty === difficulty && (
                <div className="absolute top-3 right-3 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs font-bold">✓</span>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Loading state */}
      {loadingProgress && (
        <div className="mt-4 p-4 rounded-lg bg-blue-50 border border-blue-200 text-blue-800 text-sm">
          Loading difficulty progress...
        </div>
      )}

      {/* Info message */}
      {!loadingProgress && (
        <div className="mt-4 p-4 rounded-lg bg-blue-50 border border-blue-200 text-blue-800 text-sm">
          <p className="font-semibold mb-1">💡 Tip:</p>
          <p>
            Score 70% or higher to unlock the next difficulty level. Retakes are unlimited!
          </p>
        </div>
      )}
    </div>
  );
};

export default DifficultySelector;
