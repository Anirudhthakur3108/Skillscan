/**
 * AssessmentResults Page
 * Displays assessment results with score, feedback, and recommendations
 */

import React, { useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AssessmentResult } from '../types/assessment';

interface LocationState {
  result: AssessmentResult;
}

const AssessmentResults: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const result = (location.state as LocationState)?.result;

  // Redirect if no result
  if (!result) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">No Assessment Results</h1>
          <p className="text-gray-600 mb-6">Unable to find assessment results.</p>
          <button
            onClick={() => navigate('/assessment')}
            className="px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700"
          >
            Back to Assessments
          </button>
        </div>
      </div>
    );
  }

  // Calculate if passed
  const isPassed = result.percentage >= 70;

  // Get badge styling
  const getBadgeStyle = (): {
    bgColor: string;
    textColor: string;
    borderColor: string;
    emoji: string;
  } => {
    switch (result.badge) {
      case 'Excellent':
        return {
          bgColor: 'bg-green-50',
          textColor: 'text-green-900',
          borderColor: 'border-green-200',
          emoji: '⭐',
        };
      case 'Good':
        return {
          bgColor: 'bg-blue-50',
          textColor: 'text-blue-900',
          borderColor: 'border-blue-200',
          emoji: '✓',
        };
      case 'Fair':
        return {
          bgColor: 'bg-yellow-50',
          textColor: 'text-yellow-900',
          borderColor: 'border-yellow-200',
          emoji: '→',
        };
      case 'Needs Work':
        return {
          bgColor: 'bg-red-50',
          textColor: 'text-red-900',
          borderColor: 'border-red-200',
          emoji: '📚',
        };
      default:
        return {
          bgColor: 'bg-gray-50',
          textColor: 'text-gray-900',
          borderColor: 'border-gray-200',
          emoji: '→',
        };
    }
  };

  const badgeStyle = getBadgeStyle();

  // Format difficulty
  const formattedDifficulty =
    result.difficulty.charAt(0).toUpperCase() + result.difficulty.slice(1);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Assessment Complete! 🎉</h1>
          <p className="text-lg text-gray-600">Here's how you performed</p>
        </div>

        {/* Score Card */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          {/* Main score display */}
          <div className="text-center mb-8">
            <div className="inline-block">
              <div className="text-6xl font-bold text-blue-600 mb-2">
                {result.score}/{result.total_points}
              </div>
              <div className="text-2xl font-semibold text-gray-700">
                {result.percentage}%
              </div>
            </div>
          </div>

          {/* Pass/Fail message */}
          {isPassed ? (
            <div className="mb-8 p-4 rounded-lg bg-green-50 border border-green-200 text-green-900 text-center font-semibold">
              ✅ Congratulations! You passed this assessment!
            </div>
          ) : (
            <div className="mb-8 p-4 rounded-lg bg-red-50 border border-red-200 text-red-900 text-center font-semibold">
              📚 Keep practicing! We recommend retaking this assessment after studying the
              resources below.
            </div>
          )}

          {/* Performance badge */}
          <div className={`mb-8 p-6 rounded-lg border-2 ${badgeStyle.bgColor} ${badgeStyle.textColor} ${badgeStyle.borderColor} text-center`}>
            <div className="text-4xl mb-2">{badgeStyle.emoji}</div>
            <div className="text-2xl font-bold">{result.badge}</div>
            <div className="text-sm mt-2">
              {result.difficulty && `${formattedDifficulty} Level`}
            </div>
          </div>

          {/* Assessment details */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg mb-8">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{result.percentage}%</div>
              <div className="text-xs text-gray-600 mt-1">Score</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-700">
                {result.assessment_type === 'mcq'
                  ? 'MCQ'
                  : result.assessment_type === 'coding'
                    ? 'Coding'
                    : 'Case Study'}
              </div>
              <div className="text-xs text-gray-600 mt-1">Type</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {formattedDifficulty}
              </div>
              <div className="text-xs text-gray-600 mt-1">Difficulty</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-teal-600">
                {new Date(result.submitted_at).toLocaleDateString()}
              </div>
              <div className="text-xs text-gray-600 mt-1">Date</div>
            </div>
          </div>
        </div>

        {/* Feedback Section */}
        {result.feedback && (
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">📝 Feedback</h2>
            <div className="p-4 bg-blue-50 border-l-4 border-blue-500 rounded text-gray-700">
              {result.feedback}
            </div>
          </div>
        )}

        {/* Areas to Improve */}
        {result.gaps && result.gaps.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">🎯 Areas to Improve</h2>
            <div className="space-y-2">
              {result.gaps.map((gap, index) => (
                <div
                  key={index}
                  className="p-3 bg-yellow-50 border border-yellow-200 rounded text-yellow-900"
                >
                  • {gap}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Wrong Answers */}
        {result.wrong_answers && result.wrong_answers.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              ❌ What You Got Wrong
            </h2>
            <div className="space-y-4">
              {result.wrong_answers.map((answer, index) => (
                <div
                  key={answer.question_id}
                  className="p-4 border border-red-200 rounded-lg bg-red-50"
                >
                  <div className="font-semibold text-gray-900 mb-2">
                    Question {index + 1}: {answer.question}
                  </div>
                  <div className="mb-2">
                    <span className="font-medium text-red-700">Your answer:</span>{' '}
                    <span className="text-gray-700">{answer.user_answer}</span>
                  </div>
                  <div className="mb-2">
                    <span className="font-medium text-green-700">Correct answer:</span>{' '}
                    <span className="text-gray-700">{answer.correct_answer}</span>
                  </div>
                  <div className="p-3 bg-blue-50 rounded">
                    <span className="font-medium text-gray-900">Explanation:</span>{' '}
                    <span className="text-gray-700">{answer.explanation}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {result.recommendations && result.recommendations.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              💡 Recommended Resources
            </h2>
            <div className="space-y-4">
              {result.recommendations.slice(0, 3).map((rec, index) => (
                <div
                  key={rec.id}
                  className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">
                        {index + 1}. {rec.title}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                    </div>
                    <span className="text-xs bg-gray-100 text-gray-700 px-3 py-1 rounded ml-4 flex-shrink-0">
                      {rec.type}
                    </span>
                  </div>
                  {rec.duration && (
                    <div className="text-xs text-gray-600">⏱️ {rec.duration}</div>
                  )}
                  {rec.url && (
                    <a
                      href={rec.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium mt-2 inline-block"
                    >
                      View Resource →
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">What's Next?</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Retake button */}
            <button
              onClick={() => navigate('/assessment')}
              className="px-6 py-3 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
            >
              🔄 Retake Assessment
            </button>

            {/* Next difficulty button (only if passed) */}
            {isPassed && result.difficulty !== 'hard' && (
              <button
                onClick={() => navigate('/assessment')}
                className="px-6 py-3 rounded-lg bg-green-600 text-white font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
              >
                ⬆️ Try Next Difficulty
              </button>
            )}

            {/* Back to profile button */}
            <button
              onClick={() => navigate('/profile')}
              className="px-6 py-3 rounded-lg bg-gray-600 text-white font-medium hover:bg-gray-700 transition-colors flex items-center justify-center gap-2"
            >
              ← Back to Profile
            </button>

            {/* Learning plan button */}
            <button
              onClick={() => navigate('/learning-plan')}
              className="px-6 py-3 rounded-lg border-2 border-blue-600 text-blue-600 font-medium hover:bg-blue-50 transition-colors flex items-center justify-center gap-2"
            >
              📚 View Learning Plan
            </button>
          </div>
        </div>

        {/* Footer message */}
        <div className="mt-8 text-center">
          <p className="text-gray-600">
            Need help? Contact us at{' '}
            <a
              href="mailto:support@skillscan.com"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              support@skillscan.com
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default AssessmentResults;
