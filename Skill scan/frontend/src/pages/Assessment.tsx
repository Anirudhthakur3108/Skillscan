/**
 * Assessment Page
 * Main assessment interface with skill, difficulty, and assessment type selection
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Assessment, AssessmentType, DifficultyLevel, AssessmentSubmission, AssessmentResult } from '../types/assessment';
import { assessmentAPI } from '../api/assessments';
import DifficultySelector from '../components/assessments/DifficultySelector';
import MCQForm from '../components/assessments/MCQForm';
import CodingForm from '../components/assessments/CodingForm';
import CaseStudyForm from '../components/assessments/CaseStudyForm';

type AssessmentStage = 'selection' | 'instructions' | 'in-progress' | 'submitted';

interface AssessmentState {
  stage: AssessmentStage;
  selectedSkillId: number | null;
  selectedDifficulty: DifficultyLevel | null;
  selectedAssessmentType: AssessmentType | null;
  assessment: Assessment | null;
  isLoading: boolean;
  error: string | null;
  isSubmitting: boolean;
}

const Assessment: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [state, setState] = useState<AssessmentState>({
    stage: 'selection',
    selectedSkillId: location.state?.skillId || null,
    selectedDifficulty: null,
    selectedAssessmentType: null,
    assessment: null,
    isLoading: false,
    error: null,
    isSubmitting: false,
  });

  // Mock skills data (in production, fetch from API)
  const skills = [
    { id: 1, name: 'Database Design', category: 'Analytics' },
    { id: 2, name: 'SQL Optimization', category: 'Analytics' },
    { id: 3, name: 'Data Analysis', category: 'Analytics' },
    { id: 4, name: 'Python Basics', category: 'BCA' },
    { id: 5, name: 'Web Development', category: 'BCA' },
  ];

  const assessmentTypes: { type: AssessmentType; label: string; description: string; timeLimit: number }[] = [
    {
      type: 'mcq',
      label: 'Multiple Choice Questions',
      description: 'Test your knowledge with timed multiple choice questions',
      timeLimit: 360,
    },
    {
      type: 'coding',
      label: 'Coding Problems',
      description: 'Write code to solve programming problems',
      timeLimit: 3600,
    },
    {
      type: 'casestudy',
      label: 'Case Study Analysis',
      description: 'Analyze real-world scenarios and provide detailed responses',
      timeLimit: 1800,
    },
  ];

  // Start assessment
  const handleStartAssessment = async () => {
    if (!state.selectedSkillId || !state.selectedDifficulty || !state.selectedAssessmentType) {
      setState((prev) => ({
        ...prev,
        error: 'Please select skill, difficulty, and assessment type',
      }));
      return;
    }

    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const assessment = await assessmentAPI.generateAssessment(
        state.selectedSkillId,
        state.selectedDifficulty,
        state.selectedAssessmentType
      );

      setState((prev) => ({
        ...prev,
        assessment,
        stage: 'in-progress',
        isLoading: false,
      }));
    } catch (error) {
      console.error('Failed to start assessment:', error);
      setState((prev) => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to load assessment',
        isLoading: false,
      }));
    }
  };

  // Submit assessment
  const handleSubmitAssessment = async (submission: AssessmentSubmission) => {
    setState((prev) => ({
      ...prev,
      isSubmitting: true,
      error: null,
    }));

    try {
      const result = await assessmentAPI.submitAssessment(submission);

      // Navigate to results page
      navigate('/assessment-results', {
        state: { result },
        replace: true,
      });
    } catch (error) {
      console.error('Failed to submit assessment:', error);
      setState((prev) => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to submit assessment',
        isSubmitting: false,
      }));
    }
  };

  // Reset and go back to selection
  const handleReset = () => {
    setState({
      stage: 'selection',
      selectedSkillId: null,
      selectedDifficulty: null,
      selectedAssessmentType: null,
      assessment: null,
      isLoading: false,
      error: null,
      isSubmitting: false,
    });
  };

  const selectedSkill = skills.find((s) => s.id === state.selectedSkillId);
  const selectedAssessmentInfo = assessmentTypes.find(
    (a) => a.type === state.selectedAssessmentType
  );

  // If assessment is in progress, render the appropriate form
  if (state.stage === 'in-progress' && state.assessment) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <button
              onClick={handleReset}
              className="mb-4 px-4 py-2 rounded-lg text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 transition-colors"
            >
              ← Back to Selection
            </button>
            <h1 className="text-3xl font-bold text-gray-900">
              {selectedSkill?.name} - {state.selectedDifficulty?.charAt(0).toUpperCase()}{state.selectedDifficulty?.slice(1)} Assessment
            </h1>
            <p className="text-gray-600 mt-2">{selectedAssessmentInfo?.description}</p>
          </div>

          {/* Error message */}
          {state.error && (
            <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-800">
              {state.error}
              <button
                onClick={() => handleStartAssessment()}
                className="ml-4 px-4 py-1 rounded bg-red-600 text-white text-sm hover:bg-red-700"
              >
                Retry
              </button>
            </div>
          )}

          {/* Assessment form */}
          {state.selectedAssessmentType === 'mcq' && (
            <MCQForm
              assessment={state.assessment}
              onSubmit={handleSubmitAssessment}
              onTimeout={() => {}}
              isSubmitting={state.isSubmitting}
            />
          )}

          {state.selectedAssessmentType === 'coding' && (
            <CodingForm
              assessment={state.assessment}
              onSubmit={handleSubmitAssessment}
              onTimeout={() => {}}
              isSubmitting={state.isSubmitting}
            />
          )}

          {state.selectedAssessmentType === 'casestudy' && (
            <CaseStudyForm
              assessment={state.assessment}
              onSubmit={handleSubmitAssessment}
              onTimeout={() => {}}
              isSubmitting={state.isSubmitting}
            />
          )}
        </div>
      </div>
    );
  }

  // Selection stage
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Assessment Center</h1>
          <p className="text-xl text-gray-600">
            Select a skill and take an assessment to verify your knowledge
          </p>
        </div>

        {/* Error message */}
        {state.error && (
          <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-800">
            {state.error}
          </div>
        )}

        {/* Main selection card */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Step 1: Skill Selection */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">1. Select a Skill</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {skills.map((skill) => (
                <button
                  key={skill.id}
                  onClick={() =>
                    setState((prev) => ({
                      ...prev,
                      selectedSkillId: skill.id,
                      selectedDifficulty: null,
                      selectedAssessmentType: null,
                      error: null,
                    }))
                  }
                  className={`p-4 rounded-lg border-2 transition-all text-left ${
                    state.selectedSkillId === skill.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-blue-300'
                  }`}
                >
                  <div className="font-semibold text-gray-900">{skill.name}</div>
                  <div className="text-sm text-gray-600">{skill.category}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Step 2: Difficulty Selection */}
          {state.selectedSkillId && (
            <div className="mb-8 pb-8 border-b border-gray-200">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">2. Select Difficulty Level</h2>
              <DifficultySelector
                skillId={state.selectedSkillId}
                selectedDifficulty={state.selectedDifficulty}
                onSelect={(difficulty) =>
                  setState((prev) => ({
                    ...prev,
                    selectedDifficulty: difficulty,
                    error: null,
                  }))
                }
                isLoading={state.isLoading}
              />
            </div>
          )}

          {/* Step 3: Assessment Type Selection */}
          {state.selectedSkillId && state.selectedDifficulty && (
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">3. Select Assessment Type</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {assessmentTypes.map((aType) => (
                  <button
                    key={aType.type}
                    onClick={() =>
                      setState((prev) => ({
                        ...prev,
                        selectedAssessmentType: aType.type,
                        error: null,
                      }))
                    }
                    className={`p-6 rounded-lg border-2 transition-all text-left ${
                      state.selectedAssessmentType === aType.type
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 bg-white hover:border-blue-300'
                    }`}
                  >
                    <div className="font-semibold text-gray-900 mb-2">{aType.label}</div>
                    <p className="text-sm text-gray-600 mb-3">{aType.description}</p>
                    <div className="text-xs bg-gray-100 text-gray-700 px-3 py-1 rounded w-fit">
                      ⏱️ {aType.timeLimit / 60} min{aType.timeLimit % 60 !== 0 ? 's' : ''}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Instructions and summary */}
          {state.selectedSkillId && state.selectedDifficulty && state.selectedAssessmentType && (
            <div className="mb-8 p-6 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-3">📋 Assessment Summary</h3>
              <ul className="space-y-2 text-gray-700">
                <li>
                  <span className="font-medium">Skill:</span> {selectedSkill?.name}
                </li>
                <li>
                  <span className="font-medium">Difficulty:</span>{' '}
                  {state.selectedDifficulty?.charAt(0).toUpperCase()}{state.selectedDifficulty?.slice(1)}
                </li>
                <li>
                  <span className="font-medium">Type:</span> {selectedAssessmentInfo?.label}
                </li>
                <li>
                  <span className="font-medium">Time Limit:</span>{' '}
                  {selectedAssessmentInfo?.timeLimit || 0} seconds
                </li>
                <li className="pt-2 border-t border-blue-200 text-sm">
                  ✓ You can retake this assessment unlimited times
                </li>
                <li className="text-sm">✓ Score of 70% or higher to unlock next difficulty</li>
              </ul>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-4 justify-end">
            <button
              onClick={handleReset}
              className="px-6 py-2 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
            >
              Reset
            </button>
            <button
              onClick={handleStartAssessment}
              disabled={
                !state.selectedSkillId ||
                !state.selectedDifficulty ||
                !state.selectedAssessmentType ||
                state.isLoading
              }
              className="px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {state.isLoading ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Loading Assessment...
                </>
              ) : (
                <>
                  ▶ Start Assessment
                </>
              )}
            </button>
          </div>
        </div>

        {/* Back button */}
        <div className="mt-8 text-center">
          <button
            onClick={() => navigate('/profile')}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            ← Back to Profile
          </button>
        </div>
      </div>
    </div>
  );
};

export default Assessment;
