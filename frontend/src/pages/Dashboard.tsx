import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FaArrowRight,
  FaSpinner,
  FaCircleCheck,
} from 'react-icons/fa6';
import {
  FiFileText,
  FiActivity,
  FiTarget,
  FiAlertTriangle,
  FiBookOpen,
  FiCheckCircle,
  FiChevronRight,
  FiZap,
  FiAward,
  FiTrendingUp,
} from 'react-icons/fi';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';

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

  const assessedSkillIds = new Set(assessments.map(a => a.skill_name));
  const pendingSkills = skills.filter(s => !assessedSkillIds.has(s.skill_name));
  const unconfiguredPendingSkills = pendingSkills.filter(
    (skill) => !skill.difficulty_configured || !skill.proficiency_claimed,
  );

  const completionPercent = skills.length > 0
    ? Math.floor((completedAssessments.length / skills.length) * 100)
    : 0;

  // ─── Loading state ─────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center">
        <FaSpinner size={48} className="animate-spin text-secondary mb-4" />
        <p className="text-primary/60 font-medium animate-pulse">Loading your dashboard...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-6 py-12 max-w-6xl space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">

      {/* ─── Page Header ─────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="p-4 rounded-2xl bg-secondary-container/20 text-secondary">
            <FiActivity size={32} />
          </div>
          <div>
            <h1 className="text-4xl font-display font-extrabold text-primary tracking-tight">
              Welcome back, {user?.name || 'Student'}
            </h1>
            <p className="text-primary/60 mt-1 font-medium">
              Your skill verification journey is {completionPercent}% complete.
            </p>
          </div>
        </div>
        <button
          onClick={() => navigate('/skills')}
          className="btn-primary flex items-center gap-2"
        >
          Add / Verify Skills <FaArrowRight size={16} />
        </button>
      </div>

      {/* ─── Error Banner ────────────────────────────────────────────────── */}
      {error && (
        <div className="glass p-5 rounded-2xl border-red-500/20 bg-red-50/60 flex items-start gap-3">
          <FiAlertTriangle className="text-red-500 shrink-0 mt-0.5" size={20} />
          <p className="text-red-600 font-semibold text-sm flex-1">{error}</p>
          <button
            onClick={() => setError(null)}
            className="text-red-400 hover:text-red-600 transition-colors font-bold text-lg leading-none"
          >
            ×
          </button>
        </div>
      )}

      {/* ─── Stats Row ───────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            label: 'Total Skills',
            value: skills.length,
            icon: <FiTarget size={20} />,
            color: 'bg-blue-100 text-secondary',
          },
          {
            label: 'Verified',
            value: completedAssessments.length,
            icon: <FiCheckCircle size={20} />,
            color: 'bg-emerald-100 text-emerald-600',
          },
          {
            label: 'Pending',
            value: pendingSkills.length,
            icon: <FiZap size={20} />,
            color: 'bg-amber-100 text-amber-600',
          },
          {
            label: 'Gaps Found',
            value: gaps.length,
            icon: <FiAlertTriangle size={20} />,
            color: 'bg-red-100 text-red-500',
          },
        ].map((stat) => (
          <div
            key={stat.label}
            className="glass p-5 rounded-2xl flex items-center gap-4 hover:shadow-ambient transition-shadow"
          >
            <div className={`p-3 rounded-xl ${stat.color}`}>{stat.icon}</div>
            <div>
              <div className="text-2xl font-display font-extrabold text-primary leading-none">
                {stat.value}
              </div>
              <div className="text-xs font-semibold text-primary/50 uppercase tracking-wider mt-1">
                {stat.label}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ─── Milestone Banner ────────────────────────────────────────────── */}
      <div className="glass rounded-2xl p-6 md:p-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-secondary/8 to-transparent rounded-bl-full -z-[1]" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-emerald-100 text-emerald-600">
              <FiAward size={24} />
            </div>
            <div>
              <div className="text-xs font-bold text-primary/50 uppercase tracking-wider mb-1">
                Academic Rank
              </div>
              <div className="text-2xl font-display font-extrabold text-primary leading-none">
                Level {Math.floor(completedAssessments.length / 3) + 1}
              </div>
            </div>
          </div>

          {/* Progress bar */}
          <div className="flex-1 max-w-sm">
            <div className="flex justify-between text-xs font-semibold text-primary/50 mb-2">
              <span>Verification Progress</span>
              <span>{completionPercent}%</span>
            </div>
            <div className="h-2 w-full bg-primary/5 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-secondary to-emerald rounded-full transition-all duration-700"
                style={{ width: `${completionPercent}%` }}
              />
            </div>
          </div>

          <button
            onClick={() => navigate('/skills')}
            className="text-sm font-bold text-secondary hover:underline flex items-center gap-1 shrink-0"
          >
            View skill profile <FiChevronRight size={16} />
          </button>
        </div>
      </div>

      {/* ─── Two Column Layout ───────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

        {/* ─── LEFT: Recent Assessments ──────────────────────────────────── */}
        <div className="lg:col-span-7 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-display font-extrabold text-primary flex items-center gap-2">
              <FiFileText size={20} className="text-secondary" />
              Recent Assessments
            </h2>
            {assessments.length > 0 && (
              <button
                onClick={() => navigate('/assessment')}
                className="text-xs font-bold text-secondary uppercase tracking-wider hover:underline flex items-center gap-1"
              >
                View All <FiChevronRight size={14} />
              </button>
            )}
          </div>

          {assessments.length === 0 ? (
            <div className="glass p-12 rounded-2xl text-center space-y-4">
              <div className="w-16 h-16 bg-primary/5 rounded-full flex items-center justify-center mx-auto">
                <FiFileText size={28} className="text-primary/30" />
              </div>
              <div className="space-y-1">
                <h3 className="text-lg font-display font-bold text-primary">No assessments yet</h3>
                <p className="text-sm text-primary/60 max-w-xs mx-auto">
                  Generate your first assessment from the skills panel to start verifying your expertise.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {assessments.slice(0, 5).map((item) => (
                <div
                  key={item.assessment_id}
                  onClick={() =>
                    item.status === 'completed'
                      ? navigate(`/results?assessment_id=${item.assessment_id}`)
                      : navigate(`/assessment-test?assessment_id=${item.assessment_id}`)
                  }
                  className="glass p-5 rounded-xl flex items-center justify-between group hover:shadow-ambient hover:-translate-y-0.5 transition-all duration-300 cursor-pointer"
                >
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    {/* Status indicator */}
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                      item.status === 'completed'
                        ? 'bg-emerald-100 text-emerald-600'
                        : 'bg-amber-100 text-amber-600'
                    }`}>
                      {item.status === 'completed'
                        ? <FiCheckCircle size={18} />
                        : <FiZap size={18} />}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="font-bold text-primary group-hover:text-secondary transition-colors truncate">
                        {item.skill_name}
                      </div>
                      <div className="text-xs text-primary/50 font-medium">
                        {item.category}
                      </div>
                    </div>
                  </div>

                  <div className="text-right ml-4 shrink-0">
                    {item.status === 'completed' ? (
                      <div>
                        <div className="text-xl font-display font-extrabold text-primary tabular-nums">
                          {item.score}<span className="text-xs font-semibold text-primary/40">/10</span>
                        </div>
                        <div className="text-[10px] font-bold text-primary/40 uppercase tracking-wider">
                          Verified
                        </div>
                      </div>
                    ) : (
                      <span className="text-xs font-bold text-amber-600 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-200/50">
                        Continue →
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ─── RIGHT: Skills to Verify + Gaps ────────────────────────────── */}
        <div className="lg:col-span-5 space-y-8">

          {/* Pending Skills */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-display font-extrabold text-primary flex items-center gap-2">
                <FiTarget size={20} className="text-secondary" />
                Skills to Verify
              </h2>
              {unconfiguredPendingSkills.length > 0 && (
                <span className="text-[10px] font-bold text-amber-600 bg-amber-50 px-2.5 py-1 rounded-md border border-amber-200/50 uppercase tracking-wider">
                  {unconfiguredPendingSkills.length} need setup
                </span>
              )}
            </div>

            {pendingSkills.length === 0 ? (
              <div className="glass p-10 rounded-2xl text-center space-y-3">
                <div className="w-14 h-14 bg-emerald-100 rounded-full flex items-center justify-center mx-auto">
                  <FaCircleCheck size={24} className="text-emerald-500" />
                </div>
                <p className="font-bold text-primary">All skills verified!</p>
                <p className="text-xs text-primary/50">Great work — keep adding new skills to grow.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {pendingSkills.map((item) => {
                  const isReady = !!item.difficulty_configured && !!item.proficiency_claimed;
                  const isGenerating = generatingFor === item.skill_id;

                  return (
                    <div
                      key={item.id}
                      className="glass p-4 rounded-xl flex items-center justify-between gap-3 hover:shadow-ambient transition-shadow"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="font-bold text-primary truncate text-sm">{item.skill_name}</div>
                        <div className="text-xs text-primary/50">{item.category}</div>
                        {!isReady && (
                          <button
                            onClick={() => navigate('/skills')}
                            className="text-[10px] font-bold text-amber-600 hover:underline mt-0.5 uppercase tracking-wider"
                          >
                            Configure first →
                          </button>
                        )}
                      </div>

                      <button
                        onClick={() => handleGenerateAssessment(item)}
                        disabled={isGenerating || !isReady}
                        className={`px-4 py-2 rounded-lg text-xs font-bold transition-all shrink-0 ${
                          isReady
                            ? 'bg-secondary text-white hover:bg-blue-700 shadow-sm shadow-secondary/20'
                            : 'bg-primary/5 text-primary/40 cursor-not-allowed'
                        }`}
                      >
                        {isGenerating ? (
                          <FaSpinner size={14} className="animate-spin" />
                        ) : (
                          'Assess'
                        )}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Knowledge Gaps */}
          <div className="space-y-4">
            <h2 className="text-xl font-display font-extrabold text-primary flex items-center gap-2">
              <FiTrendingUp size={20} className="text-secondary" />
              Knowledge Gaps
            </h2>

            {gaps.length === 0 ? (
              <div className="glass p-10 rounded-2xl text-center space-y-3">
                <div className="w-14 h-14 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
                  <FiTrendingUp size={24} className="text-secondary" />
                </div>
                <p className="font-bold text-primary">No gaps identified</p>
                <p className="text-xs text-primary/50">Take more assessments to discover growth areas.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {gaps.slice(0, 5).map((item) => (
                  <div
                    key={item.assessment_id}
                    onClick={() => navigate(`/results?assessment_id=${item.assessment_id}`)}
                    className="glass p-4 rounded-xl cursor-pointer group hover:shadow-ambient hover:-translate-y-0.5 transition-all duration-300"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="font-bold text-sm text-primary group-hover:text-secondary transition-colors">
                        {item.skill_name}
                      </div>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-red-50 text-red-500 border border-red-200/50 uppercase tracking-wider">
                        Gap
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs text-primary/50">
                      <span>{item.category}</span>
                      <span className="flex items-center gap-1 text-secondary font-medium">
                        View report <FiChevronRight size={12} />
                      </span>
                    </div>
                  </div>
                ))}

                {gaps.length > 0 && (
                  <button
                    onClick={() => navigate('/learning-plan')}
                    className="w-full p-4 rounded-xl bg-gradient-to-br from-primary to-primary-container text-white text-sm font-bold hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
                  >
                    <FiBookOpen size={16} />
                    View Learning Plans
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
