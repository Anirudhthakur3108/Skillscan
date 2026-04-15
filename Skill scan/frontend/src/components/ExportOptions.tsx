import React, { useState } from 'react';
import { Card } from './Card';
import { Button } from './Button';

interface ExportOption {
  id: string;
  label: string;
  description: string;
  icon: string;
  selected: boolean;
}

interface ExportOptionsProps {
  onOptionsChange?: (options: ExportOption[]) => void;
  disabled?: boolean;
}

export const ExportOptions: React.FC<ExportOptionsProps> = ({
  onOptionsChange,
  disabled = false,
}) => {
  const [options, setOptions] = useState<ExportOption[]>([
    {
      id: 'assessments',
      label: 'Assessments',
      description: 'All assessment history with scores and feedback',
      icon: '✅',
      selected: true,
    },
    {
      id: 'gaps',
      label: 'Gap Analysis',
      description: 'Identified gaps with recommendations and benchmarks',
      icon: '🎯',
      selected: true,
    },
    {
      id: 'profile',
      label: 'Complete Profile',
      description: 'All skills, assessments, gaps, and learning plans',
      icon: '📋',
      selected: true,
    },
    {
      id: 'learning_plans',
      label: 'Learning Plans',
      description: 'Your personalized learning paths and milestones',
      icon: '📚',
      selected: true,
    },
  ]);

  const handleToggle = (id: string) => {
    const updated = options.map((opt) =>
      opt.id === id ? { ...opt, selected: !opt.selected } : opt
    );
    setOptions(updated);
    onOptionsChange?.(updated);
  };

  const handleSelectAll = () => {
    const allSelected = options.every((opt) => opt.selected);
    const updated = options.map((opt) => ({
      ...opt,
      selected: !allSelected,
    }));
    setOptions(updated);
    onOptionsChange?.(updated);
  };

  const selectedCount = options.filter((opt) => opt.selected).length;

  return (
    <Card className="export-options">
      <div className="export-options-header">
        <h3>Select Content to Include</h3>
        <button
          className="select-all-btn"
          onClick={handleSelectAll}
          disabled={disabled}
        >
          {selectedCount === options.length ? 'Deselect All' : 'Select All'}
        </button>
      </div>

      <div className="export-options-list">
        {options.map((option) => (
          <label key={option.id} className="export-option-item">
            <div className="option-checkbox">
              <input
                type="checkbox"
                checked={option.selected}
                onChange={() => handleToggle(option.id)}
                disabled={disabled}
              />
              <span className="option-icon">{option.icon}</span>
            </div>
            <div className="option-content">
              <div className="option-label">{option.label}</div>
              <div className="option-description">{option.description}</div>
            </div>
          </label>
        ))}
      </div>

      <div className="export-options-footer">
        <p className="selection-count">
          {selectedCount} of {options.length} items selected
        </p>
      </div>
    </Card>
  );
};

export default ExportOptions;
