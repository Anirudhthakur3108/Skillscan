import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FaTrophy, 
  FaArrowRight,
  FaSpinner,
  FaCircleCheck
} from 'react-icons/fa6';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { FiFileText } from 'react-icons/fi';
import { BiTrendingUp } from 'react-icons/bi';

interface Assessment {
  assessment_id: number;
  skill_name: string;
  category: string;
  status: string;
  score: number | null;
  gap_identified: boolean | null;
  created_at: string;
}

interface StudentSkill {
  id: number;
  skill_id: number;
  skill_name: string;
  category: string;
  proficiency_claimed: number | null;
  difficulty_configured: number | null;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [skills, setSkills] = useState<StudentSkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [generatingFor, setGeneratingFor] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      if (!user?.id) return;
      try {
        const [assResponse, skillsResponse] = await Promise.all([
          apiClient.get(`/assessments/student/${user.id}`),
          apiClient.get(`/students/${user.id}/skills`)
        ]);
        setAssessments(assResponse.data.assessments || []);
        setSkills(skillsResponse.data.skills || []);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, [user]);



  const handleGenerateAssessment = async (skill: StudentSkill) => {
    setGeneratingFor(skill.skill_id);
    setError(null);
    try {
      if (!user?.id) {
        setError("User not authenticated");
        setGeneratingFor(null);
        return;
      }

      if (!skill.difficulty_configured || !skill.proficiency_claimed) {
        setError(`Configure difficulty and proficiency for ${skill.skill_name} before assessment.`);
        setGeneratingFor(null);
        return;
      }

      const res = await apiClient.post('/assessments/generate', {
        student_id: user.id,
        skill_id: skill.skill_id,
        difficulty: skill.difficulty_configured,
        proficiency_claimed: skill.proficiency_claimed,
      });
      
      if (res.data.assessment_id) {
        navigate(`/assessment-test?assessment_id=${res.data.assessment_id}`);
      } else {
        setError("Invalid response from server");
      }
    } catch (err: any) {
      console.error("Failed to generate assessment:", err);
      const errorMsg = err.response?.data?.error || err.message || "Failed to generate assessment";
      setError(errorMsg);
    } finally {
      setGeneratingFor(null);
    }
  };

  const completedAssessments = assessments.filter(a => a.status === 'completed');
  const gaps = completedAssessments.filter(a => a.gap_identified);
  
  // Find skills that don't have an assessment yet
  const assessedSkillIds = new Set(assessments.map(a => a.skill_name));
  const pendingSkills = skills.filter(s => !assessedSkillIds.has(s.skill_name));
  const unconfiguredPendingSkills = pendingSkills.filter(
    (skill) => !skill.difficulty_configured || !skill.proficiency_claimed,
  );

  return (
    <div className="py-6 lg:py-12">
      <div className="space-y-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold tracking-tight">Welcome back, {user?.name || 'Student'}</h1>
            <p className="text-foreground-muted font-medium">Your academic verification journey is {Math.floor((completedAssessments.length / (skills.length || 1)) * 100)}% complete.</p>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={() => navigate('/skills')}
              className="px-6 py-3 bg-primary text-white rounded-xl font-bold hover:bg-primary-dark transition-all shadow-lg shadow-primary/20 flex items-center gap-2"
            >
              Add / Verify Skills <FaArrowRight size={18} />
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <FaSpinner className="animate-spin text-primary" size={48} />
          </div>
        ) : (
          <>
            {/* Error Display */}
            {error && (
              <div className="glass p-4 rounded-2xl border border-red-500/20 bg-red-500/5 flex items-start gap-3 mb-6">
                <div className="text-red-500 font-bold">⚠️</div>
                <div className="flex-1">
                  <p className="text-red-400 font-bold text-sm">{error}</p>
                </div>
                <button 
                  onClick={() => setError(null)}
                  className="text-red-500 hover:text-red-400 transition-colors"
                >
                  ✕
                </button>
              </div>
            )}

            {/* Top Row: Stats & Milestone */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2 glass rounded-3xl p-8 border border-white/10 flex flex-col justify-between min-h-[200px] relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl group-hover:bg-primary/10 transition-colors" />
                <div className="space-y-4 relative z-10">
                  <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Verification Milestone</div>
                  <h2 className="text-2xl font-bold max-w-md leading-snug">
                    You have {completedAssessments.length} verified {completedAssessments.length === 1 ? 'skill' : 'skills'} in your professional profile.
                  </h2>
                </div>
                <div className="pt-6 relative z-10">
                  <button 
                    onClick={() => navigate('/skills')}
                    className="text-sm font-bold text-foreground hover:text-primary transition-colors flex items-center gap-2"
                  >
                    View skill profile <FaArrowRight size={14} />
                  </button>
                </div>
              </div>

              <div className="glass rounded-3xl p-8 border border-white/10 flex flex-col justify-between items-center text-center relative overflow-hidden">
                <div className="absolute inset-0 bg-emerald-500/5 opacity-50" />
                <div className="p-4 rounded-2xl bg-emerald-500/10 text-emerald-500 mb-2 relative z-10">
                  <FaTrophy size={32} />
                </div>
                <div className="space-y-1 relative z-10">
                  <div className="text-3xl font-black">Level {Math.floor(completedAssessments.length / 3) + 1}</div>
                  <div className="text-[10px] text-foreground-muted uppercase tracking-[0.2em] font-bold">Academic Rank</div>
                </div>
              </div>
            </div>

            {/* Grid Layout for Recent and Skill Gaps */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
              {/* Recent Assessments */}
              <div className="space-y-8">
                <div className="flex items-center justify-between px-2">
                  <h3 className="text-xl font-bold">Recent Assessments</h3>
                  <button className="text-xs font-bold text-primary uppercase tracking-widest hover:underline">View All</button>
                </div>
                {assessments.length === 0 ? (
                  <div className="glass p-12 rounded-3xl border border-white/5 text-center text-foreground-muted space-y-4">
                    <FiFileText size={40} className="mx-auto opacity-20" />
                    <p className="font-medium">No assessments taken yet.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {assessments.slice(0, 5).map((item) => (
                      <div key={item.assessment_id} className="glass p-6 rounded-2xl border border-white/5 flex items-center justify-between group hover:border-white/20 transition-all cursor-pointer" onClick={() => navigate(`/results?assessment_id=${item.assessment_id}`)}>
                        <div className="space-y-1.5 flex-1">
                          <div className="font-bold group-hover:text-primary transition-colors flex items-center gap-2">
                            {item.skill_name}
                            {item.status !== 'completed' && (
                              <span className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
                            )}
                          </div>
                          <div className="text-xs text-foreground-muted font-medium">{item.category}</div>
                          
                          {item.status !== 'completed' && (
                            <div className="pt-2 pr-12">
                              <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                <div className="h-full bg-yellow-500/50 w-1/3 rounded-full" />
                              </div>
                              <div className="text-[10px] font-bold text-yellow-500/70 mt-1 uppercase tracking-wider">In Progress • 33%</div>
                            </div>
                          )}
                        </div>
                        <div className="text-right ml-4">
                          {item.status === 'completed' ? (
                            <div className="space-y-1">
                              <div className="text-2xl font-black text-primary tabular-nums">{item.score}</div>
                              <div className="text-[10px] font-bold uppercase tracking-tighter opacity-50">Verified Score</div>
                            </div>
                          ) : (
                            <button 
                              onClick={(e) => { e.stopPropagation(); navigate(`/assessment?assessment_id=${item.assessment_id}`); }}
                              className="px-4 py-2 bg-yellow-500/10 text-yellow-500 rounded-lg text-xs font-bold hover:bg-yellow-500/20 transition-all"
                            >
                              Continue
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Right Column: Pending Skills and Gaps */}
              <div className="space-y-12">
                {/* Pending Skills to Assess */}
                <div className="space-y-8">
                  <div className="px-2 space-y-2">
                    <h3 className="text-xl font-bold">Skills to Verify</h3>
                    {unconfiguredPendingSkills.length > 0 && (
                      <p className="text-xs font-bold uppercase tracking-wider text-amber-400">
                        {unconfiguredPendingSkills.length} skills need configuration before assessment.
                      </p>
                    )}
                  </div>
                  {pendingSkills.length === 0 ? (
                    <div className="glass p-12 rounded-3xl border border-white/5 text-center text-foreground-muted space-y-4">
                      <FaCircleCheck size={40} className="mx-auto opacity-20 text-emerald-500" />
                      <p className="font-medium">All skills verified. Well done!</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {pendingSkills.map((item) => (
                        <div key={item.id} className="glass p-6 rounded-2xl border border-white/5 flex items-center justify-between group hover:border-white/20 transition-all">
                          <div className="space-y-1">
                            <div className="font-bold group-hover:text-primary transition-colors">{item.skill_name}</div>
                            <div className="text-xs text-foreground-muted font-medium">{item.category}</div>
                            {(!item.difficulty_configured || !item.proficiency_claimed) && (
                              <div className="text-[10px] font-bold uppercase tracking-wider text-amber-400">
                                Difficulty and proficiency setup required
                              </div>
                            )}
                          </div>
                          <div className="text-right">
                            <button 
                              onClick={() => handleGenerateAssessment(item)}
                              disabled={generatingFor === item.skill_id || !item.difficulty_configured || !item.proficiency_claimed}
                              className="px-5 py-2.5 bg-primary/10 text-primary rounded-xl text-sm font-bold hover:bg-primary text-white transition-all disabled:opacity-50 disabled:hover:bg-primary/10 disabled:hover:text-primary shadow-sm"
                            >
                              {generatingFor === item.skill_id ? <FaSpinner size={16} className="animate-spin inline" /> : 'Assess Now'}
                            </button>
                            {(!item.difficulty_configured || !item.proficiency_claimed) && (
                              <button
                                onClick={() => navigate('/skills')}
                                className="block mt-2 text-[10px] font-bold uppercase tracking-wider text-amber-400 hover:underline"
                              >
                                Configure Skill
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Identified Skill Gaps */}
                <div className="space-y-8">
                  <h3 className="text-xl font-bold px-2">Knowledge Gaps</h3>
                  {gaps.length === 0 ? (
                    <div className="glass p-12 rounded-3xl border border-white/5 text-center text-foreground-muted space-y-4">
                      <BiTrendingUp size={40} className="mx-auto opacity-20" />
                      <p className="font-medium">No gaps identified. Keep it up!</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {gaps.slice(0, 5).map((item) => (
                        <div key={item.assessment_id} className="glass p-6 rounded-2xl border border-white/5 space-y-4 hover:border-primary/20 transition-all cursor-pointer group" onClick={() => navigate(`/results?assessment_id=${item.assessment_id}`)}>
                          <div className="flex items-center justify-between">
                            <div className="font-bold group-hover:text-primary transition-colors">{item.skill_name}</div>
                            <div className="text-[10px] font-bold px-2 py-1 rounded bg-red-500/10 text-red-400 uppercase tracking-wider">Improvement Area</div>
                          </div>
                          <div className="flex items-center justify-between bg-white/5 p-4 rounded-2xl border border-white/5 group-hover:bg-white/10 transition-colors">
                            <div className="text-sm w-full">
                              <span className="text-foreground-muted block text-[10px] font-bold uppercase tracking-widest mb-2 opacity-60">AI Insight</span>
                              <span className="font-medium text-sm line-clamp-2 leading-relaxed italic">
                                {item.gap_identified ? "Gap identified from latest assessment" : "No gap identified"}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Dashboard;

