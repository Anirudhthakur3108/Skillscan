/**
 * SkillScoreChart Component
 * Bar chart displaying skill scores with color coding and interactivity
 */

import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { SkillScore } from '../types/gap';

interface SkillScoreChartProps {
  skills: SkillScore[];
  onSkillClick: (skillId: number) => void;
}

const getScoreColor = (score: number): string => {
  if (score >= 90) return '#10b981'; // Green
  if (score >= 80) return '#3b82f6'; // Blue
  if (score >= 70) return '#eab308'; // Yellow
  return '#ef4444'; // Red
};

const getScoreLevelLabel = (score: number): string => {
  if (score >= 90) return 'Excellent';
  if (score >= 80) return 'Very Good';
  if (score >= 70) return 'Good';
  if (score >= 60) return 'Fair';
  return 'Needs Work';
};

const CustomTooltip: React.FC<any> = ({ active, payload }) => {
  if (active && payload && payload.length > 0) {
    const data = payload[0].payload;
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
        <p className="font-semibold text-gray-900">{data.skill_name}</p>
        <p className="text-sm text-gray-600">Score: {data.score}/100</p>
        <p className="text-xs text-gray-500">
          Level: {getScoreLevelLabel(data.score)}
        </p>
        {data.last_assessed && (
          <p className="mt-1 text-xs text-gray-500">
            Last: {new Date(data.last_assessed).toLocaleDateString()}
          </p>
        )}
        {data.trend && (
          <p className="mt-1 text-xs font-medium">
            {data.trend === 'up'
              ? '📈 Improving'
              : data.trend === 'down'
              ? '📉 Declining'
              : '➡️ Stable'}
          </p>
        )}
      </div>
    );
  }
  return null;
};

export const SkillScoreChart: React.FC<SkillScoreChartProps> = ({
  skills,
  onSkillClick,
}) => {
  const chartData = useMemo(
    () =>
      skills.map((skill) => ({
        ...skill,
        fill: getScoreColor(skill.score),
      })),
    [skills]
  );

  const handleBarClick = (data: any) => {
    onSkillClick(data.skill_id);
  };

  // Calculate statistics
  const avgScore = useMemo(() => {
    if (skills.length === 0) return 0;
    return Math.round(skills.reduce((sum, s) => sum + s.score, 0) / skills.length);
  }, [skills]);

  const excellentCount = useMemo(
    () => skills.filter((s) => s.score >= 90).length,
    [skills]
  );

  const needsWorkCount = useMemo(
    () => skills.filter((s) => s.score < 60).length,
    [skills]
  );

  if (skills.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <p className="text-gray-600">No skill data available. Complete an assessment to get started.</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Skill Assessment Scores</h3>
        <p className="mt-1 text-sm text-gray-600">
          {skills.length} skill{skills.length !== 1 ? 's' : ''} assessed
        </p>
      </div>

      {/* Summary Stats */}
      <div className="mb-6 grid grid-cols-3 gap-3">
        <div className="rounded-lg bg-green-50 p-4">
          <p className="text-sm text-gray-600">Average Score</p>
          <p className="mt-1 text-2xl font-bold text-green-700">{avgScore}%</p>
        </div>
        <div className="rounded-lg bg-blue-50 p-4">
          <p className="text-sm text-gray-600">Excellent (90+)</p>
          <p className="mt-1 text-2xl font-bold text-blue-700">{excellentCount}</p>
        </div>
        <div className="rounded-lg bg-red-50 p-4">
          <p className="text-sm text-gray-600">Needs Work (&lt;60)</p>
          <p className="mt-1 text-2xl font-bold text-red-700">{needsWorkCount}</p>
        </div>
      </div>

      {/* Chart */}
      <div className="mb-4">
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={chartData}
            margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            onClick={(state) => {
              if (state && state.activeTooltipIndex !== undefined) {
                handleBarClick(chartData[state.activeTooltipIndex]);
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="skill_name"
              angle={-45}
              textAnchor="end"
              height={100}
              tick={{ fontSize: 12 }}
            />
            <YAxis domain={[0, 100]} label={{ value: 'Score', angle: -90, position: 'insideLeft' }} />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              dataKey="score"
              fill="#8884d8"
              radius={[8, 8, 0, 0]}
              cursor="pointer"
              onClick={(data) => handleBarClick(data)}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="mt-6 flex flex-wrap gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded bg-green-500" />
          <span className="text-gray-700">Excellent (90+)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded bg-blue-500" />
          <span className="text-gray-700">Very Good (80-89)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded bg-yellow-500" />
          <span className="text-gray-700">Good (70-79)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded bg-red-500" />
          <span className="text-gray-700">Needs Work (&lt;70)</span>
        </div>
      </div>

      {/* Note */}
      <p className="mt-4 text-xs text-gray-500">
        💡 Click on any bar to view detailed gap analysis for that skill
      </p>
    </div>
  );
};
