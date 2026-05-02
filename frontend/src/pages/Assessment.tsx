import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { FaSpinner, FaArrowRight } from 'react-icons/fa6';
import { LuBrainCircuit } from 'react-icons/lu';
import { FiFileText } from 'react-icons/fi';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';

interface AssessmentItem {
  assessment_id: number;
  skill_name: string;
  category: string;
  status: string;
  score: number | null;
  gap_identified: boolean | null;
  created_at: string;
}

const Assessment: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const assessmentId = searchParams.get('assessment_id');
  const [assessmentsList, setAssessmentsList] = useState<AssessmentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // If an assessment_id is provided in the URL, redirect to the modern test runner
    // which supports MCQ, Coding, and Case Study questions.
    if (assessmentId) {
      navigate(`/assessment-test?assessment_id=${assessmentId}`, { replace: true });
      return;
    }

    const fetchAllAssessments = async () => {
      if (!user?.id) return;
      try {
        const response = await apiClient.get(`/assessments/student/${user.id}`);
        setAssessmentsList(response.data.assessments || []);
      } catch (err) {
        console.error("Failed to load assessments:", err);
        setError("Failed to load assessments. Please try again later.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchAllAssessments();
  }, [assessmentId, navigate, user]);

  if (isLoading && !assessmentId) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center">
        <FaSpinner size={48} className="animate-spin text-primary mb-4" />
        <p className="text-foreground-muted font-medium animate-pulse">Loading your verification history...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 lg:py-12 max-w-6xl">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">My Assessments</h1>
          <p className="text-foreground-muted font-medium">
            Manage and continue your generated skill verification journeys.
          </p>
        </div>
        <button 
          onClick={() => navigate('/dashboard')}
          className="px-6 py-3 bg-white/5 border border-white/10 rounded-xl font-bold hover:bg-white/10 transition-all flex items-center gap-2"
        >
          Back to Dashboard
        </button>
      </div>

      {error ? (
        <div className="glass p-8 rounded-3xl border border-red-500/20 text-center space-y-4">
          <p className="text-red-400 font-medium">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-primary/10 text-primary rounded-xl font-bold hover:bg-primary hover:text-white transition-all"
          >
            Retry
          </button>
        </div>
      ) : assessmentsList.length === 0 ? (
        <div className="glass p-20 rounded-[3rem] border border-white/5 text-center space-y-6">
          <div className="w-20 h-20 bg-white/5 rounded-3xl flex items-center justify-center mx-auto mb-4">
            <FiFileText size={40} className="text-white/20" />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white/90">No assessments found</h2>
            <p className="text-foreground-muted max-w-xs mx-auto">
              You haven't generated any assessments yet. Head back to the dashboard to start verifying your skills.
            </p>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-8 py-3 bg-primary text-white rounded-xl font-bold hover:bg-primary-dark transition-all shadow-lg shadow-primary/20"
          >
            Go to Dashboard
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {assessmentsList.map((a) => (
            <div 
              key={a.assessment_id} 
              className="glass p-8 rounded-[2.5rem] border border-white/5 flex flex-col space-y-8 hover:border-primary/30 transition-all group relative overflow-hidden"
            >
              {/* Decorative background element */}
              <div className="absolute -top-10 -right-10 w-32 h-32 bg-primary/5 rounded-full blur-3xl group-hover:bg-primary/10 transition-colors" />
              
              <div className="relative z-10">
                <div className="flex justify-between items-start mb-4">
                  <div className="p-3 rounded-2xl bg-white/5 border border-white/10 text-primary group-hover:scale-110 transition-transform">
                    <LuBrainCircuit size={24} />
                  </div>
                  <span className={`text-[10px] font-black uppercase tracking-[0.2em] px-3 py-1.5 rounded-full ${
                    a.status === 'completed' 
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                      : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  }`}>
                    {a.status}
                  </span>
                </div>
                
                <div className="space-y-1">
                  <h3 className="font-bold text-xl leading-tight group-hover:text-primary transition-colors">
                    {a.skill_name}
                  </h3>
                  <p className="text-[11px] text-foreground-muted uppercase tracking-[0.15em] font-bold">
                    {a.category}
                  </p>
                </div>
              </div>

              <div className="flex-1 min-h-[40px] relative z-10">
                {a.status === 'completed' && a.score !== null && (
                  <div className="space-y-1">
                    <div className="text-3xl font-black text-white tabular-nums">{a.score}</div>
                    <div className="text-[10px] font-bold uppercase tracking-widest text-foreground-muted">Verified Proficiency</div>
                  </div>
                )}
                {a.status !== 'completed' && (
                  <div className="space-y-3">
                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full bg-amber-500/50 w-1/3 rounded-full" />
                    </div>
                    <div className="text-[10px] font-bold text-amber-500/70 uppercase tracking-widest">Questions Generated • Ready</div>
                  </div>
                )}
              </div>

              <div className="pt-6 border-t border-white/5 relative z-10">
                {a.status === 'completed' ? (
                  <button
                    onClick={() => navigate(`/results?assessment_id=${a.assessment_id}`)}
                    className="w-full py-4 bg-white/5 rounded-2xl text-sm font-bold hover:bg-white/10 transition-all flex items-center justify-center gap-2 border border-white/5"
                  >
                    View Performance Report <FaArrowRight size={14} />
                  </button>
                ) : (
                  <button
                    onClick={() => navigate(`/assessment-test?assessment_id=${a.assessment_id}`)}
                    className="w-full py-4 bg-primary text-white rounded-2xl text-sm font-bold hover:bg-primary-dark transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary/20"
                  >
                    Start Assessment <FaArrowRight size={14} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer Branding */}
      <div className="mt-16 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4 text-[10px] font-bold uppercase tracking-[0.2em] text-foreground-muted/40">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
          <span>Scholar Veritas Academic Portal</span>
        </div>
        <span className="text-primary/60">© 2026 Architecting the Future of Verification</span>
      </div>
    </div>
  );
};

export default Assessment;
