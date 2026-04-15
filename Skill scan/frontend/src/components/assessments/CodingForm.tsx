/**
 * CodingForm Component
 * Coding problem assessment form with code editor and test cases
 */

import React, { useState, useCallback, useRef } from 'react';
import { CodingResponse, TestResult } from '../../types/assessment';
import { AssessmentFormProps, Assessment } from '../../types/assessment';
import AssessmentTimer from './AssessmentTimer';
import ProgressBar from './ProgressBar';

interface CodingFormState {
  currentProblemIndex: number;
  solutions: Map<string, string>;
  testResults: Map<string, TestResult[]>;
  timeStarted: number;
}

interface LineNumbersProps {
  lines: number;
}

const LineNumbers: React.FC<LineNumbersProps> = ({ lines }) => {
  return (
    <div className="flex flex-col bg-gray-100 text-gray-600 text-sm font-mono select-none">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="h-6 px-3 py-1 text-right">
          {i + 1}
        </div>
      ))}
    </div>
  );
};

const CodingForm: React.FC<AssessmentFormProps> = ({
  assessment,
  onSubmit,
  isSubmitting = false,
}) => {
  const [formState, setFormState] = useState<CodingFormState>({
    currentProblemIndex: 0,
    solutions: new Map(),
    testResults: new Map(),
    timeStarted: Date.now(),
  });

  const [hasTimeExpired, setHasTimeExpired] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isAutoSubmitting, setIsAutoSubmitting] = useState(false);
  const [runningTests, setRunningTests] = useState(false);
  const editorRef = useRef<HTMLTextAreaElement>(null);

  const problems = assessment.problems || [];
  const currentProblem = problems[formState.currentProblemIndex];
  const totalProblems = problems.length;

  // Handle time expiration
  const handleTimeExpire = useCallback(async () => {
    setHasTimeExpired(true);
    setIsAutoSubmitting(true);

    // Auto-submit with current solutions
    try {
      const responses: CodingResponse[] = Array.from(formState.solutions.entries()).map(
        ([problemId, code]) => ({
          problem_id: problemId,
          code,
          language: 'python',
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

  // Update code
  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const code = e.target.value;
    setFormState((prev) => ({
      ...prev,
      solutions: new Map(prev.solutions).set(currentProblem.id, code),
    }));
    setSubmitError(null);
  };

  // Run test cases (mock for MVP)
  const handleRunTests = async () => {
    setRunningTests(true);
    const currentCode = formState.solutions.get(currentProblem.id) || '';

    try {
      // Mock test results - in production, this would call backend
      if (!currentProblem.test_cases) {
        setSubmitError('No test cases available');
        setRunningTests(false);
        return;
      }

      // Simulate test execution delay
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const mockResults: TestResult[] = currentProblem.test_cases.map((testCase) => ({
        test_case_id: testCase.id,
        passed: currentCode.includes('def') || currentCode.includes('function'),
        expected_output: testCase.expected_output,
        actual_output: currentCode.length > 10 ? testCase.expected_output : 'Error',
      }));

      setFormState((prev) => ({
        ...prev,
        testResults: new Map(prev.testResults).set(currentProblem.id, mockResults),
      }));
    } catch (error) {
      console.error('Test execution failed:', error);
      setSubmitError('Failed to run tests');
    } finally {
      setRunningTests(false);
    }
  };

  // Navigate to next problem
  const handleNext = () => {
    if (formState.currentProblemIndex < totalProblems - 1) {
      setFormState((prev) => ({
        ...prev,
        currentProblemIndex: prev.currentProblemIndex + 1,
      }));
    }
  };

  // Navigate to previous problem
  const handlePrevious = () => {
    if (formState.currentProblemIndex > 0) {
      setFormState((prev) => ({
        ...prev,
        currentProblemIndex: prev.currentProblemIndex - 1,
      }));
    }
  };

  // Jump to specific problem
  const handleJumpToProblem = (index: number) => {
    setFormState((prev) => ({
      ...prev,
      currentProblemIndex: index,
    }));
  };

  // Submit form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formState.solutions.size === 0) {
      setSubmitError('Please write code for at least one problem');
      return;
    }

    setSubmitError(null);

    try {
      const responses: CodingResponse[] = Array.from(formState.solutions.entries()).map(
        ([problemId, code]) => ({
          problem_id: problemId,
          code,
          language: 'python',
          test_results: formState.testResults.get(problemId),
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

  if (!currentProblem) {
    return <div className="text-center py-8">No problems available</div>;
  }

  const currentCode = formState.solutions.get(currentProblem.id) || '';
  const currentTests = formState.testResults.get(currentProblem.id);
  const codeLines = currentCode.split('\n').length;

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-4xl mx-auto">
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
          current={formState.currentProblemIndex + 1}
          total={totalProblems}
          showLabel={true}
        />
      </div>

      {/* Problem counter */}
      <div className="mb-4 text-sm text-gray-600 font-medium">
        Problem {formState.currentProblemIndex + 1} of {totalProblems}
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
          Time expired! Auto-submitting your solutions...
        </div>
      )}

      {/* Problem container */}
      <div className="mb-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Problem description */}
        <div className="p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">{currentProblem.title}</h3>
          <p className="text-gray-700 mb-4 whitespace-pre-wrap">{currentProblem.description}</p>

          {/* Starter code if available */}
          {currentProblem.starter_code && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Starter Code:</h4>
              <pre className="p-3 bg-gray-900 text-gray-100 rounded text-xs overflow-x-auto">
                {currentProblem.starter_code}
              </pre>
            </div>
          )}

          {/* Test cases */}
          {currentProblem.test_cases && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Test Cases:</h4>
              <div className="space-y-2">
                {currentProblem.test_cases.map((testCase, index) => (
                  <div key={testCase.id} className="p-3 bg-gray-50 rounded border border-gray-200 text-xs">
                    <div className="font-semibold text-gray-900 mb-1">Test {index + 1}: {testCase.description}</div>
                    <div className="text-gray-700 mb-1">
                      <span className="font-medium">Input:</span> {testCase.input}
                    </div>
                    <div className="text-gray-700">
                      <span className="font-medium">Expected:</span> {testCase.expected_output}
                    </div>

                    {/* Test result if available */}
                    {currentTests && currentTests[index] && (
                      <div className={`mt-2 p-2 rounded ${
                        currentTests[index].passed
                          ? 'bg-green-50 border border-green-200 text-green-800'
                          : 'bg-red-50 border border-red-200 text-red-800'
                      }`}>
                        {currentTests[index].passed ? '✅ Passed' : '❌ Failed'}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Code editor */}
        <div className="flex flex-col">
          <div className="flex-1 bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            <div className="flex h-full">
              {/* Line numbers */}
              <LineNumbers lines={codeLines} />

              {/* Code editor */}
              <textarea
                ref={editorRef}
                value={currentCode}
                onChange={handleCodeChange}
                disabled={isSubmitting || isAutoSubmitting || hasTimeExpired}
                placeholder="Write your code here..."
                className="flex-1 p-3 font-mono text-sm resize-none focus:outline-none focus:ring-0 bg-gray-900 text-gray-100"
                style={{ lineHeight: '1.5rem' }}
              />
            </div>
          </div>

          {/* Editor actions */}
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              onClick={handleRunTests}
              disabled={!currentCode || isSubmitting || isAutoSubmitting || runningTests || hasTimeExpired}
              className="flex-1 px-4 py-2 rounded-lg bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {runningTests ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Running Tests...
                </>
              ) : (
                <>▶ Run Tests</>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Problem indicators */}
      <div className="mb-6 p-4 rounded-lg bg-gray-50 border border-gray-200">
        <div className="text-sm font-medium text-gray-700 mb-3">Problem Status:</div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {problems.map((p, index) => (
            <button
              key={p.id}
              onClick={() => handleJumpToProblem(index)}
              type="button"
              disabled={isSubmitting || isAutoSubmitting || hasTimeExpired}
              className={`w-full py-2 rounded font-semibold text-sm transition-all ${
                index === formState.currentProblemIndex
                  ? 'bg-blue-500 text-white'
                  : formState.solutions.has(p.id)
                    ? 'bg-green-500 text-white hover:bg-green-600'
                    : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
              }`}
              title={
                formState.solutions.has(p.id) ? `Problem ${index + 1} (started)` : `Problem ${index + 1}`
              }
            >
              {index + 1}
            </button>
          ))}
        </div>
      </div>

      {/* Navigation buttons */}
      <div className="flex gap-3 justify-between">
        <button
          type="button"
          onClick={handlePrevious}
          disabled={
            formState.currentProblemIndex === 0 ||
            isSubmitting ||
            isAutoSubmitting ||
            hasTimeExpired
          }
          className="px-6 py-2 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          ← Previous
        </button>

        {formState.currentProblemIndex < totalProblems - 1 ? (
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
              formState.solutions.size === 0
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

export default CodingForm;
