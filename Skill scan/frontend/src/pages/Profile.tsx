import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import SkillInput from '../components/skills/SkillInput';
import SkillCard from '../components/skills/SkillCard';

interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  user_type: string;
}

interface Skill {
  id: number;
  name: string;
  proficiency_claimed: number;
  source: string;
  confidence?: number;
}

interface ExtractedSkill {
  skill_name: string;
  confidence: number;
}

const Profile: React.FC = () => {
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [uploading, setUploading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [showResumeConfirmation, setShowResumeConfirmation] = useState<boolean>(false);
  const [extractedSkills, setExtractedSkills] = useState<ExtractedSkill[]>([]);
  const [resumeFile, setResumeFile] = useState<File | null>(null);

  const token = localStorage.getItem('token');
  const userId = localStorage.getItem('user_id');
  const userName = localStorage.getItem('user_name');
  const userType = localStorage.getItem('user_type');

  useEffect(() => {
    if (!token || !userId) {
      window.location.href = '/login';
      return;
    }

    // Set user profile from localStorage and fetch skills
    setUserProfile({
      id: parseInt(userId),
      email: '',
      full_name: userName || '',
      user_type: userType || ''
    });

    fetchSkills();
  }, []);

  const fetchSkills = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/students/${userId}/skills`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.status === 'success') {
        setSkills(response.data.skills || []);
      }
    } catch (err: any) {
      console.error('Error fetching skills:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleResumeUpload = async (file: File) => {
    if (!file.name.endsWith('.pdf')) {
      setError('Only PDF files are accepted');
      return;
    }

    setResumeFile(file);
    setUploading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(
        `/api/students/${userId}/skills/upload`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      if (response.data.status === 'success') {
        setExtractedSkills(response.data.extracted_skills || []);
        setShowResumeConfirmation(true);
        setSuccessMessage(`Successfully extracted ${response.data.extracted_skills.length} skills from your resume`);
      } else {
        setError(response.data.message || 'Failed to extract skills from resume');
      }
    } catch (err: any) {
      setError(
        err.response?.data?.message ||
        'Failed to upload resume. Please try again or add skills manually.'
      );
    } finally {
      setUploading(false);
    }
  };

  const handleConfirmExtractedSkills = async () => {
    try {
      setLoading(true);
      const skillsToAdd = extractedSkills.map(skill => ({
        skill_name: skill.skill_name,
        proficiency_claimed: 5 // Default to 5 for extracted skills
      }));

      for (const skill of skillsToAdd) {
        await axios.post(
          `/api/students/${userId}/skills/add-manual`,
          skill,
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );
      }

      setShowResumeConfirmation(false);
      setExtractedSkills([]);
      setResumeFile(null);
      setSuccessMessage('Skills added successfully!');
      
      // Refresh skills list
      await fetchSkills();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to add skills');
    } finally {
      setLoading(false);
    }
  };

  const handleSkillAdded = (skill: { skill_name: string; proficiency_claimed: number }) => {
    setSuccessMessage(`Skill "${skill.skill_name}" added successfully!`);
    fetchSkills();
    setTimeout(() => setSuccessMessage(''), 3000);
  };

  const handleSkillRemoved = (skillId: number) => {
    setSkills(skills.filter(s => s.id !== skillId));
    setSuccessMessage('Skill removed successfully!');
    setTimeout(() => setSuccessMessage(''), 3000);
  };

  if (loading && !userProfile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* User Profile Header */}
        <Card className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{userProfile?.full_name}</h1>
              <p className="text-gray-600 mt-1">{userProfile?.user_type}</p>
            </div>
            <Button onClick={() => {
              localStorage.clear();
              window.location.href = '/login';
            }}>
              Logout
            </Button>
          </div>
        </Card>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
            {error}
            <button
              onClick={() => setError('')}
              className="ml-4 text-red-600 hover:text-red-800 font-semibold"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Success Message */}
        {successMessage && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md text-green-700">
            {successMessage}
          </div>
        )}

        {/* Resume Upload Section */}
        <Card className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Upload Your Resume</h2>
          
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-indigo-500 transition">
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => e.target.files && handleResumeUpload(e.target.files[0])}
              disabled={uploading}
              className="hidden"
              id="resume-upload"
            />
            <label htmlFor="resume-upload" className="cursor-pointer">
              {uploading ? (
                <>
                  <LoadingSpinner />
                  <p className="mt-4 text-gray-600">Extracting skills...</p>
                </>
              ) : (
                <>
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    stroke="currentColor"
                    fill="none"
                    viewBox="0 0 48 48"
                  >
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20a4 4 0 004 4h24a4 4 0 004-4V20m-6-12v12m0 0l-3-3m3 3l3-3"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <p className="mt-4 text-gray-700 font-semibold">Drop your resume here</p>
                  <p className="text-gray-600 text-sm">or click to browse (PDF only)</p>
                  <p className="text-gray-500 text-xs mt-2">Skills will be automatically extracted</p>
                </>
              )}
            </label>
          </div>
        </Card>

        {/* Resume Confirmation Modal */}
        {showResumeConfirmation && extractedSkills.length > 0 && (
          <Card className="mb-8 border-2 border-indigo-500 bg-indigo-50">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Confirm Extracted Skills</h3>
            <p className="text-gray-600 mb-6">
              We found {extractedSkills.length} skills in your resume. Review and confirm:
            </p>
            
            <div className="space-y-3 mb-6">
              {extractedSkills.map((skill, idx) => (
                <div key={idx} className="flex items-center justify-between bg-white p-4 rounded-lg border border-gray-200">
                  <span className="font-semibold text-gray-900">{skill.skill_name}</span>
                  <span className="text-sm text-gray-600">
                    Confidence: {(skill.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>

            <div className="flex gap-4">
              <Button
                onClick={handleConfirmExtractedSkills}
                disabled={loading}
                className="flex-1"
              >
                {loading ? <LoadingSpinner /> : 'Confirm & Add Skills'}
              </Button>
              <Button
                onClick={() => {
                  setShowResumeConfirmation(false);
                  setExtractedSkills([]);
                }}
                variant="outline"
                className="flex-1"
              >
                Cancel
              </Button>
            </div>
          </Card>
        )}

        {/* Manual Skill Input Section */}
        <Card className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Add Skills Manually</h2>
          <SkillInput userId={parseInt(userId!)} onSkillAdded={handleSkillAdded} />
        </Card>

        {/* Current Skills Section */}
        <Card>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Your Skills</h2>
          
          {skills.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600">No skills added yet. Upload a resume or add skills manually.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {skills.map(skill => (
                <SkillCard
                  key={skill.id}
                  skill={skill}
                  onRemove={handleSkillRemoved}
                />
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default Profile;
