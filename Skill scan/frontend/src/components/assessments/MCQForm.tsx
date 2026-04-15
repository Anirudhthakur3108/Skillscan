/**
 * MCQForm Component
 * Multiple choice question assessment form with timer and progress tracking
 */

import React, { useState, useCallback, useEffect } from 'react';
import { MCQResponse } from '../../types/assessment';
import { AssessmentFormProps, Assessment } from '../../types/assessment';
import AssessmentTimer from './AssessmentTimer';
import ProgressBar from './ProgressBar';

interface MCQFormState {
  currentQuestionIndex: number;
  answers: Map<string, string>;
  timeStarted: number;
}

const MCQForm: React.FC<AssessmentFormProps> = ({
  assessment,
  onSubmit,
  isSubmitting = false,
}) => {
  const [formState, setFormState] = useState<MCQFormState>({
    currentQuestionIndex: 0,
    answers: new Map(),
    timeStarted: Date.now(),
  });

  const [hasTimeExpired, setHasTimeExpired] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isAutoSubmitting, setIsAutoSubmitting] = useState(false);

  const questions = assessment.questions || [];
  const currentQuestion = questions[formState.currentQuestionIndex];
  const totalQuestions = questions.length;

  // Handle time expiration
  const handleTimeExpire = useCallback(async () => {
    setHasTimeExpired(true);
    setIsAutoSubmitting(true);

    // Auto-submit with current answers
    try {
      const responses: MCQResponse[] = Array.from(formState.answers.entries()).map(
        ([questionId, selectedOption]) => ({
          question_id: questionId,
          selected_option: selectedOption,
          time_spent: Date.now() - formState.timeStarted,
        })
      );

      await onSubmit({
        assessment_id: assessment.id,
        assessment_type: assessment.assessment_type,
        responses,
        time_spent: Date.now() - formState.timeStarted,
      });
    } catch (error) {
      console.error('Auto-submit failed:', error);
      setSubmitError('Failed to auto-submit. Please try again.');
    } finally {
      setIsAutoSubmitting(false);
    }
  }, [formState, assessment, onSubmit]);

  // Select an answer
  const handleSelectAnswer = (questionId: string, optionIndex: number) => {
    setFormState((prev) => ({
      ...prev,
      answers: new Map(prev.answers).set(questionId, String.fromCharCode(65 + optionIndex)), // A, B, C, D
    }));
    setSubmitError(null);
  };

  // Navigate to next question
  const handleNext = () => {
    if (formState.currentQuestionIndex < totalQuestions - 1) {
      setFormState((prev) => ({
        ...prev,
        currentQuestionIndex: prev.currentQuestionIndex + 1,
      }));
    }
  };

  // Navigate to previous question
  const handlePrevious = () => {
    if (formState.currentQuestionIndex > 0) {
      setFormState((prev) => ({
        ...prev,
        currentQuestionIndex: prev.currentQuestionIndex - 1,
      }));
    }
  };

  // Jump to specific question
  const handleJumpToQuestion = (index: number) => {
    setFormState((prev) => ({
      ...prev,
      currentQuestionIndex: index,
    }));
  };

  // Submit form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formState.answers.size === 0) {
      setSubmitError('Please answer at least one question');
      return;
    }

    setSubmitError(null);

    try {
      const responses: MCQResponse[] = Array.from(formState.answers.entries()).map(
        ([questionId, selectedOption]) => ({
          question_id: questionId,
          selected_option: selectedOption,
          time_spent: Date.now() - formState.timeStarted,
        })
      );

      await onSubmit({
        assessment_id: assessment.id,
        assessment_type: assessment.assessment_type,
        responses,
        time_spent: Date.now() - formState.timeStarted,
      });
    } catch (error) {
      console.error('Submit failed:', error);
      setSubmitError(
        error instanceof Error ? error.message : 'Failed to submit assessment'
      );
    }
  };

  if (!currentQuestion) {
    return <div className="text-center py-8">No questions available</div>;
  }

  const currentAnswer = formState.answers.get(currentQuestion.id);
  const answerLabels = ['A', 'B', 'C', 'D'];

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      {/* Timer */}
      <div className="mb-6">
        <AssessmentTimer
          totalSeconds={assessment.timer_seconds}
          onTimeExpire={handleTimeExpire}
          isPaused={hasTimeExpired || isAutoSubmitting}
        />
      </div>

      {/* Progress bar */}
      <div className="mb-6">
        <ProgressBar
          current={formState.currentQuestionIndex + 1}
          total={totalQuestions}
          showLabel={true}
        />
      </div>

      {/* Question counter */}
      <div className="mb-4 text-sm text-gray-600 font-medium">
        Question {formState.currentQuestionIndex + 1} of {totalQuestions}
      </div>

      {/* Error message */}
      {submitError && (
        <div className="mb-4 p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm">
          {submitError}
        </div>
      )}

      {/* Auto-submit message */}
      {isAutoSubmitting && (
        <div className="mb-4 p-4 rounded-lg bg-blue-50 border border-blue-200 text-blue-800 text-sm">
          Time expired! Auto-submitting your answers...
        </div>
      )}

      {/* Question container */}
      <div className="mb-6 p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
        {/* Question text */}
        <h3 className="text-lg font-semibold text-gray-900 mb-6">{currentQuestion.question}</h3>

        {/* Options */}
        <div className="space-y-3">
          {currentQuestion.options.map((option, index) => (
            <label
              key={index}
              className={`flex items-start p-4 rounded-lg border-2 cursor-pointer transition-all ${
                currentAnswer === answerLabels[index]
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-gray-50 hover:border-gray-300 hover:bg-white'
              }`}
            >
              <input
                type="radio"
                name={`question-${currentQuestion.id}`}
                value={answerLabels[index]}
                checked={currentAnswer === answerLabels[index]}
                onChange={() => handleSelectAnswer(currentQuestion.id, index)}
                disabled={isSubmitting || isAutoSubmitting || hasTimeExpired}
                className="mt-1 mr-4 w-5 h-5 text-blue-600 cursor-pointer"
              />
              <div className="flex-1">
                <div className="font-semibold text-gray-900">
                  {answerLabels[index]}. {option}
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Question indicators */}
      <div className="mb-6 p-4 rounded-lg bg-gray-50 border border-gray-200">
        <div className="text-sm font-medium text-gray-700 mb-3">Question Status:</div>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
          {questions.map((q, index) => (
            <button
              key={q.id}
              onClick={() => handleJumpToQuestion(index)}
              type="button"
              disabled={isSubmitting || isAutoSubmitting || hasTimeExpired}
              className={`w-full py-2 rounded font-semibold text-sm transition-all ${
                index === formState.currentQuestionIndex
                  ? 'bg-blue-500 text-white'
                  : formState.answers.has(q.id)
                    ? 'bg-green-500 text-white hover:bg-green-600'
                    : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
              }`}
              title={
                formState.answers.has(q.id) ? `Question ${index + 1} (answered)` : `Question ${index + 1}`
              }
            >
              {index + 1}
            </button>
          ))}
        </div>
      </div>

      {/* Navigation buttons */}
      <div className="mb-6 flex gap-3 justify-between">
        <button
          type="button"
          onClick={handlePrevious}
          disabled={
            formState.currentQuestionIndex === 0 ||
            isSubmitting ||
            isAutoSubmitting ||
            hasTimeExpired
          }
          className="px-6 py-2 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          ← Previous
        </button>

        {formState.currentQuestionIndex < totalQuestions - 1 ? (
          <button
            type="button"
            onClick={handleNext}
            disabled={isSubmitting || isAutoSubmitting || hasTimeExpired}
            className="px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Next →
          </button>
        ) : (
          <button
            type="submit"
            disabled={
              isSubmitting ||
              isAutoSubmitting ||
              hasTimeExpired ||
              formState.answers.size === 0
            }
            className="px-6 py-2 rounded-lg bg-green-600 text-white font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isSubmitting ? (
              <>
                <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Submitting...
              </>
            ) : (
              <>✓ Submit Assessment</>
            )}
          </button>
        )}
      </div>

      {/* Question counter info */}
      <div className="text-xs text-gray-600 text-center">
        Answered: {formState.answers.size} / {totalQuestions}
      </div>
    </form>
  );
};

export default MCQForm;
