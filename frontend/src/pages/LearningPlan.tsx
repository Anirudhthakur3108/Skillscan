import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import { FaSpinner, FaExternalLinkAlt, FaMap, FaPlayCircle, FaBookOpen, FaCheckCircle, FaRegClock, FaCalendarAlt } from 'react-icons/fa';

const LearningPlan: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();

  const planIdFromUrl = searchParams.get('plan_id');
  const [plans, setPlans] = useState<any[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [planDetail, setPlanDetail] = useState<any | null>(null);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      navigate('/auth');
      return;
    }

    const loadPlansList = async () => {
      setIsLoadingList(true);
      try {
        const listResp = await apiClient.get(`/learning-plan/student/${user.id}`);
        const plansList = listResp.data.learning_plans || [];
        setPlans(plansList);
        setError(null);

        if (planIdFromUrl) {
          setSelectedPlanId(parseInt(planIdFromUrl));
        } else if (plansList.length > 0) {
          setSelectedPlanId(plansList[0].learning_plan_id);
        }
      } catch (err: any) {
        console.error('Failed to load plans:', err);
        setError(err.response?.data?.error || 'Failed to load learning plans.');
      } finally {
        setIsLoadingList(false);
      }
    };

    loadPlansList();
  }, [user, authLoading, navigate, planIdFromUrl]);

  useEffect(() => {
    if (!selectedPlanId) return;

    const loadPlanDetail = async () => {
      setIsLoadingDetail(true);
      setPlanDetail(null);
      try {
        const resp = await apiClient.get(`/learning-plan/${selectedPlanId}`);
        setPlanDetail(resp.data);
        setError(null);
      } catch (err: any) {
        console.error('Failed to fetch plan detail:', err);
        setError(err.response?.data?.error || 'Failed to fetch plan detail.');
      } finally {
        setIsLoadingDetail(false);
      }
    };

    loadPlanDetail();
  }, [selectedPlanId]);

  if (authLoading || isLoadingList) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <FaSpinner size={48} className="animate-spin text-secondary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="card-tonal max-w-md text-center space-y-4 border-red-500/20">
          <h2 className="text-xl font-display font-bold text-red-600">Error</h2>
          <p className="text-primary/70">{error}</p>
          <button onClick={() => navigate('/dashboard')} className="btn-secondary">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-6 py-12 max-w-5xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center gap-4 mb-8">
        <div className="p-4 rounded-2xl bg-secondary-container/20 text-secondary">
          <FaMap size={32} />
        </div>
        <div>
          <h1 className="text-4xl font-display font-extrabold text-primary tracking-tight">Your Learning Path</h1>
          <p className="text-primary/60 mt-1 font-medium">Personalized roadmaps to master your skills.</p>
        </div>
      </div>

      {plans.length === 0 ? (
        <div className="card-tonal text-center space-y-6 py-12">
          <div className="w-20 h-20 bg-primary/5 rounded-full flex items-center justify-center mx-auto mb-4">
            <FaBookOpen size={32} className="text-primary/40" />
          </div>
          <h2 className="text-2xl font-display font-bold text-primary">No Learning Plans Found</h2>
          <p className="text-primary/70 max-w-md mx-auto">
            Take an assessment to identify your skill gaps and generate a personalized learning plan.
          </p>
          <button onClick={() => navigate('/assessment')} className="btn-primary mt-4">
            Take Assessment
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
          {/* Sidebar / Plan Selector */}
          <div className="md:col-span-4 space-y-4">
            <h3 className="font-display font-bold text-lg text-primary px-1">Available Plans</h3>
            <div className="space-y-3">
              {plans.map((p) => (
                <button
                  key={p.learning_plan_id}
                  onClick={() => setSelectedPlanId(p.learning_plan_id)}
                  className={`w-full text-left p-4 rounded-xl transition-all duration-300 border ${
                    selectedPlanId === p.learning_plan_id
                      ? 'bg-white shadow-ambient border-secondary/30 ring-1 ring-secondary/20'
                      : 'bg-transparent border-outline-variant hover:bg-white hover:shadow-sm'
                  }`}
                >
                  <div className="font-bold text-primary">{p.skill_name}</div>
                  <div className="text-sm text-primary/60 mt-1 line-clamp-2">
                    {p.summary || 'Click to view details'}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Plan Detail Section */}
          <div className="md:col-span-8">
            {isLoadingDetail ? (
              <div className="card-tonal flex flex-col items-center justify-center py-24 space-y-4">
                <FaSpinner className="animate-spin text-secondary" size={32} />
                <span className="text-primary/60 font-medium">Crafting your roadmap...</span>
              </div>
            ) : planDetail ? (
              <div className="space-y-8 animate-in fade-in duration-500">
                {/* Plan Hero Summary */}
                <div className="glass p-8 rounded-3xl relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-secondary/10 to-transparent rounded-bl-full -z-10" />
                  <h2 className="text-3xl font-display font-extrabold text-primary mb-4">
                    {planDetail.recommendations?.skill_name || 'Learning Plan'}
                  </h2>
                  <p className="text-primary/70 text-lg leading-relaxed mb-8">
                    {planDetail.recommendations?.summary || 'Plan summary not available.'}
                  </p>
                  
                  <div className="flex flex-wrap items-center gap-6">
                    <div className="flex items-center gap-3 bg-white px-5 py-3 rounded-xl shadow-sm border border-outline-variant">
                      <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg">
                        <FaCalendarAlt />
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-primary leading-none">
                          {planDetail.timeline_weeks || planDetail.recommendations?.total_weeks || '—'}
                        </div>
                        <div className="text-xs font-semibold text-primary/50 uppercase tracking-wider mt-1">Weeks</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3 bg-white px-5 py-3 rounded-xl shadow-sm border border-outline-variant">
                      <div className="p-2 bg-blue-100 text-secondary rounded-lg">
                        <FaRegClock />
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-primary leading-none">
                          {Math.round((planDetail.estimated_hours || 0) / 60) || '—'}
                        </div>
                        <div className="text-xs font-semibold text-primary/50 uppercase tracking-wider mt-1">Hours</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Timeline / Phases */}
                {planDetail.recommendations?.phases && planDetail.recommendations.phases.length > 0 ? (
                  <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-secondary/20 before:via-outline-variant before:to-transparent">
                    {planDetail.recommendations.phases.map((phase: any, phaseIdx: number) => (
                      <div key={phaseIdx} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                        
                        {/* Timeline Marker */}
                        <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-background bg-secondary text-white font-bold text-sm shadow-sm z-10 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                          {phase.phase_number}
                        </div>

                        {/* Card Content */}
                        <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] glass p-6 rounded-2xl shadow-sm hover:shadow-ambient hover:-translate-y-1 transition-all duration-300">
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="text-xl font-display font-bold text-primary">{phase.title}</h4>
                            <span className="text-xs font-bold bg-primary/5 text-primary/70 px-2 py-1 rounded-md">
                              {phase.timeline_weeks || phase.duration_weeks || 'N/A'} wks
                            </span>
                          </div>
                          <p className="text-sm text-primary/70 mb-6">{phase.description}</p>
                          
                          <div className="space-y-4">
                            {/* Videos */}
                            {phase.youtube_resources && phase.youtube_resources.length > 0 && (
                              <div className="space-y-2">
                                <h5 className="text-xs font-bold text-primary/50 uppercase tracking-wider flex items-center gap-2 mb-2">
                                  <FaPlayCircle className="text-secondary" /> Videos
                                </h5>
                                {phase.youtube_resources.map((video: any, vidIdx: number) => (
                                  <a
                                    key={vidIdx}
                                    href={video.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="block p-3 rounded-lg bg-white border border-outline-variant hover:border-secondary/30 hover:bg-blue-50/50 transition-colors group/link"
                                  >
                                    <div className="flex justify-between items-start gap-2">
                                      <p className="text-sm font-semibold text-primary group-hover/link:text-secondary line-clamp-2">
                                        {video.title}
                                      </p>
                                      <FaExternalLinkAlt className="text-primary/30 group-hover/link:text-secondary shrink-0 text-xs mt-1" />
                                    </div>
                                    {video.duration_minutes && (
                                      <p className="text-xs text-primary/50 mt-1">{video.duration_minutes} min</p>
                                    )}
                                  </a>
                                ))}
                              </div>
                            )}

                            {/* Materials */}
                            {phase.website_resources && phase.website_resources.length > 0 && (
                              <div className="space-y-2">
                                <h5 className="text-xs font-bold text-primary/50 uppercase tracking-wider flex items-center gap-2 mb-2 mt-4">
                                  <FaBookOpen className="text-emerald" /> Materials
                                </h5>
                                {phase.website_resources.map((res: any, resIdx: number) => (
                                  <a
                                    key={resIdx}
                                    href={res.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="block p-3 rounded-lg bg-white border border-outline-variant hover:border-emerald/30 hover:bg-emerald-50/50 transition-colors group/link"
                                  >
                                    <div className="flex justify-between items-start gap-2">
                                      <p className="text-sm font-semibold text-primary group-hover/link:text-emerald line-clamp-2">
                                        {res.title}
                                      </p>
                                      <FaExternalLinkAlt className="text-primary/30 group-hover/link:text-emerald shrink-0 text-xs mt-1" />
                                    </div>
                                    <p className="text-xs text-primary/50 mt-1 capitalize">{res.category}</p>
                                  </a>
                                ))}
                              </div>
                            )}
                            
                            {/* Milestones */}
                            {phase.milestones && phase.milestones.length > 0 && (
                              <div className="mt-4 pt-4 border-t border-outline-variant">
                                <ul className="space-y-2">
                                  {phase.milestones.map((ms: string, msIdx: number) => (
                                    <li key={msIdx} className="flex items-start gap-2 text-sm text-primary/70">
                                      <FaCheckCircle className="text-primary/20 shrink-0 mt-0.5" />
                                      <span className="leading-snug">{ms}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};

export default LearningPlan;
