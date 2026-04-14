import React from 'react';
import axios from 'axios';
import Button from '../ui/Button';

interface Skill {
  id: number;
  name: string;
  proficiency_claimed: number;
  source: string;
  confidence?: number;
}

interface SkillCardProps {
  skill: Skill;
  onRemove?: (skillId: number) => void;
}

const SkillCard: React.FC<SkillCardProps> = ({ skill, onRemove }) => {
  const [loading, setLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string>('');
  const userId = localStorage.getItem('user_id');
  const token = localStorage.getItem('token');

  const handleRemove = async () => {
    if (!confirm(`Remove "${skill.name}" from your skills?`)) return;

    setLoading(true);
    setError('');

    try {
      const response = await axios.delete(
        `/api/students/${userId}/skills/${skill.id}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.status === 'success' && onRemove) {
        onRemove(skill.id);
      } else {
        setError('Failed to remove skill');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to remove skill');
    } finally {
      setLoading(false);
    }
  };

  const getProficiencyColor = (level: number) => {
    if (level >= 8) return 'bg-green-100 text-green-800';
    if (level >= 6) return 'bg-blue-100 text-blue-800';
    if (level >= 4) return 'bg-yellow-100 text-yellow-800';
    return 'bg-orange-100 text-orange-800';
  };

  const getProficiencyLabel = (level: number) => {
    if (level >= 9) return 'Expert';
    if (level >= 7) return 'Advanced';
    if (level >= 5) return 'Intermediate';
    return 'Beginner';
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{skill.name}</h3>
          <p className="text-xs text-gray-500 capitalize">
            Source: {skill.source}
            {skill.confidence && ` • ${(skill.confidence * 100).toFixed(0)}% confidence`}
          </p>
        </div>
        <Button
          variant="danger"
          size="sm"
          onClick={handleRemove}
          disabled={loading}
        >
          {loading ? '...' : 'Remove'}
        </Button>
      </div>

      <div className="mb-3">
        <div className="flex items-center justify-between mb-2">
          <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getProficiencyColor(skill.proficiency_claimed)}`}>
            {getProficiencyLabel(skill.proficiency_claimed)}
          </span>
          <span className="text-sm font-bold text-gray-700">
            {skill.proficiency_claimed}/10
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-indigo-600 h-2 rounded-full transition-all"
            style={{ width: `${(skill.proficiency_claimed / 10) * 100}%` }}
          ></div>
        </div>
      </div>

      {error && (
        <p className="text-red-600 text-sm mt-2">{error}</p>
      )}
    </div>
  );
};

export default SkillCard;
