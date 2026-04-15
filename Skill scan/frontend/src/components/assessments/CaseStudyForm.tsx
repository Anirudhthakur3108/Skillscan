/**
 * CaseStudyForm Component
 * Case study scenario assessment form with text responses
 */

import React, { useState, useCallback } from 'react';
import { CaseStudyResponse } from '../../types/assessment';
import { AssessmentFormProps, Assessment } from '../../types/assessment';
import AssessmentTimer from './AssessmentTimer';
import ProgressBar from './ProgressBar';

interface CaseStudyFormState {
  currentScenarioIndex: number;
  responses: Map<string, string[]>;
  timeStarted: number;
}

const CaseStudyForm: React.FC<AssessmentFormProps> = ({
  assessment,
  onSubmit,
  isSubmitting = false,
}) => {
  const [formState, setFormState] = useState<CaseStudyFormState>({
    currentScenarioIndex: 0,
    responses: new Map(),
    timeStarted: Date.now(),
  });

  const [hasTimeExpired, setHasTimeExpired] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isAutoSubmitting, setIsAutoSubmitting] = useState(false);

  const scenarios = assessment.scenarios || [];
  const currentScenario = scenarios[formState.currentScenarioIndex];
  const totalScenarios = scenarios.length;

  // Handle time expiration
  const handleTimeExpire = useCallback(async () => {
    setHasTimeExpired(true);
    setIsAutoSubmitting(true);

    // Auto-submit with current responses
    try {
      const responses: CaseStudyResponse[] = Array.from(formState.responses.entries()).map(
        ([scenarioId, scenarioResponses]) => ({
          scenario_id: scenarioId,
          responses: scenarioResponses.map((response, index) => ({
            question_index: index,
            response,
          })),
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

  // Update response for a specific question in current scenario
  const handleResponseChange = (
    questionIndex: number,
    e: React.ChangeEvent<HTMLTextAreaElement>
  ) => {
    const responseText = e.target.value;
    setFormState((prev) => {
      const scenarioResponses = prev.responses.get(currentScenario.id) || [];
      const updatedResponses = [...scenarioResponses];
      updatedResponses[questionIndex] = responseText;
      return {
        ...prev,
        responses: new Map(prev.responses).set(currentScenario.id, updatedResponses),
      };
    });
    setSubmitError(null);
  };

  // Get word count for a response
  const getWordCount = (text: string): number => {
    return text
      .trim()
      .split(/\s+/)
      .filter((word) => word.length > 0).length;
  };

  // Navigate to next scenario
  const handleNext = () => {
    if (formState.currentScenarioIndex < totalScenarios - 1) {
      setFormState((prev) => ({
        ...prev,
        currentScenarioIndex: prev.currentScenarioIndex + 1,
      }));
    }
  };

  // Navigate to previous scenario
  const handlePrevious = () => {
    if (formState.currentScenarioIndex > 0) {
      setFormState((prev) => ({
        ...prev,
        currentScenarioIndex: prev.currentScenarioIndex - 1,
      }));
    }
  };

  // Jump to specific scenario
  const handleJumpToScenario = (index: number) => {
    setFormState((prev) => ({
      ...prev,
      currentScenarioIndex: index,
    }));
  };

  // Submit form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formState.responses.size === 0) {
      setSubmitError('Please provide responses to at least one scenario');
      return;
    }

    // Check if all questions in the last scenario are answered
    const currentResponses = formState.responses.get(currentScenario.id) || [];
    if (currentResponses.some((r) => !r || r.trim().length === 0)) {
      setSubmitError('Please answer all questions in the current scenario');
      return;
    }

    setSubmitError(null);

    try {
      const responses: CaseStudyResponse[] = Array.from(formState.responses.entries()).map(
        ([scenarioId, scenarioResponses]) => ({
          scenario_id: scenarioId,
          responses: scenarioResponses.map((response, index) => ({
            question_index: index,
            response,
          })),
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

  if (!currentScenario) {
    return <div className="text-center py-8">No scenarios available</div>;
  }

  const currentResponses = formState.responses.get(currentScenario.id) || [];

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
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
          current={formState.currentScenarioIndex + 1}
          total={totalScenarios}
          showLabel={true}
        />
      </div>

      {/* Scenario counter */}
      <div className="mb-4 text-sm text-gray-600 font-medium">
        Scenario {formState.currentScenarioIndex + 1} of {totalScenarios}
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
          Time expired! Auto-submitting your responses...
        </div>
      )}

      {/* Scenario container */}
      <div className="mb-6 p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
        {/* Scenario title */}
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{currentScenario.title}</h3>

        {/* Scenario description */}
        <div className="mb-6 p-4 bg-gray-50 rounded border border-gray-200">
          <p className="text-gray-700 whitespace-pre-wrap mb-3">{currentScenario.description}</p>
          {currentScenario.context && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-900">
              <span className="font-semibold">Context:</span> {currentScenario.context}
            </div>
          )}
        </div>

        {/* Questions and responses */}
        <div className="space-y-6">
          {currentScenario.questions.map((question, qIndex) => {
            const response = currentResponses[qIndex] || '';
            const wordCount = getWordCount(response);

            return (
              <div key={qIndex} className="border-b border-gray-200 pb-6 last:border-b-0">
                {/* Question number and text */}
                <h4 className="text-md font-semibold text-gray-900 mb-3">
                  Question {qIndex + 1}: {question}
                </h4>

                {/* Response textarea */}
                <textarea
                  value={response}
                  onChange={(e) => handleResponseChange(qIndex, e)}
                  disabled={isSubmitting || isAutoSubmitting || hasTimeExpired}
                  placeholder="Type your response here... (minimum 50 words recommended)"
                  className="w-full h-32 p-4 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 resize-none transition-colors focus:outline-none disabled:bg-gray-100 disabled:cursor-not-allowed"
                />

                {/* Word count */}
                <div className="mt-2 flex items-center justify-between text-xs text-gray-600">
                  <span>Word count: {wordCount}</span>
                  {wordCount < 50 && wordCount > 0 && (
                    <span className="text-yellow-600 font-medium">⚠️ Aim for at least 50 words</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Scenario indicators */}
      <div className="mb-6 p-4 rounded-lg bg-gray-50 border border-gray-200">
        <div className="text-sm font-medium text-gray-700 mb-3">Scenario Status:</div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {scenarios.map((s, index) => {
            const scenarioResponses = formState.responses.get(s.id) || [];
            const isAnswered =
              scenarioResponses.length > 0 &&
              scenarioResponses.some((r) => r && r.trim().length > 0);

            return (
              <button
                key={s.id}
                onClick={() => handleJumpToScenario(index)}
                type="button"
                disabled={isSubmitting || isAutoSubmitting || hasTimeExpired}
                className={`w-full py-2 rounded font-semibold text-sm transition-all ${
                  index === formState.currentScenarioIndex
                    ? 'bg-blue-500 text-white'
                    : isAnswered
                      ? 'bg-green-500 text-white hover:bg-green-600'
                      : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
                }`}
                title={
                  isAnswered ? `Scenario ${index + 1} (started)` : `Scenario ${index + 1}`
                }
              >
                {index + 1}
              </button>
            );
          })}
        </div>
      </div>

      {/* Summary of responses */}
      <div className="mb-6 p-4 rounded-lg bg-blue-50 border border-blue-200 text-blue-900 text-sm">
        <span className="font-semibold">Progress:</span> {formState.responses.size} of{' '}
        {totalScenarios} scenarios started
      </div>

      {/* Navigation buttons */}
      <div className="flex gap-3 justify-between">
        <button
          type="button"
          onClick={handlePrevious}
          disabled={
            formState.currentScenarioIndex === 0 ||
            isSubmitting ||
            isAutoSubmitting ||
            hasTimeExpired
          }
          className="px-6 py-2 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          ← Previous
        </button>

        {formState.currentScenarioIndex < totalScenarios - 1 ? (
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
              formState.responses.size === 0
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
    </form>
  );
};

export default CaseStudyForm;
