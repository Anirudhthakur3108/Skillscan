import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { FaSpinner, FaCircleCheck } from 'react-icons/fa6';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import { LuBrainCircuit } from 'react-icons/lu';
import { TiMediaRecord } from 'react-icons/ti';
import { BiInfoCircle } from 'react-icons/bi';

interface Question {
  id: string;
  question: string;
  options: { id: string, text: string }[];
  difficulty: number;
}

const Assessment: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const assessmentId = searchParams.get('assessment_id');

  const [questions, setQuestions] = useState<Question[]>([]);
  const [skillName, setSkillName] = useState<string>('');
  const [currentStep, setCurrentStep] = useState(1);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<number>(5);
  const [numQuestions, setNumQuestions] = useState<number>(5);

  // State for all assessments list
  const [assessmentsList, setAssessmentsList] = useState<any[]>([]);

  // Track answers
  const [answers, setAnswers] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!assessmentId) {
      if (!user?.id) return;

      const fetchAllAssessments = async () => {
        try {
          const response = await apiClient.get(`/assessments/student/${user.id}`);
          setAssessmentsList(response.data.assessments || []);
        } catch (err) {
          console.error("Failed to load assessments:", err);
          setError("Failed to load assessments.");
        } finally {
          setIsLoading(false);
        }
      };

      fetchAllAssessments();
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

        setSkillName(data.skill_name);
        setDifficulty(data.difficulty || 5);
        setNumQuestions(data.num_questions || 5);

        // Combine MCQs and other types if they exist, here we focus on MCQs
        const mcqs = data.questions?.mcq || [];
        setQuestions(mcqs);
      } catch (err) {
        console.error("Failed to load assessment:", err);
        setError("Failed to load assessment. It may not exist or you don't have access.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchAssessment();
  }, [assessmentId, navigate, user]);

  const totalSteps = questions.length || 5;

  const handleSelectOption = (questionId: string, optionId: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: optionId }));

    // Auto-advance after short delay
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
      if (currentStep < totalSteps) {
        setCurrentStep(currentStep + 1);
      } else {
        submitAssessment({ ...answers, [questionId]: optionId });
      }
    }, 1000);
  };

  const submitAssessment = async (finalAnswers: Record<string, string>) => {
    setIsProcessing(true);
    try {
      const response = await apiClient.post(`/assessments/${assessmentId}/submit`, {
        student_answers: {
          mcq: finalAnswers,
          coding: {},
          case_study: {}
        }
      });
      if (response.data?.skill_score_id) {
        localStorage.setItem(`skillScoreId_${assessmentId}`, response.data.skill_score_id.toString());
      }
      navigate(`/results?assessment_id=${assessmentId}`);
    } catch (err) {
      console.error("Failed to submit assessment:", err);
      setError("Failed to submit assessment. Please try again.");
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <FaSpinner size={48} className="animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="glass p-8 rounded-3xl border border-red-500/20 max-w-md text-center space-y-4">
          <h2 className="text-xl font-bold text-red-400">Error</h2>
          <p className="text-foreground-muted">{error}</p>
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

  if (!assessmentId) {
    return (
      <div className="container mx-auto px-6 py-12 max-w-5xl min-h-[70vh] flex flex-col">
        <div className="mb-10">
          <h1 className="text-4xl font-bold tracking-tight">My Assessments</h1>
          <p className="text-foreground-muted mt-2">Manage and continue your generated skill assessments.</p>
        </div>

        {assessmentsList.length === 0 ? (
          <div className="glass p-12 rounded-3xl border border-white/5 text-center text-foreground-muted space-y-4">
            <LuBrainCircuit size={40} className="mx-auto opacity-20" />
            <p className="font-medium">No assessments generated yet. Go to Dashboard to generate one.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {assessmentsList.map(a => (
              <div key={a.assessment_id} className="glass p-6 rounded-2xl border border-white/5 flex flex-col space-y-6 hover:border-white/20 transition-all">
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-xl leading-tight">{a.skill_name}</h3>
                    <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-md ${a.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-yellow-500/10 text-yellow-400'}`}>
                      {a.status}
                    </span>
                  </div>
                  <p className="text-xs text-primary uppercase tracking-widest font-bold">{a.category}</p>
                </div>

                <div className="flex-1"></div>

                <div className="pt-4 border-t border-white/5">
                  {a.status === 'completed' ? (
                    <button
                      onClick={() => navigate(`/results?assessment_id=${a.assessment_id}`)}
                      className="w-full py-3 bg-white/5 rounded-xl text-sm font-bold hover:bg-white/10 transition-colors"
                    >
                      View Results
                    </button>
                  ) : (
                    <button
                      onClick={() => navigate(`/assessment?assessment_id=${a.assessment_id}`)}
                      className="w-full py-3 bg-primary/20 text-primary rounded-xl text-sm font-bold hover:bg-primary hover:text-white transition-colors"
                    >
                      Start Assessment
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p>No questions found for this assessment.</p>
      </div>
    );
  }

  const currentQuestion = questions[currentStep - 1];

  return (
    <div className="container mx-auto px-6 py-12 max-w-4xl min-h-[70vh] flex flex-col">
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-6 mb-12">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-primary/10 text-primary">
            <LuBrainCircuit size={28} />
          </div>
          <div>
            <h1 className="text-xl font-bold uppercase tracking-widest text-foreground-muted/60">{skillName}</h1>
            <div className="text-sm font-bold text-primary">Question {currentStep} of {totalSteps}</div>
            <div className="text-xs text-foreground-muted mt-1 flex items-center gap-2">
              <span>Difficulty: {difficulty}/10</span>
              <span>•</span>
              <span>{numQuestions} Questions</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 px-4 py-2 glass border border-white/10 rounded-xl">
            <TiMediaRecord size={18} className="text-primary" />
            <span className="font-mono font-bold">14:52</span>
          </div>
          <div className="hidden md:flex gap-1">
            {Array.from({ length: totalSteps }).map((_, i) => (
              <div
                key={i}
                className={`h-1.5 w-8 rounded-full transition-all duration-500 ${i + 1 < currentStep ? 'bg-primary' : i + 1 === currentStep ? 'bg-primary/40' : 'bg-white/5'
                  }`}
              />
            ))}
          </div>
        </div>
      </div>

      {!isProcessing ? (
        <div className="flex-1 flex flex-col justify-center animate-in fade-in slide-in-from-bottom-8 duration-700">
          <div className="space-y-8 mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-surface-container-high text-xs font-bold uppercase tracking-wider text-primary border border-primary/20">
              <BiInfoCircle size={12} />
              Level {currentQuestion.difficulty}
            </div>
            <h2 className="text-3xl lg:text-4xl font-bold leading-tight">
              {currentQuestion.question}
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {currentQuestion.options?.map((option, i) => (
              <button
                key={option.id}
                onClick={() => handleSelectOption(currentQuestion.id, option.id)}
                className="group flex items-center justify-between p-6 rounded-2xl glass border border-white/10 hover:border-primary/50 hover:bg-primary/5 transition-all text-left animate-in fade-in slide-in-from-bottom-2 duration-300"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="flex items-center gap-6">
                  <div className="min-w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center font-bold group-hover:bg-primary group-hover:text-white transition-all">
                    {option.id}
                  </div>
                  <span className="text-lg font-medium">{option.text}</span>
                </div>
                <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                  <FaCircleCheck className="text-primary" />
                </div>
              </button>
            ))}
          </div>
        </div>

      ) : (
        <div className="flex-1 flex flex-col items-center justify-center space-y-8 animate-in fade-in zoom-in-95 duration-500 text-center">
          <div className="relative">
            <div className="absolute inset-0 bg-primary/20 rounded-full blur-3xl animate-pulse" />
            <div className="relative p-10 rounded-[3rem] glass border border-white/20 shadow-2xl">
              <FaSpinner size={64} className="text-primary animate-spin" />
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-2xl font-bold">
              {currentStep >= totalSteps ? 'Evaluating Responses...' : 'AI is crafting your tailored assessment...'}
            </h3>
            <p className="text-foreground-muted max-w-sm mx-auto">
              {currentStep >= totalSteps
                ? 'Synthesizing your performance against industry benchmarks.'
                : 'Analyzing your last answer to determine the optimal next challenge.'}
            </p>
          </div>
        </div>
      )}

      {/* Footer Branding */}
      <div className="mt-8 pt-4 border-t border-white/5 flex justify-between items-center text-[10px] font-bold uppercase tracking-widest text-foreground-muted/40">
        <span>© 2026 Scholar Veritas Academic Portal</span>
        <span className="text-primary">Architecting the Future of Verification</span>
      </div>
    </div>
  );
};

export default Assessment;

