import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  FaSpinner,
} from 'react-icons/fa6';
import {
  FiAlertTriangle,
  FiAward,
  FiBarChart2,
  FiBookOpen,
  FiCheckCircle,
  FiChevronRight,
  FiRefreshCw,
  FiShield,
  FiTarget,
  FiTrendingUp,
  FiMap,
} from 'react-icons/fi';
import apiClient from '../api/client';

const Results: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const assessmentId = searchParams.get('assessment_id');

  const [assessment, setAssessment] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [learningPlanData] = useState<any>(null);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
  const [skillScoreId, setSkillScoreId] = useState<number | null>(null);
  const [studyCompleted, setStudyCompleted] = useState(false);
  const [reassessmentEligibility, setReassessmentEligibility] = useState<any>(null);
  const [isCheckingEligibility, setIsCheckingEligibility] = useState(false);
  const [isStartingReassessment, setIsStartingReassessment] = useState(false);

  const fetchReassessmentEligibility = async (studyCompletionFlag: boolean) => {
    if (!assessmentId) return;
    setIsCheckingEligibility(true);
    try {
      const response = await apiClient.get(`/assessments/${assessmentId}/reassessment-eligibility`, {
        params: {
          study_completed: studyCompletionFlag,
        },
      });
      setReassessmentEligibility(response.data);
    } catch (err) {
      console.error('Failed to fetch reassessment eligibility:', err);
    } finally {
      setIsCheckingEligibility(false);
    }
  };

  useEffect(() => {
    if (!assessmentId) {
      setError("No assessment ID provided.");
      setIsLoading(false);
      return;
    }

    const fetchResults = async () => {
      try {
        const response = await apiClient.get(`/assessments/${assessmentId}`);
        const data = response.data;
        setAssessment(data);
        if (data?.status === 'completed') {
          await fetchReassessmentEligibility(false);
        }

        // Prefer server-provided skill_score_id when available
        if (data.skill_score_id) {
          setSkillScoreId(data.skill_score_id);
          localStorage.setItem(`skillScoreId_${assessmentId}`, data.skill_score_id.toString());
        }

        // Get skill_score_id from localStorage
        const storedSkillScoreId = localStorage.getItem(`skillScoreId_${assessmentId}`);
        if (!data.skill_score_id && storedSkillScoreId) {
          setSkillScoreId(parseInt(storedSkillScoreId));
        }
      } catch (err) {
        console.error("Failed to load assessment results:", err);
        setError("Failed to load assessment results.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchResults();
  }, [assessmentId]);

  const handleStartReassessment = async () => {
    if (!assessmentId) return;
    setError(null);
    setIsStartingReassessment(true);
    try {
      const response = await apiClient.post(`/assessments/${assessmentId}/reassess`, {
        study_completed: studyCompleted,
      });
      const nextAssessmentId = response.data?.assessment_id;
      if (!nextAssessmentId) {
        setError('Reassessment was created but no assessment id was returned.');
        return;
      }
      navigate(`/assessment-test?assessment_id=${nextAssessmentId}`);
    } catch (err: any) {
      const message = err.response?.data?.error || 'Unable to start reassessment right now.';
      setError(message);
      await fetchReassessmentEligibility(studyCompleted);
    } finally {
      setIsStartingReassessment(false);
    }
  };

  const handleGenerateLearningPlan = async () => {
    if (!skillScoreId) {
      setError("Skill score information not available.");
      return;
    }

    setIsGeneratingPlan(true);
    try {
      const response = await apiClient.post('/learning-plan/generate', {
        skill_score_id: skillScoreId
      });

      // Navigate to persistent Learning Plan page with created plan id (or existing plan id)
      const planId = response.data?.learning_plan_id;
      if (planId) {
        navigate(`/learning-plan?plan_id=${planId}`);
        return;
      }

      // Fallback: if no plan id returned but plan object exists, store it locally and navigate
      if (response.data?.plan) {
        localStorage.setItem(`__last_plan_${skillScoreId}`, JSON.stringify(response.data.plan));
        navigate(`/learning-plan`);
        return;
      }

      setError('Learning plan generation succeeded but no plan identifier was returned.');
    } catch (err: any) {
      console.error("Failed to generate learning plan:", err);
      setError(err.response?.data?.error || "Failed to generate learning plan. Please try again.");
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  // ─── Loading state ──────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center">
        <FaSpinner size={48} className="animate-spin text-secondary mb-4" />
        <p className="text-primary/60 font-medium animate-pulse">Loading results...</p>
      </div>
    );
  }

  // ─── Error / not found state ────────────────────────────────────────────────
  if (error && !assessment) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <div className="card-tonal max-w-md text-center space-y-4">
          <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mx-auto">
            <FiAlertTriangle size={24} className="text-red-500" />
          </div>
          <h2 className="text-xl font-display font-bold text-primary">Something went wrong</h2>
          <p className="text-primary/60 text-sm">{error}</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="btn-secondary"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!assessment) return null;

  const aiFeedback = assessment.ai_feedback || {};
  const overallScore = aiFeedback.overall_score || aiFeedback.score || 0;
  const selectedProficiency = aiFeedback.selected_proficiency;
  const performanceGap = aiFeedback.performance_gap;
  const mcqFeedback = aiFeedback.mcq_feedback || {};
  const longAnswerFeedback = aiFeedback.long_answer_feedback || {};
  const caseStudyFeedback = aiFeedback.case_study_feedback || {};
  const identifiedGaps = aiFeedback.identified_gaps || [];

  /** Score color helper */
  const scoreColor = (score: number) => {
    if (score >= 8) return 'text-emerald-600';
    if (score >= 5) return 'text-amber-600';
    return 'text-red-500';
  };

  const progressColor = (score: number) => {
    if (score >= 8) return 'bg-emerald';
    if (score >= 5) return 'bg-amber-500';
    return 'bg-red-500';
  };

  return (
    <div className="container mx-auto px-6 py-12 max-w-5xl space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">

      {/* ─── Error Banner ────────────────────────────────────────────────── */}
      {error && (
        <div className="glass p-4 rounded-xl border-red-200/50 bg-red-50/60 flex items-start gap-3">
          <FiAlertTriangle className="text-red-500 shrink-0 mt-0.5" size={18} />
          <p className="text-red-600 font-semibold text-sm flex-1">{error}</p>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 font-bold text-lg leading-none">×</button>
        </div>
      )}

      {/* ─── Hero Result Card ────────────────────────────────────────────── */}
      <div className="glass rounded-2xl p-8 md:p-10 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-secondary/8 to-transparent rounded-bl-full -z-[1]" />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
          {/* Left: Info */}
          <div className="lg:col-span-2 space-y-5">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-secondary-container/20 text-secondary text-xs font-bold uppercase tracking-wider">
              <FiShield size={14} />
              Skill Validation Report
            </div>
            <h1 className="text-3xl lg:text-4xl font-display font-extrabold text-primary tracking-tight">
              {assessment.skill_name || 'Assessment'} Results
            </h1>
            <p className="text-primary/60 text-lg leading-relaxed max-w-lg">
              Based on our AI-driven assessment, your capabilities have been evaluated and scored.
            </p>
            <div className="flex flex-wrap gap-3 pt-2">
              <button
                onClick={() => navigate('/assessment')}
                className="btn-primary flex items-center gap-2 text-sm"
              >
                Back to Assessments
              </button>
              <button
                onClick={() => navigate('/dashboard')}
                className="px-5 py-3 rounded-md border border-outline-variant text-primary font-semibold hover:bg-surface-container-low transition-colors text-sm"
              >
                Dashboard
              </button>
            </div>
          </div>

          {/* Right: Score circle */}
          <div className="flex flex-col items-center justify-center p-8 glass rounded-2xl aspect-square max-w-[200px] mx-auto lg:mx-0 lg:ml-auto">
            <div className={`text-7xl font-display font-extrabold ${scoreColor(overallScore)} leading-none`}>
              {overallScore}
            </div>
            <div className="text-xs font-bold text-primary/50 uppercase tracking-wider mt-2">
              Overall Score
            </div>
            <div className="mt-5 h-2 w-full bg-primary/5 rounded-full overflow-hidden">
              <div
                className={`h-full ${progressColor(overallScore)} rounded-full transition-all duration-700`}
                style={{ width: `${overallScore * 10}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* ─── Calibration Insight ──────────────────────────────────────────── */}
      {(typeof selectedProficiency === 'number' || typeof performanceGap === 'number') && (
        <div className="glass p-5 rounded-xl flex items-center gap-4">
          <div className="p-2.5 rounded-lg bg-blue-100 text-secondary">
            <FiTarget size={20} />
          </div>
          <div>
            <div className="text-xs font-bold text-primary/50 uppercase tracking-wider mb-0.5">Calibration Insight</div>
            <p className="text-sm text-primary/70 font-medium">
              Target proficiency: <span className="font-bold text-primary">{selectedProficiency ?? 'N/A'}/10</span>.
              {' '}Performance gap: <span className="font-bold text-primary">{performanceGap ?? 0}</span> points.
            </p>
          </div>
        </div>
      )}

      {/* ─── Score Breakdown ──────────────────────────────────────────────── */}
      {mcqFeedback && mcqFeedback.total && (
        <div className="space-y-6">
          <h2 className="text-2xl font-display font-extrabold text-primary flex items-center gap-3">
            <FiBarChart2 size={22} className="text-secondary" />
            Score Breakdown
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* MCQ */}
            <div className="glass p-6 rounded-2xl space-y-4 hover:shadow-ambient transition-shadow">
              <h3 className="font-display font-bold text-primary text-lg">MCQ Performance</h3>
              <div className="flex items-baseline justify-between">
                <span className="text-primary/60 text-sm font-medium">Correct Answers</span>
                <span className="text-2xl font-display font-extrabold text-primary">
                  {mcqFeedback.correct}<span className="text-sm font-semibold text-primary/40">/{mcqFeedback.total}</span>
                </span>
              </div>
              <div className="h-2 bg-primary/5 rounded-full overflow-hidden">
                <div className="h-full bg-secondary rounded-full transition-all duration-700" style={{ width: `${mcqFeedback.percentage}%` }} />
              </div>
              <div className="text-xs font-semibold text-primary/50 text-center">
                {mcqFeedback.percentage}% Success Rate
              </div>
            </div>

            {/* Coding / Writing */}
            {longAnswerFeedback && (
              <div className="glass p-6 rounded-2xl space-y-4 hover:shadow-ambient transition-shadow">
                <h3 className="font-display font-bold text-primary text-lg">
                  {assessment.category_type === 'soft_skill' ? 'Writing Task' :
                   assessment.category_type === 'domain' ? 'Analytical Task' :
                   assessment.category_type === 'tool' ? 'Workflow Task' : 'Coding Challenge'}
                </h3>
                <div className="flex items-baseline justify-between">
                  <span className="text-primary/60 text-sm font-medium">Score</span>
                  <span className={`text-2xl font-display font-extrabold ${scoreColor(longAnswerFeedback.score || 0)}`}>
                    {longAnswerFeedback.score || 'N/A'}<span className="text-sm font-semibold text-primary/40">/10</span>
                  </span>
                </div>
                {longAnswerFeedback.feedback && (
                  <p className="text-sm text-primary/60 leading-relaxed">{longAnswerFeedback.feedback}</p>
                )}
              </div>
            )}

            {/* Case Study */}
            {caseStudyFeedback && (
              <div className="glass p-6 rounded-2xl space-y-4 hover:shadow-ambient transition-shadow">
                <h3 className="font-display font-bold text-primary text-lg">
                  {assessment.category_type === 'soft_skill' ? 'Behavioral Scenario' :
                   assessment.category_type === 'domain' ? 'Strategic Case Study' :
                   assessment.category_type === 'tool' ? 'Integration Scenario' : 'Case Study'}
                </h3>
                <div className="flex items-baseline justify-between">
                  <span className="text-primary/60 text-sm font-medium">Score</span>
                  <span className={`text-2xl font-display font-extrabold ${scoreColor(caseStudyFeedback.score || 0)}`}>
                    {caseStudyFeedback.score || 'N/A'}<span className="text-sm font-semibold text-primary/40">/10</span>
                  </span>
                </div>
                {caseStudyFeedback.feedback && (
                  <p className="text-sm text-primary/60 leading-relaxed">{caseStudyFeedback.feedback}</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─── Identified Gaps ─────────────────────────────────────────────── */}
      {identifiedGaps && identifiedGaps.length > 0 && (
        <div className="space-y-5">
          <h2 className="text-2xl font-display font-extrabold text-primary flex items-center gap-3">
            <FiAlertTriangle size={22} className="text-amber-500" />
            Identified Skill Gaps
          </h2>

          <div className="space-y-3">
            {identifiedGaps.map((gap: any, i: number) => {
              const severityStyles = {
                high: 'bg-red-50 border-red-200/50',
                medium: 'bg-amber-50 border-amber-200/50',
                low: 'bg-yellow-50 border-yellow-200/50',
              } as Record<string, string>;
              const badgeStyles = {
                high: 'bg-red-100 text-red-600',
                medium: 'bg-amber-100 text-amber-600',
                low: 'bg-yellow-100 text-yellow-600',
              } as Record<string, string>;

              return (
                <div key={i} className={`p-5 rounded-xl border ${severityStyles[gap.severity] || severityStyles.low}`}>
                  <div className="flex items-start gap-4">
                    <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md shrink-0 ${badgeStyles[gap.severity] || badgeStyles.low}`}>
                      {gap.severity}
                    </span>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-display font-bold text-primary text-base">{gap.gap_name}</h4>
                      <p className="text-sm text-primary/60 mt-1 leading-relaxed">{gap.reason}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ─── Reassessment Gate ───────────────────────────────────────────── */}
      {assessment?.status === 'completed' && (
        <div className="space-y-5">
          <h2 className="text-2xl font-display font-extrabold text-primary flex items-center gap-3">
            <FiRefreshCw size={22} className="text-secondary" />
            Reassessment Readiness
          </h2>

          <div className="glass p-6 rounded-2xl space-y-5">
            <label className="flex items-center gap-3 text-sm font-medium text-primary/80 cursor-pointer">
              <input
                type="checkbox"
                checked={studyCompleted}
                onChange={async (event) => {
                  const checked = event.target.checked;
                  setStudyCompleted(checked);
                  await fetchReassessmentEligibility(checked);
                }}
                className="w-4 h-4 rounded border-primary/20 text-secondary focus:ring-secondary/30 cursor-pointer"
              />
              I completed the recommended study plan and want to request early reassessment
            </label>

            {isCheckingEligibility ? (
              <div className="flex items-center gap-2 text-sm text-primary/50">
                <FaSpinner className="animate-spin" />
                Checking reassessment eligibility...
              </div>
            ) : (
              reassessmentEligibility && (
                <div className={`p-4 rounded-xl border ${
                  reassessmentEligibility.eligible
                    ? 'border-emerald/20 bg-emerald-50'
                    : 'border-amber-200/50 bg-amber-50'
                }`}>
                  <div className="flex items-center gap-2 mb-1">
                    {reassessmentEligibility.eligible
                      ? <FiCheckCircle className="text-emerald-600" size={16} />
                      : <FiAlertTriangle className="text-amber-600" size={16} />}
                    <p className={`font-bold text-sm ${
                      reassessmentEligibility.eligible ? 'text-emerald-700' : 'text-amber-700'
                    }`}>
                      {reassessmentEligibility.eligible ? 'Eligible for reassessment' : 'Not yet eligible'}
                    </p>
                  </div>
                  <p className="text-sm text-primary/60 ml-6">{reassessmentEligibility.reason}</p>
                  {reassessmentEligibility.next_eligible_at && (
                    <p className="text-xs text-primary/40 mt-2 ml-6">
                      Next cooldown eligibility: {new Date(reassessmentEligibility.next_eligible_at).toLocaleString()}
                    </p>
                  )}
                </div>
              )
            )}

            <button
              onClick={handleStartReassessment}
              disabled={isStartingReassessment || !reassessmentEligibility?.eligible}
              className="btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isStartingReassessment ? (
                <><FaSpinner className="animate-spin" size={16} /> Starting...</>
              ) : (
                <><FiRefreshCw size={16} /> Start Reassessment</>
              )}
            </button>
          </div>
        </div>
      )}

      {/* ─── Learning Plan CTA ───────────────────────────────────────────── */}
      {assessment?.ai_feedback?.gap_identified && (
        <div className="space-y-5">
          <h2 className="text-2xl font-display font-extrabold text-primary flex items-center gap-3">
            <FiMap size={22} className="text-secondary" />
            Your Learning Architecture
          </h2>

          {!learningPlanData ? (
            <button
              onClick={handleGenerateLearningPlan}
              disabled={isGeneratingPlan || !skillScoreId}
              className="w-full p-6 glass rounded-2xl hover:shadow-ambient transition-all flex items-center justify-center gap-3 group disabled:opacity-50"
            >
              {isGeneratingPlan ? (
                <>
                  <FaSpinner className="animate-spin text-secondary" size={20} />
                  <span className="font-bold text-primary">Generating Personalized Plan...</span>
                </>
              ) : (
                <>
                  <div className="p-3 rounded-xl bg-secondary-container/20 text-secondary group-hover:scale-110 transition-transform">
                    <FiBookOpen size={24} />
                  </div>
                  <div className="text-left">
                    <div className="font-display font-bold text-primary text-lg">Generate Your Learning Plan</div>
                    <div className="text-sm text-primary/50">Get a personalized roadmap to bridge your skill gaps</div>
                  </div>
                  <FiChevronRight size={20} className="text-primary/30 ml-auto" />
                </>
              )}
            </button>
          ) : (
            <div className="glass p-8 rounded-2xl space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-100 text-emerald-600">
                  <FiAward size={20} />
                </div>
                <h3 className="text-xl font-display font-bold text-primary">{learningPlanData.skill_name}</h3>
              </div>
              <p className="text-primary/60 leading-relaxed">{learningPlanData.summary}</p>
              <div className="flex items-center gap-2 text-sm">
                <span className="font-bold text-primary text-lg">{learningPlanData.total_weeks}</span>
                <span className="text-primary/50 font-medium">weeks estimated</span>
              </div>
              <button
                onClick={() => navigate('/learning-plan')}
                className="btn-primary flex items-center gap-2 text-sm mt-4"
              >
                <FiBookOpen size={16} /> View Full Plan
              </button>
            </div>
          )}
        </div>
      )}

      {/* ─── Quick Actions ───────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          onClick={() => navigate('/learning-plan')}
          className="glass p-5 rounded-xl hover:shadow-ambient transition-all flex items-center gap-4 text-left group"
        >
          <div className="p-3 rounded-xl bg-emerald-100 text-emerald-600 group-hover:scale-110 transition-transform">
            <FiBookOpen size={20} />
          </div>
          <div>
            <div className="font-display font-bold text-primary">Learning Plans</div>
            <div className="text-xs text-primary/50">View all your personalized roadmaps</div>
          </div>
          <FiChevronRight size={18} className="text-primary/30 ml-auto" />
        </button>
        <button
          onClick={() => navigate('/assessment')}
          className="glass p-5 rounded-xl hover:shadow-ambient transition-all flex items-center gap-4 text-left group"
        >
          <div className="p-3 rounded-xl bg-blue-100 text-secondary group-hover:scale-110 transition-transform">
            <FiTrendingUp size={20} />
          </div>
          <div>
            <div className="font-display font-bold text-primary">All Assessments</div>
            <div className="text-xs text-primary/50">Review your verification history</div>
          </div>
          <FiChevronRight size={18} className="text-primary/30 ml-auto" />
        </button>
      </div>
    </div>
  );
};

export default Results;
