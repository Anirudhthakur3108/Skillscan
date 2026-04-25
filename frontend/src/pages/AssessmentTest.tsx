import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  ChevronRight, 
  BrainCircuit, 
  Timer, 
  CheckCircle2, 
  Loader2, 
  Info,
  ArrowLeft,
  Clock,
  AlertCircle
} from 'lucide-react';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';

interface Question {
  id: string;
  question: string;
  options: { id: string; text: string }[];
  difficulty?: number;
  correct_option_id?: string;
  explanation?: string;
}

interface AssessmentData {
  assessment_id: number;
  skill_name: string;
  status: string;
  questions: {
    mcq?: Question[];
    coding?: any[];
    case_study?: any[];
  };
}

const AssessmentTest: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const assessmentId = searchParams.get('assessment_id');
  
  const [assessment, setAssessment] = useState<AssessmentData | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(1800); // 30 minutes
  
  // Track answers
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [answered, setAnswered] = useState<Set<string>>(new Set());

  // Timer effect
  useEffect(() => {
    if (!assessment || isSubmitting) return;
    
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 0) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [assessment, isSubmitting]);

  // Load assessment data
  useEffect(() => {
    if (!assessmentId) {
      setError("No assessment ID provided.");
      setIsLoading(false);
      return;
    }

    const fetchAssessment = async () => {
      try {
        const response = await apiClient.get(`/assessments/${assessmentId}`);
        const data = response.data;
        
        if (data.status === 'completed') {
          navigate(`/results?assessment_id=${assessmentId}`);
          return;
        }
        
        setAssessment({
          assessment_id: data.assessment_id,
          skill_name: data.skill_name,
          status: data.status,
          questions: data.questions || { mcq: [] }
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

  // Get all MCQ questions
  const allQuestions = assessment?.questions?.mcq || [];
  const currentQuestion = allQuestions[currentQuestionIndex];
  const totalQuestions = allQuestions.length;
  const isCurrentAnswered = currentQuestion?.id ? answered.has(currentQuestion.id) : false;

  const handleSelectOption = (optionId: string) => {
    if (!currentQuestion) return;
    
    setAnswers(prev => ({
      ...prev,
      [currentQuestion.id]: optionId
    }));
    
    setAnswered(prev => new Set([...prev, currentQuestion.id]));
  };

  const handleNext = () => {
    if (currentQuestionIndex < totalQuestions - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setIsProcessing(false);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
      setIsProcessing(false);
    }
  };

  const handleSubmitAssessment = async () => {
    if (answered.size < totalQuestions) {
      setError(`Please answer all questions. ${totalQuestions - answered.size} remaining.`);
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const response = await apiClient.post(`/assessments/${assessmentId}/submit`, {
        student_answers: answers
      });
      
      navigate(`/results?assessment_id=${assessmentId}`, {
        state: { scoreData: response.data }
      });
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

  const progressPercent = totalQuestions > 0 ? ((currentQuestionIndex + 1) / totalQuestions) * 100 : 0;
  const isTimeWarning = timeRemaining < 300;
  const isTimeCritical = timeRemaining < 60;

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="text-center space-y-4">
          <Loader2 size={48} className="animate-spin text-primary mx-auto" />
          <p className="text-foreground-muted font-medium">Loading assessment...</p>
        </div>
      </div>
    );
  }

  if (error && !assessment) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="glass p-8 rounded-3xl border border-red-500/20 max-w-md text-center space-y-4">
          <AlertCircle size={40} className="text-red-500 mx-auto" />
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

  if (!assessment || !currentQuestion) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <p className="text-foreground-muted">No questions available for this assessment.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 px-4 py-2 glass rounded-xl border border-white/10 hover:border-white/20 transition-all"
          >
            <ArrowLeft size={18} />
            Exit
          </button>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-4 py-2 glass rounded-xl border border-white/10">
              <BrainCircuit size={18} className="text-primary" />
              <span className="font-bold text-sm">{assessment.skill_name}</span>
            </div>
            
            <div className={`flex items-center gap-2 px-4 py-2 glass rounded-xl border ${
              isTimeCritical 
                ? 'border-red-500/50 bg-red-500/5' 
                : isTimeWarning
                ? 'border-yellow-500/50 bg-yellow-500/5'
                : 'border-white/10'
            } transition-all`}>
              <Clock size={18} className={isTimeCritical ? 'text-red-500' : isTimeWarning ? 'text-yellow-500' : 'text-primary'} />
              <span className={`font-mono font-bold ${isTimeCritical ? 'text-red-500' : isTimeWarning ? 'text-yellow-500' : ''}`}>
                {formatTime(timeRemaining)}
              </span>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="glass p-4 rounded-2xl border border-red-500/20 bg-red-500/5 flex items-start gap-3 mb-6">
            <AlertCircle size={20} className="text-red-500 flex-shrink-0 mt-0.5" />
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
              <div className="text-sm font-bold text-foreground-muted uppercase tracking-wide">
                Question {currentQuestionIndex + 1} of {totalQuestions}
              </div>
              <div className="text-sm font-bold text-primary">
                {answered.size} / {totalQuestions} answered
              </div>
            </div>
            <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
              <div 
                className="bg-gradient-to-r from-primary to-primary/50 h-full rounded-full transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Question */}
          <div className="mb-8 space-y-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-primary/10 text-primary font-bold text-sm min-w-fit mt-1">
                Q{currentQuestionIndex + 1}
              </div>
              <div>
                <h2 className="text-2xl font-bold leading-relaxed">
                  {currentQuestion.question}
                </h2>
                {currentQuestion.difficulty && (
                  <div className="mt-3 text-xs font-bold text-foreground-muted uppercase tracking-wide">
                    Difficulty: {
                      currentQuestion.difficulty <= 3 ? '🟢 Easy' :
                      currentQuestion.difficulty <= 6 ? '🟡 Medium' :
                      '🔴 Hard'
                    }
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Options */}
          <div className="space-y-3 mb-8">
            {currentQuestion.options && currentQuestion.options.map((option) => (
              <button
                key={option.id}
                onClick={() => handleSelectOption(option.id)}
                className={`w-full p-6 rounded-2xl border-2 transition-all text-left group ${
                  answers[currentQuestion.id] === option.id
                    ? 'border-primary bg-primary/10'
                    : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                    answers[currentQuestion.id] === option.id
                      ? 'border-primary bg-primary'
                      : 'border-white/30 group-hover:border-white/50'
                  }`}>
                    {answers[currentQuestion.id] === option.id && (
                      <CheckCircle2 size={20} className="text-white" />
                    )}
                  </div>
                  <span className="font-semibold text-lg">{option.text}</span>
                </div>
              </button>
            ))}
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between gap-4">
            <button
              onClick={handlePrevious}
              disabled={currentQuestionIndex === 0}
              className="px-6 py-3 bg-white/5 border border-white/10 rounded-xl font-bold hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
            >
              ← Previous
            </button>

            <div className="text-center text-sm text-foreground-muted font-medium">
              {!isCurrentAnswered && (
                <span className="text-yellow-500 font-bold">⚠️ Question not answered</span>
              )}
            </div>

            {currentQuestionIndex === totalQuestions - 1 ? (
              <button
                onClick={handleSubmitAssessment}
                disabled={isSubmitting || answered.size < totalQuestions}
                className="px-8 py-3 bg-primary text-white rounded-xl font-bold hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2 shadow-lg shadow-primary/20"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    Submit Assessment
                    <CheckCircle2 size={18} />
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
            {Array.from({ length: totalQuestions }).map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentQuestionIndex(idx)}
                className={`aspect-square rounded-lg font-bold text-xs transition-all border ${
                  idx === currentQuestionIndex
                    ? 'bg-primary border-primary text-white scale-110'
                    : answered.has(allQuestions[idx]?.id || '')
                    ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
                    : 'bg-white/5 border-white/10 hover:border-white/20 hover:bg-white/10'
                }`}
              >
                {idx + 1}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssessmentTest;
