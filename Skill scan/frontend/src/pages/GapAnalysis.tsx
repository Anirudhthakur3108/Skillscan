/**
 * GapAnalysis Page
 * Displays gap analysis for selected skill with benchmark comparison
 */

import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { GapAnalysis as GapAnalysisType, SkillScore } from '../types/gap';
import { getGapAnalysis, getBenchmarks } from '../api/gap';
import { GapCard } from '../components/GapCard';
import { GapAnalysisTable } from '../components/GapAnalysisTable';

interface SkillOption {
  id: number;
  name: string;
}

export const GapAnalysis: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [skills, setSkills] = useState<SkillOption[]>([]);
  const [selectedSkillId, setSelectedSkillId] = useState<number | null>(
    searchParams.get('skill_id') ? parseInt(searchParams.get('skill_id')!) : null
  );
  const [gapAnalysis, setGapAnalysis] = useState<GapAnalysisType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards');

  // Fetch available skills
  useEffect(() => {
    const fetchSkills = async () => {
      try {
        const response = await fetch(
          `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/skills`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
            },
          }
        );
        if (response.ok) {
          const data = await response.json();
          setSkills(data.data || []);
        }
      } catch (err) {
        console.error('Error fetching skills:', err);
      }
    };

    fetchSkills();
  }, []);

  // Fetch gap analysis when skill is selected
  useEffect(() => {
    if (!selectedSkillId) return;

    const fetchGapAnalysis = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getGapAnalysis(selectedSkillId);
        setGapAnalysis(data);
        setSearchParams({ skill_id: selectedSkillId.toString() });
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Failed to fetch gap analysis';
        setError(message);
        setGapAnalysis(null);
      } finally {
        setLoading(false);
      }
    };

    fetchGapAnalysis();
  }, [selectedSkillId, setSearchParams]);

  const handleSkillChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const skillId = parseInt(e.target.value);
    setSelectedSkillId(skillId || null);
  };

  const handleCreatePlan = (gapId: string) => {
    navigate(`/learning-plan?skill_id=${selectedSkillId}&gap_id=${gapId}`);
  };

  const handleViewDetails = (gapId: string) => {
    // Could navigate to detailed gap view
    console.log('View details for gap:', gapId);
  };

  const getScoreColor = (score: number): string => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-blue-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPercentileBadge = (percentile: number): string => {
    if (percentile >= 75) return 'bg-green-100 text-green-800';
    if (percentile >= 50) return 'bg-blue-100 text-blue-800';
    return 'bg-yellow-100 text-yellow-800';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Gap Analysis</h1>
          <p className="mt-2 text-gray-600">
            Identify skill gaps and create targeted learning plans
          </p>
        </div>

        {/* Skill Selector */}
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <label className="block text-sm font-medium text-gray-700">
            Select a Skill to Analyze
          </label>
          <select
            value={selectedSkillId || ''}
            onChange={handleSkillChange}
            className="mt-2 w-full max-w-md rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0"
          >
            <option value="">-- Choose a skill --</option>
            {skills.map((skill) => (
              <option key={skill.id} value={skill.id}>
                {skill.name}
              </option>
            ))}
          </select>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
            <button
              onClick={() => selectedSkillId && setSelectedSkillId(selectedSkillId)}
              className="mt-2 text-sm font-medium text-red-700 hover:text-red-800 underline"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
            <div className="inline-flex h-8 w-8 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
            <p className="mt-3 text-gray-600">Loading gap analysis...</p>
          </div>
        )}

        {/* Gap Analysis Results */}
        {gapAnalysis && !loading && (
          <>
            {/* Score Comparison Card */}
            <div className="mb-6 grid grid-cols-1 gap-6 md:grid-cols-3">
              {/* Current Score */}
              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <p className="text-sm font-medium text-gray-600">Your Score</p>
                <div className="mt-3 flex items-baseline gap-2">
                  <span
                    className={`text-3xl font-bold ${getScoreColor(
                      gapAnalysis.current_score
                    )}`}
                  >
                    {gapAnalysis.current_score}%
                  </span>
                  <span className="text-sm text-gray-500">/100</span>
                </div>
              </div>

              {/* Benchmark Score */}
              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <p className="text-sm font-medium text-gray-600">Industry Benchmark</p>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-3xl font-bold text-blue-600">
                    {gapAnalysis.benchmark_score}%
                  </span>
                  <span className="text-sm text-gray-500">/100</span>
                </div>
                <p className="mt-2 text-xs text-gray-600">
                  You are {Math.abs(gapAnalysis.current_score - gapAnalysis.benchmark_score)}%{' '}
                  {gapAnalysis.current_score >= gapAnalysis.benchmark_score
                    ? 'above'
                    : 'below'}{' '}
                  benchmark
                </p>
              </div>

              {/* Percentile */}
              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <p className="text-sm font-medium text-gray-600">Percentile Ranking</p>
                <div className="mt-3">
                  <span className={`inline-flex items-center rounded-full px-4 py-2 text-lg font-bold ${getPercentileBadge(gapAnalysis.percentile)}`}>
                    Top {100 - gapAnalysis.percentile}%
                  </span>
                </div>
                <p className="mt-2 text-xs text-gray-600">
                  You rank better than {gapAnalysis.percentile}% of users
                </p>
              </div>
            </div>

            {/* View Mode Toggle */}
            <div className="mb-4 flex items-center gap-2">
              <button
                onClick={() => setViewMode('cards')}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  viewMode === 'cards'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                Card View
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  viewMode === 'table'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                Table View
              </button>
            </div>

            {/* Gaps Section */}
            <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  Identified Gaps ({gapAnalysis.gaps.length})
                </h2>
                {gapAnalysis.weak_areas.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {gapAnalysis.weak_areas.map((area, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-800"
                      >
                        {area}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {viewMode === 'cards' ? (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {gapAnalysis.gaps.map((gap) => (
                    <GapCard
                      key={gap.id}
                      gap={gap}
                      onCreatePlan={handleCreatePlan}
                    />
                  ))}
                </div>
              ) : (
                <GapAnalysisTable
                  gaps={gapAnalysis.gaps}
                  onViewDetails={handleViewDetails}
                  onCreatePlan={handleCreatePlan}
                />
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => {
                  const link = document.createElement('a');
                  link.href = '#';
                  link.download = `gap-analysis-${gapAnalysis.skill_name}.pdf`;
                  link.click();
                }}
                className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2.5 text-sm font-medium text-gray-700 border border-gray-200 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                📄 Download Report
              </button>
              <button
                onClick={() => navigate('/dashboard')}
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                ← Back to Dashboard
              </button>
            </div>
          </>
        )}

        {/* Empty State */}
        {!selectedSkillId && !loading && (
          <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
            <p className="text-gray-600">
              Select a skill above to view gap analysis
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
