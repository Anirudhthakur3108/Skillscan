import React, { useState } from 'react';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { exportService } from '../api/export';
import '../styles/Export.css';

interface ExportOptions {
  format: 'pdf' | 'csv' | 'zip';
  includeAssessments: boolean;
  includeGaps: boolean;
  includeProfile: boolean;
  includeLearningPlans: boolean;
}

interface ExportHistory {
  id: string;
  type: string;
  format: string;
  timestamp: string;
  filename: string;
  size: string;
}

export const Export: React.FC = () => {
  const [options, setOptions] = useState<ExportOptions>({
    format: 'pdf',
    includeAssessments: true,
    includeGaps: true,
    includeProfile: true,
    includeLearningPlans: true,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [history, setHistory] = useState<ExportHistory[]>([]);

  const handleFormatChange = (format: 'pdf' | 'csv' | 'zip') => {
    setOptions({ ...options, format });
    setError(null);
  };

  const handleOptionChange = (key: keyof Omit<ExportOptions, 'format'>) => {
    setOptions({
      ...options,
      [key]: !options[key],
    });
  };

  const handleExport = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      if (options.format === 'zip') {
        await exportService.exportAll(options.format);
      } else if (options.includeProfile) {
        await exportService.exportProfile(options.format);
      } else if (options.includeAssessments) {
        await exportService.exportAssessments(options.format);
      } else if (options.includeGaps) {
        await exportService.exportGapReports(options.format);
      } else {
        setError('Please select at least one export option');
        return;
      }

      setSuccess('Export completed successfully!');
      
      // Add to history
      const newEntry: ExportHistory = {
        id: Date.now().toString(),
        type: options.includeProfile ? 'Profile' : 'Partial',
        format: options.format.toUpperCase(),
        timestamp: new Date().toLocaleString(),
        filename: `skillscan-export-${Date.now()}.${options.format === 'pdf' ? 'pdf' : options.format === 'csv' ? 'csv' : 'zip'}`,
        size: 'calculating...',
      };
      
      setHistory([newEntry, ...history]);

      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(null), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed. Please try again.');
      console.error('Export error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getEstimatedSize = (): string => {
    let size = 0;
    if (options.includeProfile) size += 2;
    if (options.includeAssessments) size += 1;
    if (options.includeGaps) size += 1;
    if (options.includeLearningPlans) size += 0.5;
    
    return `${(size).toFixed(1)} MB`;
  };

  return (
    <div className="export-container">
      <div className="export-header">
        <h1>Export Your Data</h1>
        <p>Download your assessments, gaps, and profile in your preferred format</p>
      </div>

      <div className="export-content">
        {/* Format Selection */}
        <Card className="export-card">
          <h2>Select Export Format</h2>
          <div className="format-options">
            <button
              className={`format-btn ${options.format === 'pdf' ? 'active' : ''}`}
              onClick={() => handleFormatChange('pdf')}
              disabled={loading}
            >
              📄 PDF
              <small>Professional reports</small>
            </button>
            <button
              className={`format-btn ${options.format === 'csv' ? 'active' : ''}`}
              onClick={() => handleFormatChange('csv')}
              disabled={loading}
            >
              📊 CSV
              <small>Data analysis</small>
            </button>
            <button
              className={`format-btn ${options.format === 'zip' ? 'active' : ''}`}
              onClick={() => handleFormatChange('zip')}
              disabled={loading}
            >
              📦 ZIP
              <small>All formats</small>
            </button>
          </div>
        </Card>

        {/* Content Selection */}
        <Card className="export-card">
          <h2>Select Content to Export</h2>
          <div className="content-options">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={options.includeProfile}
                onChange={() => handleOptionChange('includeProfile')}
                disabled={loading}
              />
              <span>📋 Complete Profile</span>
              <small>All skills, assessments, gaps, and learning plans</small>
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={options.includeAssessments}
                onChange={() => handleOptionChange('includeAssessments')}
                disabled={loading}
              />
              <span>✅ Assessments</span>
              <small>All assessment history with scores and feedback</small>
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={options.includeGaps}
                onChange={() => handleOptionChange('includeGaps')}
                disabled={loading}
              />
              <span>🎯 Gap Analysis</span>
              <small>Identified gaps with recommendations</small>
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={options.includeLearningPlans}
                onChange={() => handleOptionChange('includeLearningPlans')}
                disabled={loading}
              />
              <span>📚 Learning Plans</span>
              <small>Your personalized learning paths</small>
            </label>
          </div>
        </Card>

        {/* Export Summary */}
        <Card className="export-card summary">
          <h3>Export Summary</h3>
          <div className="summary-info">
            <p>
              <strong>Format:</strong> {options.format.toUpperCase()}
            </p>
            <p>
              <strong>Estimated Size:</strong> {getEstimatedSize()}
            </p>
            <p>
              <strong>Frequency:</strong> Unlimited (no restrictions)
            </p>
          </div>
        </Card>

        {/* Alerts */}
        {error && (
          <div className="alert alert-error">
            ❌ {error}
          </div>
        )}

        {success && (
          <div className="alert alert-success">
            ✅ {success}
          </div>
        )}

        {/* Export Button */}
        <div className="export-actions">
          <Button
            onClick={handleExport}
            disabled={loading || (!options.includeProfile && !options.includeAssessments && !options.includeGaps)}
            className="export-btn-primary"
          >
            {loading ? (
              <>
                <LoadingSpinner /> Exporting...
              </>
            ) : (
              '📥 Download Export'
            )}
          </Button>
        </div>

        {/* Export History */}
        {history.length > 0 && (
          <Card className="export-card">
            <h2>Recent Exports</h2>
            <div className="history-table">
              <table>
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Format</th>
                    <th>Date & Time</th>
                    <th>Filename</th>
                  </tr>
                </thead>
                <tbody>
                  {history.slice(0, 5).map((item) => (
                    <tr key={item.id}>
                      <td>{item.type}</td>
                      <td>
                        <span className={`format-badge ${item.format.toLowerCase()}`}>
                          {item.format}
                        </span>
                      </td>
                      <td>{item.timestamp}</td>
                      <td className="filename">{item.filename}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Information Box */}
        <Card className="info-box">
          <h3>ℹ️ What's Included in Each Export?</h3>
          <ul>
            <li>
              <strong>PDF Format:</strong> Professional reports with formatted tables, charts, and detailed information
            </li>
            <li>
              <strong>CSV Format:</strong> Data-friendly spreadsheet format for import into Excel or analysis tools
            </li>
            <li>
              <strong>ZIP Format:</strong> Combined archive with all selected data in multiple formats
            </li>
            <li>
              <strong>Complete Profile:</strong> All your skills, assessments, gaps, and learning plans in one document
            </li>
          </ul>
        </Card>
      </div>
    </div>
  );
};

export default Export;
