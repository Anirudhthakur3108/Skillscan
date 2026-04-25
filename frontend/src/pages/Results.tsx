import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Award, Target, Brain, ArrowUpRight, CheckCircle2, AlertCircle, BookOpen, Clock, Zap, ExternalLink, Loader2, ShieldCheck, Map as MapIcon, ArrowRight, Layout } from 'lucide-react';
import apiClient from '../api/client';

const Results: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const assessmentId = searchParams.get('assessment_id');

  const [assessment, setAssessment] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!assessmentId) {
      setError("No assessment ID provided.");
      setIsLoading(false);
      return;
    }

    const fetchResults = async () => {
      try {
        const response = await apiClient.get(`/assessments/${assessmentId}`);
        setAssessment(response.data);
      } catch (err) {
        console.error("Failed to load assessment results:", err);
        setError("Failed to load assessment results.");
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchResults();
  }, [assessmentId]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 size={48} className="animate-spin text-primary" />
      </div>
    );
  }

  if (error || !assessment) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="glass p-8 rounded-3xl border border-red-500/20 max-w-md text-center space-y-4">
          <h2 className="text-xl font-bold text-red-400">Error</h2>
          <p className="text-foreground-muted">{error || "Results not found."}</p>
          <button 
            onClick={() => navigate('/dashboard')}
            className="px-6 py-2 bg-white/5 rounded-lg font-bold hover:bg-white/10"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const aiFeedback = assessment.ai_feedback || {};
  const score = aiFeedback.score || 0;
  
  // Format based on the prompt expected return
  const strengths = aiFeedback.strengths || [];
  const weaknesses = aiFeedback.weaknesses || [];
  const learningPlan = aiFeedback.learning_plan || [];

  return (
    <div className="container mx-auto px-6 py-12 max-w-5xl space-y-16">
      {/* Hero Result Section */}
      <div className="glass rounded-[3rem] p-12 lg:p-16 border border-white/20 shadow-2xl relative overflow-hidden text-center lg:text-left">
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary/20 rounded-full blur-[120px] -mr-48 -mt-48" />
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6 relative z-10">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-bold border border-primary/20">
              <ShieldCheck size={18} />
              Skill Validation Report
            </div>
            <h1 className="text-4xl lg:text-5xl font-bold">{assessment.skill_name || 'Assessment'} Results</h1>
            <p className="text-xl text-foreground-muted leading-relaxed">
              Based on our AI-driven assessment, your technical capabilities have been successfully evaluated.
            </p>
            <div className="flex gap-4">
              <button 
                onClick={() => navigate('/dashboard')}
                className="px-6 py-3 rounded-xl bg-white/5 border border-white/10 font-bold hover:bg-white/10 transition-colors"
              >
                Dashboard
              </button>
            </div>
          </div>
          
          <div className="relative z-10 flex flex-col items-center justify-center p-8 glass rounded-3xl border border-white/10 aspect-square">
            <div className="text-8xl font-black text-primary mb-2">{score}</div>
            <div className="text-lg font-bold uppercase tracking-widest text-foreground-muted">Overall Mastery</div>
            <div className="mt-8 h-2 w-full bg-white/5 rounded-full overflow-hidden">
              <div className="h-full bg-primary rounded-full shadow-[0_0_15px_rgba(16,185,129,0.4)] transition-all" style={{ width: `${score}%` }} />
            </div>
          </div>
        </div>
      </div>

      {/* Gap Analysis */}
      <div className="space-y-8">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-primary/10 text-primary">
            <Target size={28} />
          </div>
          <h2 className="text-3xl font-bold">Cognitive Analysis</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="glass p-8 rounded-3xl border border-white/10 space-y-4 hover:border-white/20 transition-all">
            <div className="flex justify-between items-start">
              <h3 className="text-2xl font-bold">Verified Strengths</h3>
              <span className="text-[10px] font-bold px-2 py-1 rounded bg-white/5 uppercase tracking-widest text-primary">
                Solid
              </span>
            </div>
            <ul className="space-y-3 mt-4">
              {strengths.map((str: string, i: number) => (
                <li key={i} className="flex gap-3 text-sm text-foreground-muted leading-relaxed">
                  <span className="text-primary mt-0.5">•</span>
                  {str}
                </li>
              ))}
              {strengths.length === 0 && (
                <li className="text-sm text-foreground-muted italic">No specific strengths verified yet.</li>
              )}
            </ul>
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-tighter text-foreground-muted/60 mt-4">
              <Zap size={14} className="text-primary" /> Proficient
            </div>
          </div>

          <div className="glass p-8 rounded-3xl border border-white/10 space-y-4 hover:border-white/20 transition-all">
            <div className="flex justify-between items-start">
              <h3 className="text-2xl font-bold">Knowledge Gaps</h3>
              <span className="text-[10px] font-bold px-2 py-1 rounded bg-white/5 uppercase tracking-widest text-amber-400">
                Gap Identified
              </span>
            </div>
            <ul className="space-y-3 mt-4">
              {weaknesses.map((weak: string, i: number) => (
                <li key={i} className="flex gap-3 text-sm text-foreground-muted leading-relaxed">
                  <span className="text-amber-400 mt-0.5">•</span>
                  {weak}
                </li>
              ))}
              {weaknesses.length === 0 && (
                <li className="text-sm text-foreground-muted italic">No major knowledge gaps identified.</li>
              )}
            </ul>
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-tighter text-foreground-muted/60 mt-4">
              <AlertCircle size={14} className="text-amber-400" /> Focus Area
            </div>
          </div>
        </div>
      </div>

      {/* Learning Architecture (Roadmap) */}
      <div className="space-y-8">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-primary/10 text-primary">
            <MapIcon size={28} />
          </div>
          <h2 className="text-3xl font-bold">Your Learning Architecture</h2>
        </div>

        <div className="grid grid-cols-1 gap-6">
          {learningPlan.map((plan: any, i: number) => (
            <div key={i} className="group glass p-8 rounded-3xl border border-white/10 hover:border-primary/30 transition-all flex flex-col md:flex-row items-center gap-8">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                <Layout size={32} />
              </div>
              <div className="flex-1 space-y-2 text-center md:text-left">
                <div className="flex flex-wrap justify-center md:justify-start gap-3 items-center">
                  <h4 className="text-xl font-bold">{plan.topic || plan}</h4>
                  <span className="text-[10px] font-bold px-2 py-1 rounded bg-primary/10 text-primary uppercase">
                    High Priority
                  </span>
                </div>
                <p className="text-foreground-muted leading-relaxed max-w-2xl">{plan.description || "Focus area based on assessment performance."}</p>
              </div>
              <div className="flex flex-col items-center md:items-end gap-3">
                <button className="p-3 rounded-xl bg-white/5 border border-white/10 hover:bg-primary hover:text-white hover:border-primary transition-all">
                  <ExternalLink size={20} />
                </button>
              </div>
            </div>
          ))}
          {learningPlan.length === 0 && (
            <div className="text-center p-12 glass rounded-3xl border border-white/10 text-foreground-muted">
              No learning plan generated.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Results;
