import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { FaCircleExclamation, FaBolt, FaArrowUpRightFromSquare, FaSpinner, FaShieldHalved, FaMap, FaTable } from 'react-icons/fa6';
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

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <FaSpinner size={48} className="animate-spin text-primary" />
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
  const overallScore = aiFeedback.overall_score || aiFeedback.score || 0;
  const selectedProficiency = aiFeedback.selected_proficiency;
  const performanceGap = aiFeedback.performance_gap;
  const mcqFeedback = aiFeedback.mcq_feedback || {};
  const longAnswerFeedback = aiFeedback.long_answer_feedback || {};
  const caseStudyFeedback = aiFeedback.case_study_feedback || {};
  const identifiedGaps = aiFeedback.identified_gaps || [];
  
  // For backwards compatibility (unused arrays removed to avoid TS no-unused errors)

  return (
    <div className="container mx-auto px-6 py-12 max-w-5xl space-y-16">
      {/* Hero Result Section */}
      <div className="glass rounded-[3rem] p-12 lg:p-16 border border-white/20 shadow-2xl relative overflow-hidden text-center lg:text-left">
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary/20 rounded-full blur-[120px] -mr-48 -mt-48" />
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6 relative z-10">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-bold border border-primary/20">
              <FaShieldHalved size={18} />
              Skill Validation Report
            </div>
            <h1 className="text-4xl lg:text-5xl font-bold">{assessment.skill_name || 'Assessment'} Results</h1>
            <p className="text-xl text-foreground-muted leading-relaxed">
              Based on our AI-driven assessment, your technical capabilities have been successfully evaluated.
            </p>
            <div className="flex gap-4">
              <button 
                onClick={() => navigate('/assessment')}
                className="px-6 py-3 rounded-xl bg-primary text-white font-bold shadow-lg shadow-primary/20 hover:scale-105 transition-all"
              >
                Back to Assessments
              </button>
              <button 
                onClick={() => navigate('/dashboard')}
                className="px-6 py-3 rounded-xl bg-white/5 border border-white/10 font-bold hover:bg-white/10 transition-colors"
              >
                Dashboard
              </button>
            </div>
          </div>
          
          <div className="relative z-10 flex flex-col items-center justify-center p-8 glass rounded-3xl border border-white/10 aspect-square">
            <div className="text-8xl font-black text-primary mb-2">{overallScore}</div>
            <div className="text-lg font-bold uppercase tracking-widest text-foreground-muted">Overall Score</div>
            <div className="mt-8 h-2 w-full bg-white/5 rounded-full overflow-hidden">
              <div className="h-full bg-primary rounded-full shadow-[0_0_15px_rgba(16,185,129,0.4)] transition-all" style={{ width: `${overallScore * 10}%` }} />
            </div>
          </div>
        </div>
      </div>

      {(typeof selectedProficiency === 'number' || typeof performanceGap === 'number') && (
        <div className="glass p-6 rounded-2xl border border-white/10">
          <h3 className="text-xl font-bold mb-3">Calibration Insight</h3>
          <p className="text-sm text-foreground-muted">
            Target proficiency: <span className="font-bold text-primary">{selectedProficiency ?? 'N/A'}/10</span>.
            Performance gap: <span className="font-bold text-primary"> {performanceGap ?? 0}</span> points.
          </p>
        </div>
      )}

      {/* Score Breakdown */}
      {mcqFeedback && mcqFeedback.total && (
        <div className="space-y-8">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-primary/10 text-primary">
              <FaTable size={28} />
            </div>
            <h2 className="text-3xl font-bold">Score Breakdown</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="glass p-8 rounded-3xl border border-white/10 space-y-4">
              <h3 className="text-xl font-bold">MCQ Performance</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-foreground-muted">Correct Answers:</span>
                  <span className="text-2xl font-bold text-primary">{mcqFeedback.correct}/{mcqFeedback.total}</span>
                </div>
                <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-primary rounded-full" style={{ width: `${mcqFeedback.percentage}%` }} />
                </div>
                <div className="text-sm text-foreground-muted text-center">
                  {mcqFeedback.percentage}% Success Rate
                </div>
              </div>
            </div>

            {longAnswerFeedback && (
              <div className="glass p-8 rounded-3xl border border-white/10 space-y-4">
                <h3 className="text-xl font-bold">Coding Challenge</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-foreground-muted">Score:</span>
                    <span className="text-2xl font-bold text-primary">{longAnswerFeedback.score || 'N/A'}/10</span>
                  </div>
                  {longAnswerFeedback.feedback && (
                    <p className="text-sm text-foreground-muted">{longAnswerFeedback.feedback}</p>
                  )}
                </div>
              </div>
            )}

            {caseStudyFeedback && (
              <div className="glass p-8 rounded-3xl border border-white/10 space-y-4">
                <h3 className="text-xl font-bold">Case Study</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-foreground-muted">Score:</span>
                    <span className="text-2xl font-bold text-primary">{caseStudyFeedback.score || 'N/A'}/10</span>
                  </div>
                  {caseStudyFeedback.feedback && (
                    <p className="text-sm text-foreground-muted">{caseStudyFeedback.feedback}</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Identified Gaps */}
      {identifiedGaps && identifiedGaps.length > 0 && (
        <div className="space-y-8">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-amber-500/10 text-amber-400">
              <FaCircleExclamation size={28} />
            </div>
            <h2 className="text-3xl font-bold">Identified Skill Gaps</h2>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {identifiedGaps.map((gap: any, i: number) => (
              <div key={i} className={`glass p-6 rounded-2xl border ${gap.severity === 'high' ? 'border-red-500/20 bg-red-500/5' : gap.severity === 'medium' ? 'border-amber-500/20 bg-amber-500/5' : 'border-yellow-500/20 bg-yellow-500/5'}`}>
                <div className="flex items-start gap-4">
                  <div className={`p-2 rounded-lg ${gap.severity === 'high' ? 'bg-red-500/20 text-red-400' : gap.severity === 'medium' ? 'bg-amber-500/20 text-amber-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                    <span className="text-xs font-bold uppercase tracking-wider">{gap.severity}</span>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-bold text-lg">{gap.gap_name}</h4>
                    <p className="text-sm text-foreground-muted mt-1">{gap.reason}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reassessment Gate */}
      {assessment?.status === 'completed' && (
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-400">
              <FaBolt size={28} />
            </div>
            <h2 className="text-3xl font-bold">Reassessment Readiness</h2>
          </div>

          <div className="glass p-8 rounded-3xl border border-white/10 space-y-5">
            <label className="flex items-center gap-3 text-sm font-medium">
              <input
                type="checkbox"
                checked={studyCompleted}
                onChange={async (event) => {
                  const checked = event.target.checked;
                  setStudyCompleted(checked);
                  await fetchReassessmentEligibility(checked);
                }}
                className="w-4 h-4 rounded cursor-pointer"
              />
              I completed the recommended study plan and want to request early reassessment
            </label>

            {isCheckingEligibility ? (
              <div className="flex items-center gap-2 text-sm text-foreground-muted">
                <FaSpinner className="animate-spin" />
                Checking reassessment eligibility...
              </div>
            ) : (
              reassessmentEligibility && (
                <div className={`p-4 rounded-xl border ${reassessmentEligibility.eligible ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-amber-500/20 bg-amber-500/5'}`}>
                  <p className={`font-bold ${reassessmentEligibility.eligible ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {reassessmentEligibility.eligible ? 'Eligible for reassessment' : 'Not yet eligible'}
                  </p>
                  <p className="text-sm text-foreground-muted mt-1">{reassessmentEligibility.reason}</p>
                  {reassessmentEligibility.next_eligible_at && (
                    <p className="text-xs text-foreground-muted mt-2">
                      Next cooldown eligibility: {new Date(reassessmentEligibility.next_eligible_at).toLocaleString()}
                    </p>
                  )}
                </div>
              )
            )}

            <button
              onClick={handleStartReassessment}
              disabled={isStartingReassessment || !reassessmentEligibility?.eligible}
              className="w-full md:w-auto px-6 py-3 rounded-xl bg-blue-500 text-white font-bold hover:bg-blue-600 transition-colors disabled:opacity-50"
            >
              {isStartingReassessment ? 'Starting reassessment...' : 'Start Reassessment'}
            </button>
          </div>
        </div>
      )}

      {/* Learning Architecture (Roadmap) */}
      {assessment?.ai_feedback?.gap_identified && (
        <div className="space-y-8">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-primary/10 text-primary">
              <FaMap size={28} />
            </div>
            <h2 className="text-3xl font-bold">Your Learning Architecture</h2>
          </div>

          {!learningPlanData ? (
            <button
              onClick={handleGenerateLearningPlan}
              disabled={isGeneratingPlan || !skillScoreId}
              className="w-full px-8 py-6 rounded-2xl bg-primary text-white font-bold shadow-lg shadow-primary/20 hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 transition-all flex items-center justify-center gap-2"
            >
              {isGeneratingPlan ? (
                <>
                  <FaSpinner className="animate-spin" size={20} />
                  Generating Personalized Plan...
                </>
              ) : (
                <>
                  <FaMap size={20} />
                  Generate Your Learning Plan
                </>
              )}
            </button>
          ) : (
            <div className="space-y-8">
              <div className="glass p-8 rounded-3xl border border-white/10">
                <h3 className="text-2xl font-bold mb-4">{learningPlanData.skill_name}</h3>
                <p className="text-foreground-muted leading-relaxed mb-4">{learningPlanData.summary}</p>
                <div className="flex items-center gap-4">
                  <div className="text-sm font-bold">
                    <span className="text-primary text-lg">{learningPlanData.total_weeks}</span> weeks
                  </div>
                </div>
              </div>

              {/* Learning Phases */}
              {learningPlanData.plan?.phases && learningPlanData.plan.phases.map((phase: any, phaseIdx: number) => (
                <div key={phaseIdx} className="space-y-4">
                  <div className="glass p-8 rounded-3xl border border-white/10">
                    <h4 className="text-2xl font-bold mb-2">Phase {phase.phase_number}: {phase.title}</h4>
                    <p className="text-foreground-muted mb-4">{phase.description}</p>
                    <div className="text-sm font-bold text-primary mb-4">Duration: {phase.timeline_weeks || phase.duration_weeks} weeks</div>

                    {/* YouTube Resources */}
                    {phase.youtube_resources && phase.youtube_resources.length > 0 && (
                      <div className="mb-6">
                        <h5 className="font-bold text-lg mb-3 flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-primary"></span>
                          Video Resources
                        </h5>
                        <div className="grid gap-3">
                          {phase.youtube_resources.map((video: any, idx: number) => (
                            <a
                              key={idx}
                              href={video.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-primary/50 transition-all flex items-start justify-between gap-4 group"
                            >
                              <div className="flex-1">
                                <p className="font-bold group-hover:text-primary transition-colors">{video.title}</p>
                                <p className="text-xs text-foreground-muted mt-1">{video.duration_minutes} minutes</p>
                              </div>
                              <FaArrowUpRightFromSquare className="text-foreground-muted group-hover:text-primary transition-colors flex-shrink-0 mt-1" />
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Website Resources */}
                    {phase.website_resources && phase.website_resources.length > 0 && (
                      <div>
                        <h5 className="font-bold text-lg mb-3 flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-primary"></span>
                          Study Materials
                        </h5>
                        <div className="grid gap-3">
                          {phase.website_resources.map((resource: any, idx: number) => (
                            <a
                              key={idx}
                              href={resource.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-primary/50 transition-all flex items-start justify-between gap-4 group"
                            >
                              <div className="flex-1">
                                <p className="font-bold group-hover:text-primary transition-colors">{resource.title}</p>
                                <p className="text-xs text-foreground-muted mt-1">
                                  {resource.category} • {resource.estimated_hours} hours
                                </p>
                              </div>
                              <FaArrowUpRightFromSquare className="text-foreground-muted group-hover:text-primary transition-colors flex-shrink-0 mt-1" />
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Milestones */}
                    {phase.milestones && phase.milestones.length > 0 && (
                      <div className="mt-6 pt-6 border-t border-white/10">
                        <h5 className="font-bold text-lg mb-3">Milestones</h5>
                        <ul className="space-y-2">
                          {phase.milestones.map((milestone: string, idx: number) => (
                            <li key={idx} className="flex items-center gap-3 text-sm text-foreground-muted">
                              <input type="checkbox" className="w-4 h-4 rounded cursor-pointer" />
                              {milestone}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Results;

