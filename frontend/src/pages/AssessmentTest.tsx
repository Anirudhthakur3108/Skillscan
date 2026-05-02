import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  FaClock,
  FaSpinner,
  FaArrowLeft,
  FaCircleExclamation,
  FaCircleCheck,
  FaCode,
  FaBookOpen,
} from 'react-icons/fa6';
import apiClient from '../api/client';
import { LuBrainCircuit } from 'react-icons/lu';

/* ─── Types ──────────────────────────────────────────────────────────────────── */

interface MCQQuestion {
  id: string;
  question: string;
  options: { id: string; text: string }[];
  difficulty?: number;
}

interface CodingQuestion {
  id: string;
  problem_statement: string;
  constraints: string;
  example_input: string;
  example_output?: string;
  hints: string[];
}

interface CaseStudyQuestion {
  id: string;
  scenario: string;
  question: string;
  evaluation_criteria?: string[];
}

/** Union item that the stepper iterates over */
type AssessmentItem =
  | { type: 'mcq'; data: MCQQuestion }
  | { type: 'coding'; data: CodingQuestion }
  | { type: 'case_study'; data: CaseStudyQuestion };

interface AssessmentData {
  assessment_id: number;
  skill_name: string;
  status: string;
  difficulty?: number;
  num_questions?: number;
  time_limit_minutes?: number;
  questions: {
    mcq?: MCQQuestion[];
    coding?: CodingQuestion[];
    case_study?: CaseStudyQuestion[];
  };
}

/* ─── Component ──────────────────────────────────────────────────────────────── */

const AssessmentTest: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const assessmentId = searchParams.get('assessment_id');

  const [assessment, setAssessment] = useState<AssessmentData | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(1800);

  // Track answers — keyed by question id
  const [mcqAnswers, setMcqAnswers] = useState<Record<string, string>>({});
  const [codingAnswers, setCodingAnswers] = useState<Record<string, string>>({});
  const [caseStudyAnswers, setCaseStudyAnswers] = useState<Record<string, string>>({});

  // ─── Timer ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!assessment || isSubmitting) return;
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 0) { clearInterval(timer); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [assessment, isSubmitting]);

  // ─── Load assessment data ──────────────────────────────────────────────────
  useEffect(() => {
    if (!assessmentId) { setError("No assessment ID provided."); setIsLoading(false); return; }

    const fetchAssessment = async () => {
      try {
        const response = await apiClient.get(`/assessments/${assessmentId}`);
        const data = response.data;
        if (data.status === 'completed') { navigate(`/results?assessment_id=${assessmentId}`); return; }
        setTimeRemaining((data.time_limit_minutes || 30) * 60);
        setAssessment({
          assessment_id: data.assessment_id,
          skill_name: data.skill_name,
          status: data.status,
          difficulty: data.difficulty,
          num_questions: data.num_questions,
          time_limit_minutes: data.time_limit_minutes,
          questions: data.questions || { mcq: [] },
        });
      } catch (err: any) {
        console.error("Failed to load assessment:", err);
        setError(err.response?.data?.error || "Failed to load assessment. Please try again.");
      } finally {
        setIsLoading(false);
      }
    };
    fetchAssessment();
  }, [assessmentId, navigate]);

  // ─── Build a flat ordered list: MCQs → Coding → Case Study ─────────────────
  const items: AssessmentItem[] = React.useMemo(() => {
    if (!assessment) return [];
    const list: AssessmentItem[] = [];
    (assessment.questions.mcq || []).forEach(q => list.push({ type: 'mcq', data: q }));
    (assessment.questions.coding || []).forEach(q => list.push({ type: 'coding', data: q }));
    (assessment.questions.case_study || []).forEach(q => list.push({ type: 'case_study', data: q }));
    return list;
  }, [assessment]);

  const totalItems = items.length;
  const currentItem = items[currentIndex] ?? null;
  const progressPercent = totalItems > 0 ? ((currentIndex + 1) / totalItems) * 100 : 0;
  const isTimeWarning = timeRemaining < 300;
  const isTimeCritical = timeRemaining < 60;

  // Derive answered status directly from answer objects — always in sync
  const isItemAnswered = (item: AssessmentItem): boolean => {
    const id = item.data.id;
    if (item.type === 'mcq') return id in mcqAnswers;
    if (item.type === 'coding') return (codingAnswers[id] || '').trim().length > 0;
    if (item.type === 'case_study') return (caseStudyAnswers[id] || '').trim().length > 0;
    return false;
  };
  const answeredCount = items.filter(isItemAnswered).length;

  // ─── Answer handlers ──────────────────────────────────────────────────────
  const handleMcqSelect = (questionId: string, optionId: string) => {
    setMcqAnswers(prev => ({ ...prev, [questionId]: optionId }));
  };

  const handleTextAnswer = (questionId: string, value: string, type: 'coding' | 'case_study') => {
    if (type === 'coding') {
      setCodingAnswers(prev => ({ ...prev, [questionId]: value }));
    } else {
      setCaseStudyAnswers(prev => ({ ...prev, [questionId]: value }));
    }
  };

  const handleNext = () => { if (currentIndex < totalItems - 1) { setCurrentIndex(currentIndex + 1); setIsProcessing(false); } };
  const handlePrevious = () => { if (currentIndex > 0) { setCurrentIndex(currentIndex - 1); setIsProcessing(false); } };

  const handleSubmitAssessment = async () => {
    if (answeredCount < totalItems) {
      setError(`Please answer all questions. ${totalItems - answeredCount} remaining.`);
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await apiClient.post(`/assessments/${assessmentId}/submit`, {
        student_answers: {
          mcq: mcqAnswers,
          coding: codingAnswers,
          case_study: caseStudyAnswers,
        }
      });
      if (response.data.skill_score_id) {
        localStorage.setItem(`skillScoreId_${assessmentId}`, response.data.skill_score_id.toString());
      }
      navigate(`/results?assessment_id=${assessmentId}`, { state: { scoreData: response.data } });
    } catch (err: any) {
      console.error("Failed to submit assessment:", err);
      setError(err.response?.data?.error || "Failed to submit assessment. Please try again.");
      setIsSubmitting(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // ─── Section label helper ──────────────────────────────────────────────────
  const sectionLabel = (type: string) => {
    switch (type) {
      case 'mcq': return 'Multiple Choice';
      case 'coding': return 'Coding Challenge';
      case 'case_study': return 'Case Study';
      default: return '';
    }
  };

  const sectionIcon = (type: string) => {
    switch (type) {
      case 'mcq': return <LuBrainCircuit size={16} />;
      case 'coding': return <FaCode size={16} />;
      case 'case_study': return <FaBookOpen size={16} />;
      default: return null;
    }
  };

  // ─── Loading / Error states ───────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="text-center space-y-4">
          <FaSpinner size={48} className="animate-spin text-primary mx-auto" />
          <p className="text-foreground-muted font-medium">Loading assessment...</p>
        </div>
      </div>
    );
  }

  if (error && !assessment) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="glass p-8 rounded-3xl border border-red-500/20 max-w-md text-center space-y-4">
          <FaCircleExclamation size={40} className="text-red-500 mx-auto" />
          <h2 className="text-xl font-bold text-red-400">Error Loading Assessment</h2>
          <p className="text-foreground-muted">{error}</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="w-full px-6 py-3 bg-primary text-white rounded-xl font-bold hover:bg-primary-dark transition-all"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!assessment || !currentItem) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <p className="text-foreground-muted">No questions available for this assessment.</p>
      </div>
    );
  }

  // ─── Render the current question based on its type ────────────────────────
  const renderQuestion = () => {
    if (!currentItem) return null;

    /* ── MCQ ────────────────────────────────────────────────────────────────── */
    if (currentItem.type === 'mcq') {
      const q = currentItem.data as MCQQuestion;
      return (
        <>
          <div className="mb-8 space-y-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-primary/10 text-primary font-bold text-sm min-w-fit mt-1">
                Q{currentIndex + 1}
              </div>
              <div>
                <h2 className="text-2xl font-bold leading-relaxed">{q.question}</h2>
                {q.difficulty && (
                  <div className="mt-3 text-xs font-bold text-foreground-muted uppercase tracking-wide">
                    Difficulty: {
                      q.difficulty <= 3 ? '🟢 Easy' :
                        q.difficulty <= 6 ? '🟡 Medium' :
                          '🔴 Hard'
                    }
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-3 mb-8">
            {q.options.map((option) => (
              <button
                key={option.id}
                onClick={() => handleMcqSelect(q.id, option.id)}
                className={`w-full p-6 rounded-2xl border-2 transition-all text-left group ${mcqAnswers[q.id] === option.id
                  ? 'border-primary bg-primary/10'
                  : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                  }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${mcqAnswers[q.id] === option.id
                    ? 'border-primary bg-primary'
                    : 'border-white/30 group-hover:border-white/50'
                    }`}>
                    {mcqAnswers[q.id] === option.id && (
                      <FaCircleCheck size={20} className="text-white" />
                    )}
                  </div>
                  <span className="font-semibold text-lg">{option.text}</span>
                </div>
              </button>
            ))}
          </div>
        </>
      );
    }

    /* ── Coding ─────────────────────────────────────────────────────────────── */
    if (currentItem.type === 'coding') {
      const q = currentItem.data as CodingQuestion;
      return (
        <div className="mb-8 space-y-6">

          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-indigo-500/15 text-indigo-400 font-bold text-sm min-w-fit mt-1">
              <FaCode size={16} className="inline mr-1" /> Code
            </div>

            <h2 className="text-2xl font-bold leading-relaxed text-[#071a56]">
              {q.problem_statement}
            </h2>
          </div>

          {q.constraints && (
            <div className="glass rounded-xl border border-white/10 p-4">
              <h4 className="text-xs font-bold uppercase tracking-wide text-indigo-300 mb-2">
                Constraints
              </h4>
              <p className="text-sm text-slate-300 whitespace-pre-wrap">
                {q.constraints}
              </p>
            </div>
          )}

          {q.example_input && (
            <div className="glass rounded-xl border border-white/10 p-4">
              <h4 className="text-xs font-bold uppercase tracking-wide text-indigo-300 mb-2">
                Example Input
              </h4>
              <pre className="text-sm text-blue-200 whitespace-pre-wrap font-mono bg-black/50 p-3 rounded-lg">
                {q.example_input}
              </pre>
            </div>
          )}

          {q.hints && q.hints.length > 0 && (
            <details className="glass rounded-xl border border-amber-500/20 p-4 cursor-pointer">
              <summary className="text-xs font-bold uppercase tracking-wide text-amber-300">
                💡 Hints ({q.hints.length})
              </summary>

              <ul className="mt-3 space-y-1 text-sm text-amber-300 list-disc list-inside">
                {q.hints.map((h, i) => (
                  <li key={i}>{h}</li>
                ))}
              </ul>
            </details>
          )}

          <div>
            <label className="text-xs font-bold uppercase tracking-wide text-indigo-300 mb-2 block">
              Your Answer
            </label>

            <textarea
              rows={10}
              value={codingAnswers[q.id] || ''}
              onChange={(e) => handleTextAnswer(q.id, e.target.value, 'coding')}
              placeholder="Write your code / solution here..."
              className="w-full bg-black/50 border border-white/10 rounded-xl p-4 font-mono text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none resize-y"
            />
          </div>

        </div>
      );
    }

    /* ── Case Study ─────────────────────────────────────────────────────────── */
    if (currentItem.type === 'case_study') {
      const q = currentItem.data as CaseStudyQuestion;
      return (
        <div className="mb-8 space-y-6">

          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-indigo-500/15 text-indigo-400 font-bold text-sm min-w-fit mt-1">
              <FaBookOpen size={16} className="inline mr-1" /> Case Study
            </div>


          </div>

          <div className="glass rounded-xl border border-indigo-500/20 p-5">
            <h4 className="text-xs font-bold uppercase tracking-wide text-indigo-400 mb-3">
              Scenario
            </h4>
            <p className="text-[#071a56] leading-relaxed whitespace-pre-wrap">
              {q.scenario}
            </p>
          </div>

          <div className="glass rounded-xl border border-white/10 p-5">
            <h4 className="text-xs font-bold uppercase tracking-wide text-indigo-400 mb-3">
              Question
            </h4>
            <p className="text-lg font-semibold text-[#071a56] leading-relaxed">
              {q.question}
            </p>
          </div>

          {q.evaluation_criteria && q.evaluation_criteria.length > 0 && (
            <div className="glass rounded-xl border border-white/10 p-4">
              <h4 className="text-xs font-bold uppercase tracking-wide text-indigo-300 mb-2">
                Evaluation Criteria
              </h4>
              <ul className="space-y-1 text-sm text-amber-300 list-disc list-inside">
                {q.evaluation_criteria.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <label className="text-xs font-bold uppercase tracking-wide text-indigo-300 mb-2 block">
              Your Answer
            </label>

            <textarea
              rows={10}
              value={caseStudyAnswers[q.id] || ''}
              onChange={(e) => handleTextAnswer(q.id, e.target.value, 'case_study')}
              placeholder="Write your detailed analysis here..."
              className="w-full bg-black/50 border border-white/10 rounded-xl p-4 text-sm text-slate-100 placeholder-white-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none resize-y"
            />
          </div>

        </div>
      );
    }

    return null;
  };

  // ─── Main render ──────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 px-4 py-2 glass rounded-xl border border-white/10 hover:border-white/20 transition-all"
          >
            <FaArrowLeft size={18} />
            Exit
          </button>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-4 py-2 glass rounded-xl border border-white/10">
              <LuBrainCircuit size={18} className="text-primary" />
              <span className="font-bold text-sm">{assessment.skill_name}</span>
            </div>

            <div className={`flex items-center gap-2 px-4 py-2 glass rounded-xl border ${isTimeCritical
              ? 'border-red-500/50 bg-red-500/5'
              : isTimeWarning
                ? 'border-yellow-500/50 bg-yellow-500/5'
                : 'border-white/10'
              } transition-all`}>
              <FaClock size={18} className={isTimeCritical ? 'text-red-500' : isTimeWarning ? 'text-yellow-500' : 'text-primary'} />
              <span className={`font-mono font-bold ${isTimeCritical ? 'text-red-500' : isTimeWarning ? 'text-yellow-500' : ''}`}>
                {formatTime(timeRemaining)}
              </span>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="glass p-4 rounded-2xl border border-red-500/20 bg-red-500/5 flex items-start gap-3 mb-6">
            <FaCircleExclamation size={20} className="text-red-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-red-400 font-bold text-sm">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-red-500 hover:text-red-400 transition-colors flex-shrink-0"
            >
              ✕
            </button>
          </div>
        )}

        {/* Question Card */}
        <div className="glass rounded-3xl border border-white/10 p-8 mb-8 shadow-2xl">
          {/* Progress Bar */}
          <div className="mb-8 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold text-foreground-muted uppercase tracking-wide">
                {sectionIcon(currentItem.type)}
                <span>{sectionLabel(currentItem.type)}</span>
                <span className="text-white/50">—</span>
                <span>Question {currentIndex + 1} of {totalItems}</span>
              </div>
              <div className="text-sm font-bold text-primary">
                {answeredCount} / {totalItems} answered
              </div>
            </div>
            <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
              <div
                className="bg-gradient-to-r from-primary to-primary/50 h-full rounded-full transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Render question based on type */}
          {renderQuestion()}

          {/* Navigation */}
          <div className="flex items-center justify-between gap-4">
            <button
              onClick={handlePrevious}
              disabled={currentIndex === 0}
              className="px-6 py-3 bg-white/5 border border-white/10 rounded-xl font-bold hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
            >
              ← Previous
            </button>

            <div className="text-center text-sm text-foreground-muted font-medium">
              {currentItem && !isItemAnswered(currentItem) && (
                <span className="text-yellow-500 font-bold">⚠️ Question not answered</span>
              )}
            </div>

            {currentIndex === totalItems - 1 ? (
              <button
                onClick={handleSubmitAssessment}
                disabled={isSubmitting || answeredCount < totalItems}
                className="px-8 py-3 bg-primary text-white rounded-xl font-bold hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2 shadow-lg shadow-primary/20"
              >
                {isSubmitting ? (
                  <>
                    <FaSpinner size={18} className="animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    Submit Assessment
                    <FaCircleCheck size={18} />
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={handleNext}
                disabled={isProcessing}
                className="px-6 py-3 bg-primary text-white rounded-xl font-bold hover:bg-primary-dark transition-all flex items-center gap-2 shadow-lg shadow-primary/20"
              >
                Next →
              </button>
            )}
          </div>
        </div>

        {/* Question Navigator */}
        <div className="glass rounded-3xl border border-white/10 p-6">
          <h3 className="text-sm font-bold uppercase tracking-wide text-foreground-muted mb-4">Quick Navigation</h3>
          <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2">
            {items.map((item, idx) => {
              const itemId = item.data.id;
              const isAnswered = isItemAnswered(item);
              const isCurrent = idx === currentIndex;
              const typeColor = item.type === 'coding'
                ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
                : item.type === 'case_study'
                  ? 'bg-violet-500/20 border-violet-500/50 text-violet-400'
                  : 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400';

              return (
                <button
                  key={idx}
                  onClick={() => setCurrentIndex(idx)}
                  title={`${sectionLabel(item.type)} — Q${idx + 1}`}
                  className={`aspect-square rounded-lg font-bold text-xs transition-all border ${isCurrent
                    ? 'bg-primary border-primary text-white scale-110'
                    : isAnswered
                      ? typeColor
                      : 'bg-white/5 border-white/10 hover:border-white/20 hover:bg-white/10'
                    }`}
                >
                  {item.type === 'coding' ? `C${idx + 1}` : item.type === 'case_study' ? `CS` : idx + 1}
                </button>
              );
            })}
          </div>
          {/* Legend */}
          <div className="flex flex-wrap gap-4 mt-4 text-xs text-foreground-muted">
            <span className="flex items-center gap-1"><LuBrainCircuit size={12} /> MCQ</span>
            <span className="flex items-center gap-1"><FaCode size={12} className="text-emerald-400" /> Coding</span>
            <span className="flex items-center gap-1"><FaBookOpen size={12} className="text-violet-400" /> Case Study</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssessmentTest;
