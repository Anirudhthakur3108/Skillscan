import axios, { AxiosError } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

interface ExportResponse {
  success: boolean;
  data?: any;
  error?: string;
}

class ExportService {
  private readonly baseURL: string = `${API_BASE_URL}/export`;

  /**
   * Export single assessment as PDF
   */
  async exportAssessmentPDF(studentId: number, assessmentId: number): Promise<Blob> {
    try {
      const response = await axios.post(
        `${this.baseURL}/assessment-pdf`,
        {
          student_id: studentId,
          assessment_id: assessmentId,
        },
        {
          responseType: 'blob',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      this.triggerDownload(response.data, `assessment_${assessmentId}.pdf`);
      return response.data;
    } catch (error) {
      this.handleError(error, 'Failed to export assessment PDF');
      throw error;
    }
  }

  /**
   * Export gap report as PDF
   */
  async exportGapReportPDF(studentId: number, skillId: number): Promise<Blob> {
    try {
      const response = await axios.post(
        `${this.baseURL}/gap-report-pdf`,
        {
          student_id: studentId,
          skill_id: skillId,
        },
        {
          responseType: 'blob',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      this.triggerDownload(response.data, `gap_report_${skillId}.pdf`);
      return response.data;
    } catch (error) {
      this.handleError(error, 'Failed to export gap report');
      throw error;
    }
  }

  /**
   * Export complete profile as PDF
   */
  async exportProfilePDF(studentId: number): Promise<Blob> {
    try {
      const response = await axios.post(
        `${this.baseURL}/profile-pdf`,
        {
          student_id: studentId,
        },
        {
          responseType: 'blob',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      this.triggerDownload(response.data, 'profile_complete.pdf');
      return response.data;
    } catch (error) {
      this.handleError(error, 'Failed to export profile');
      throw error;
    }
  }

  /**
   * Export assessments as CSV
   */
  async exportAssessmentsCSV(studentId: number, skillId?: number): Promise<Blob> {
    try {
      const response = await axios.post(
        `${this.baseURL}/assessments-csv`,
        {
          student_id: studentId,
          skill_id: skillId,
        },
        {
          responseType: 'blob',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      this.triggerDownload(response.data, 'assessments.csv');
      return response.data;
    } catch (error) {
      this.handleError(error, 'Failed to export assessments CSV');
      throw error;
    }
  }

  /**
   * Export skills as CSV
   */
  async exportSkillsCSV(studentId: number): Promise<Blob> {
    try {
      const response = await axios.post(
        `${this.baseURL}/skills-csv`,
        {
          student_id: studentId,
        },
        {
          responseType: 'blob',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      this.triggerDownload(response.data, 'skills.csv');
      return response.data;
    } catch (error) {
      this.handleError(error, 'Failed to export skills CSV');
      throw error;
    }
  }

  /**
   * Export all data as ZIP
   */
  async exportAll(studentId: number, format: 'zip' | 'pdf' | 'csv' = 'zip'): Promise<Blob> {
    try {
      const response = await axios.post(
        `${this.baseURL}/all`,
        {
          student_id: studentId,
          format,
        },
        {
          responseType: 'blob',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      const filename = `skillscan_export_${new Date().toISOString().slice(0, 10)}.${
        format === 'zip' ? 'zip' : format === 'pdf' ? 'pdf' : 'csv'
      }`;

      this.triggerDownload(response.data, filename);
      return response.data;
    } catch (error) {
      this.handleError(error, 'Failed to export all data');
      throw error;
    }
  }

  /**
   * Export profile data
   */
  async exportProfile(studentId: number, format: 'pdf' | 'csv'): Promise<Blob> {
    if (format === 'pdf') {
      return this.exportProfilePDF(studentId);
    } else {
      return this.exportAssessmentsCSV(studentId);
    }
  }

  /**
   * Export assessments data
   */
  async exportAssessments(studentId: number, format: 'pdf' | 'csv'): Promise<Blob> {
    if (format === 'pdf') {
      return this.exportProfilePDF(studentId);
    } else {
      return this.exportAssessmentsCSV(studentId);
    }
  }

  /**
   * Export gap reports
   */
  async exportGapReports(studentId: number, format: 'pdf' | 'csv'): Promise<Blob> {
    // This would need a skill_id in production
    // For now, return profile which includes gaps
    return this.exportProfile(studentId, format);
  }

  /**
   * Get export status and options
   */
  async getExportStatus(): Promise<ExportResponse> {
    try {
      const response = await axios.get(
        `${this.baseURL}/status`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      this.handleError(error, 'Failed to get export status');
      return {
        success: false,
        error: 'Failed to get export status',
      };
    }
  }

  /**
   * Trigger file download
   */
  private triggerDownload(data: Blob, filename: string): void {
    const url = window.URL.createObjectURL(data);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  /**
   * Handle API errors
   */
  private handleError(error: any, message: string): void {
    console.error(message, error);

    if (error instanceof AxiosError) {
      if (error.response?.status === 401) {
        throw new Error('Unauthorized. Please log in again.');
      } else if (error.response?.status === 404) {
        throw new Error('Resource not found.');
      } else if (error.response?.status === 500) {
        throw new Error('Server error. Please try again later.');
      } else if (error.message) {
        throw new Error(error.message);
      }
    }

    throw new Error(message);
  }
}

export const exportService = new ExportService();
