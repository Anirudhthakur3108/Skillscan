import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import Button from '../ui/Button';
import Input from '../ui/Input';

interface SkillInputProps {
  userId: number;
  onSkillAdded?: (skill: { skill_name: string; proficiency_claimed: number }) => void;
}

interface SkillOption {
  name: string;
  category: string;
}

const AVAILABLE_SKILLS: SkillOption[] = [
  // MBA Analytics
  { name: 'Python', category: 'MBA_Analytics' },
  { name: 'SQL', category: 'MBA_Analytics' },
  { name: 'Excel/VBA', category: 'MBA_Analytics' },
  { name: 'Tableau', category: 'MBA_Analytics' },
  { name: 'Power BI', category: 'MBA_Analytics' },
  { name: 'Statistics', category: 'MBA_Analytics' },
  { name: 'Data Analysis', category: 'MBA_Analytics' },
  { name: 'R', category: 'MBA_Analytics' },
  { name: 'Machine Learning', category: 'MBA_Analytics' },
  // BCA
  { name: 'Java', category: 'BCA' },
  { name: 'C++', category: 'BCA' },
  { name: 'JavaScript', category: 'BCA' },
  { name: 'React', category: 'BCA' },
  { name: 'Web Development', category: 'BCA' },
  { name: 'SQL/Databases', category: 'BCA' },
  { name: 'Data Structures', category: 'BCA' },
  { name: 'System Design', category: 'BCA' }
];

const SkillInput: React.FC<SkillInputProps> = ({ userId, onSkillAdded }) => {
  const [selectedSkill, setSelectedSkill] = useState<string>('');
  const [proficiency, setProficiency] = useState<number>(5);
  const [customSkill, setCustomSkill] = useState<string>('');
  const [useCustom, setUseCustom] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [suggestions, setSuggestions] = useState<SkillOption[]>([]);
  const [showSuggestions, setShowSuggestions] = useState<boolean>(false);
  const inputRef = useRef<HTMLDivElement>(null);
  const token = localStorage.getItem('token');

  // Handle autocomplete search
  const handleSearchChange = (value: string) => {
    setSelectedSkill(value);
    
    if (value.trim().length > 0) {
      const filtered = AVAILABLE_SKILLS.filter(skill =>
        skill.name.toLowerCase().includes(value.toLowerCase())
      );
      setSuggestions(filtered);
      setShowSuggestions(true);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  // Handle skill selection from dropdown
  const handleSelectSkill = (skillName: string) => {
    setSelectedSkill(skillName);
    setSuggestions([]);
    setShowSuggestions(false);
    setUseCustom(false);
  };

  // Handle adding skill
  const handleAddSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const skillName = useCustom ? customSkill.trim() : selectedSkill.trim();

    if (!skillName) {
      setError('Please select or enter a skill name');
      return;
    }

    if (proficiency < 1 || proficiency > 10) {
      setError('Proficiency must be between 1 and 10');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(
        `/api/students/${userId}/skills/add-manual`,
        {
          skill_name: skillName,
          proficiency_claimed: proficiency
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.status === 'success') {
        // Reset form
        setSelectedSkill('');
        setCustomSkill('');
        setProficiency(5);
        setUseCustom(false);

        // Notify parent
        if (onSkillAdded) {
          onSkillAdded({
            skill_name: skillName,
            proficiency_claimed: proficiency
          });
        }
      } else {
        setError(response.data.message || 'Failed to add skill');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to add skill');
    } finally {
      setLoading(false);
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (inputRef.current && !inputRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <form onSubmit={handleAddSkill} className="space-y-4">
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
          {error}
        </div>
      )}

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Add a Skill
        </label>

        {/* Smart Autocomplete Dropdown */}
        {!useCustom ? (
          <div ref={inputRef} className="relative">
            <input
              type="text"
              value={selectedSkill}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="Search skills (e.g., Python, React...)"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />

            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute top-full mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg z-10 max-h-48 overflow-y-auto">
                {suggestions.map((skill, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelectSkill(skill.name)}
                    className="w-full text-left px-4 py-2 hover:bg-indigo-50 border-b border-gray-200 last:border-b-0"
                  >
                    <span className="font-semibold text-gray-900">{skill.name}</span>
                    <span className="text-xs text-gray-500 ml-2">({skill.category})</span>
                  </button>
                ))}
              </div>
            )}

            {showSuggestions && selectedSkill && suggestions.length === 0 && (
              <div className="absolute top-full mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg z-10 p-4 text-center text-gray-600">
                No skills found. Try adding a custom skill instead.
              </div>
            )}
          </div>
        ) : (
          <Input
            type="text"
            value={customSkill}
            onChange={(e) => setCustomSkill(e.target.value)}
            placeholder="Enter custom skill name"
          />
        )}

        <button
          type="button"
          onClick={() => {
            setUseCustom(!useCustom);
            setSelectedSkill('');
            setCustomSkill('');
            setSuggestions([]);
            setShowSuggestions(false);
          }}
          className="text-sm text-indigo-600 hover:text-indigo-700 font-semibold"
        >
          {useCustom ? '← Back to dropdown' : 'Or add a custom skill →'}
        </button>
      </div>

      {/* Proficiency Slider */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Proficiency Level: <span className="text-indigo-600 font-bold">{proficiency}/10</span>
        </label>
        <input
          type="range"
          min="1"
          max="10"
          value={proficiency}
          onChange={(e) => setProficiency(parseInt(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          disabled={loading}
        />
        <div className="flex justify-between text-xs text-gray-500">
          <span>Beginner</span>
          <span>Expert</span>
        </div>
      </div>

      {/* Add Skill Button */}
      <Button
        type="submit"
        fullWidth
        disabled={loading || (!useCustom && !selectedSkill) || (useCustom && !customSkill)}
      >
        {loading ? 'Adding...' : 'Add Skill'}
      </Button>
    </form>
  );
};

export default SkillInput;
