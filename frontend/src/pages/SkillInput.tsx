import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaUpload, FaCircleCheck, FaArrowRight, FaSpinner, FaMicrochip, FaFont, FaPlus, FaX, FaGlobe, FaTrashCan } from 'react-icons/fa6';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import * as pdfjs from 'pdfjs-dist';
import mammoth from 'mammoth';
import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.min?url';

// Configure PDF.js worker - use bundled worker from npm package
pdfjs.GlobalWorkerOptions.workerSrc = pdfWorkerUrl;

interface ExtractedSkill {
  skill_name: string;
  category: string;
  confidence: number;
}

interface StudentSkill {
  id: number;
  skill_id: number;
  skill_name: string;
  category: string;
  proficiency_claimed: number | null;
  difficulty_configured: number | null;
  source: string;
}

type SkillConfigMap = Record<number, {
  difficulty: number | null;
  proficiency_claimed: number | null;
}>;

type InputMethod = 'upload' | 'paste' | 'manual';

const SkillInput: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [activeMethod, setActiveMethod] = useState<InputMethod>('upload');
  const [resumeText, setResumeText] = useState('');
  const [manualSkills, setManualSkills] = useState<{ name: string, category: string }[]>([]);
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillCategory, setNewSkillCategory] = useState('Technical');

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [extractedSkills, setExtractedSkills] = useState<ExtractedSkill[]>([]);
  const [configuredSkills, setConfiguredSkills] = useState<StudentSkill[]>([]);
  const [skillConfigs, setSkillConfigs] = useState<SkillConfigMap>({});
  const [isSavingConfigs, setIsSavingConfigs] = useState(false);
  const [configsSaved, setConfigsSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [_fileName, setFileName] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<StudentSkill | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const loadStudentSkills = async () => {
    if (!user?.id) return;
    try {
      const response = await apiClient.get(`/students/${user.id}/skills`);
      const skills: StudentSkill[] = response.data?.skills || [];
      setConfiguredSkills(skills);

      setSkillConfigs((previous) => {
        const next: SkillConfigMap = { ...previous };
        skills.forEach((skill) => {
          if (!next[skill.skill_id]) {
            next[skill.skill_id] = {
              difficulty: skill.difficulty_configured ?? null,
              proficiency_claimed: skill.proficiency_claimed ?? null,
            };
          }
        });
        return next;
      });

      const allAlreadyConfigured = skills.length > 0 && skills.every(
        (skill) => !!skill.difficulty_configured && !!skill.proficiency_claimed,
      );
      setConfigsSaved(allAlreadyConfigured);
    } catch (err) {
      console.error('Failed to load student skills for configuration:', err);
      setError('Failed to load skill configuration data. Please retry.');
    }
  };

  useEffect(() => {
    if (!isComplete) return;
    loadStudentSkills();
  }, [isComplete, user?.id]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    setError(null);
    setIsAnalyzing(true);

    try {
      let text = '';
      if (file.type === 'application/pdf') {
        try {
          const arrayBuffer = await file.arrayBuffer();
          const pdf = await pdfjs.getDocument({ data: arrayBuffer }).promise;
          let fullText = '';
          for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const content = await page.getTextContent();
            const strings = content.items.map((item: any) => item.str);
            fullText += strings.join(' ') + '\n';
          }
          text = fullText;
        } catch (pdfError: any) {
          console.error("PDF parsing error:", pdfError);
          throw new Error(`Failed to parse PDF: ${pdfError.message || 'Unknown error'}`);
        }
      } else if (file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
        const arrayBuffer = await file.arrayBuffer();
        const result = await mammoth.extractRawText({ arrayBuffer });
        text = result.value;
      } else {
        throw new Error("Unsupported file format. Please use PDF or DOCX.");
      }

      if (!text.trim()) throw new Error("Could not extract any text from the file.");
      setResumeText(text);
      await analyzeText(text);
    } catch (err: any) {
      console.error("File processing error:", err);
      setError(err.message || "Failed to process file. Please try again.");
      setIsAnalyzing(false);
    }
  };

  const analyzeText = async (text: string) => {
    const token = localStorage.getItem('token');
    if (!user?.id || !token) {
      setError("User not authenticated. Please sign in.");
      setIsAnalyzing(false);
      return;
    }

    setIsAnalyzing(true);
    try {
      const response = await apiClient.post(`/students/${user.id}/skills/upload`, {
        resume_text: text
      });

      if (response.data.status === 'success' || response.data.status === 'no_skills_found') {
        setExtractedSkills(response.data.extracted_skills || []);
        setConfigsSaved(false);
        setIsComplete(true);
      } else {
        setError(response.data.error || "Failed to extract skills");
      }
    } catch (err: any) {
      console.error("Extraction error:", err);
      const status = err.response?.status;
      if (status === 422 || status === 401) {
        setError("Authentication failed — please sign in again.");
        // clear local token and update auth state
        localStorage.removeItem('token');
        try { logout(); } catch (e) { /* ignore */ }
      } else {
        setError(err.response?.data?.error || "An error occurred during extraction.");
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAddManualSkill = () => {
    if (!newSkillName.trim()) return;
    setManualSkills([...manualSkills, { name: newSkillName, category: newSkillCategory }]);
    setNewSkillName('');
  };

  const removeManualSkill = (index: number) => {
    setManualSkills(manualSkills.filter((_, i) => i !== index));
  };

  const submitManualSkills = async () => {
    if (manualSkills.length === 0) {
      setError("Please add at least one skill.");
      return;
    }

    setIsAnalyzing(true);
    try {
      const response = await apiClient.post(`/students/${user?.id}/skills/bulk-add`, {
        skills: manualSkills.map(s => ({
          name: s.name,
          category: s.category,
          proficiency: 3 // Default
        }))
      });

      if (response.data.status === 'success') {
        // Set extracted skills to what we just added so the summary screen works
        setExtractedSkills(manualSkills.map(s => ({
          skill_name: s.name,
          category: s.category,
          confidence: 1.0
        })));
        setConfigsSaved(false);
        setIsComplete(true);
      } else {
        setError(response.data.error || "Failed to save skills.");
      }
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to save manual skills.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const updateSkillConfig = (skillId: number, field: 'difficulty' | 'proficiency_claimed', value: number) => {
    setSkillConfigs((previous) => ({
      ...previous,
      [skillId]: {
        difficulty: previous[skillId]?.difficulty ?? null,
        proficiency_claimed: previous[skillId]?.proficiency_claimed ?? null,
        [field]: value,
      },
    }));
    setConfigsSaved(false);
  };

  const handleSaveConfigurations = async () => {
    if (!user?.id || configuredSkills.length === 0) {
      setError('No skills available to configure.');
      return;
    }

    const payload = configuredSkills.map((skill) => ({
      skill_id: skill.skill_id,
      difficulty: skillConfigs[skill.skill_id]?.difficulty,
      proficiency_claimed: skillConfigs[skill.skill_id]?.proficiency_claimed,
    }));

    const missing = payload.find((item) => !item.difficulty || !item.proficiency_claimed);
    if (missing) {
      setError('Please select both difficulty and proficiency for every skill.');
      return;
    }

    setError(null);
    setIsSavingConfigs(true);
    try {
      await apiClient.post(`/students/${user.id}/skills/configure`, {
        skills: payload,
      });
      setConfigsSaved(true);
    } catch (err: any) {
      console.error('Failed to save skill configurations:', err);
      setError(err.response?.data?.error || 'Failed to save skill configuration.');
      setConfigsSaved(false);
    } finally {
      setIsSavingConfigs(false);
    }
  };

  const handleDeleteSkill = async () => {
    if (!user?.id || !deleteTarget) return;
    setIsDeleting(true);
    try {
      await apiClient.delete(`/students/${user.id}/skills/${deleteTarget.skill_id}`);
      // Remove from local state immediately
      setConfiguredSkills((prev) => prev.filter((s) => s.skill_id !== deleteTarget.skill_id));
      setSkillConfigs((prev) => {
        const next = { ...prev };
        delete next[deleteTarget.skill_id];
        return next;
      });
      setExtractedSkills((prev) => prev.filter((s) => s.skill_name !== deleteTarget.skill_name));
      setDeleteTarget(null);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to delete skill.');
    } finally {
      setIsDeleting(false);
    }
  };

  const allSkillsConfigured = configuredSkills.length > 0 && configuredSkills.every((skill) => {
    const config = skillConfigs[skill.skill_id];
    return !!config?.difficulty && !!config?.proficiency_claimed;
  });

  const canInitializeDashboard = allSkillsConfigured && configsSaved && !isSavingConfigs;

  return (
    <div className="container mx-auto px-6 py-12 max-w-4xl">
      <div className="text-center space-y-4 mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary-container/20 text-secondary text-sm font-semibold border border-secondary/10">
          <FaMicrochip size={16} />
          Semantic Skill Extraction
        </div>
        <h1 className="text-4xl font-display font-extrabold text-primary tracking-tight">Architect Your Portfolio</h1>
        <p className="text-lg text-primary/60 max-w-2xl mx-auto font-medium">
          Choose your method to map your expertise against industry standards.
        </p>
      </div>

      {!isComplete ? (
        <div className="glass rounded-2xl shadow-ambient overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-outline-variant bg-surface-container-low">
            {[
              { id: 'upload', label: 'File Upload', icon: FaUpload },
              { id: 'paste', label: 'Paste Text', icon: FaFont },
              { id: 'manual', label: 'Manual Entry', icon: FaPlus },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveMethod(tab.id as InputMethod)}
                className={`flex-1 flex items-center justify-center gap-2 py-4 text-sm font-bold transition-all ${activeMethod === tab.id
                  ? 'bg-gradient-to-br from-primary to-primary-container text-white'
                  : 'text-primary/50 hover:bg-primary/5 hover:text-primary'
                  }`}
              >
                <tab.icon size={18} />
                {tab.label}
              </button>
            ))}
          </div>

          <div className="p-10 flex flex-col items-center justify-center space-y-8">
            {isAnalyzing ? (
              <div className="flex flex-col items-center space-y-6 w-full max-w-md text-center">
                <div className="w-20 h-20 rounded-full bg-secondary-container/20 flex items-center justify-center relative">
                  <FaSpinner size={40} className="text-secondary animate-spin" />
                  <div className="absolute inset-0 border-4 border-secondary/20 border-t-transparent rounded-full" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-2xl font-display font-extrabold text-primary">Synthesizing Skills...</h3>
                  <p className="text-primary/60">Our AI is mapping your experience to industry gold standards.</p>
                </div>
                <div className="w-full bg-primary/5 h-2 rounded-full overflow-hidden">
                  <div className="bg-secondary h-full animate-progress rounded-full" />
                </div>
              </div>
            ) : (
              <>
                {/* Method Specific Content */}
                {activeMethod === 'upload' && (
                  <div className="w-full flex flex-col items-center space-y-6">
                    <div
                      onClick={() => fileInputRef.current?.click()}
                      className="w-full h-64 border-2 border-dashed border-outline-variant rounded-2xl flex flex-col items-center justify-center space-y-4 hover:border-secondary/40 hover:bg-secondary/5 transition-all cursor-pointer group"
                    >
                      <div className="p-5 rounded-2xl bg-primary/5 group-hover:bg-secondary-container/20 transition-colors">
                        <FaUpload size={48} className="text-primary/30 group-hover:text-secondary transition-colors" />
                      </div>
                      <div className="text-center">
                        <p className="text-xl font-display font-bold text-primary">Drop your resume here</p>
                        <p className="text-sm text-primary/50">PDF or DOCX supported (Max 5MB)</p>
                      </div>
                      <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileUpload}
                        accept=".pdf,.docx"
                        className="hidden"
                      />
                    </div>
                  </div>
                )}

                {activeMethod === 'paste' && (
                  <div className="w-full space-y-6 flex flex-col items-center">
                    <textarea
                      value={resumeText}
                      onChange={(e) => setResumeText(e.target.value)}
                      placeholder="Paste your professional summary, job descriptions, or full resume text..."
                      className="w-full h-64 bg-surface-container-low border border-outline-variant rounded-2xl p-6 text-primary focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary/40 transition-colors resize-none"
                    />
                    <button
                      onClick={() => analyzeText(resumeText)}
                      disabled={!resumeText.trim()}
                      className="btn-primary disabled:opacity-50 disabled:hover:scale-100 flex items-center gap-2"
                    >
                      Process Experience <FaArrowRight size={20} />
                    </button>
                  </div>
                )}

                {activeMethod === 'manual' && (
                  <div className="w-full space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="md:col-span-2">
                        <input
                          type="text"
                          value={newSkillName}
                          onChange={(e) => setNewSkillName(e.target.value)}
                          placeholder="Skill Name (e.g. React, Python)"
                          className="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 text-primary focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary/40 transition-colors"
                          onKeyPress={(e) => e.key === 'Enter' && handleAddManualSkill()}
                        />
                      </div>
                      <div className="flex gap-2">
                        <select
                          value={newSkillCategory}
                          onChange={(e) => setNewSkillCategory(e.target.value)}
                          className="flex-1 bg-surface-container-low border border-outline-variant rounded-xl px-3 py-3 text-primary focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary/40 transition-colors appearance-none"
                        >
                          <option value="Technical">Technical</option>
                          <option value="Soft Skill">Soft Skill</option>
                          <option value="Domain">Domain</option>
                          <option value="Tool">Tool</option>
                        </select>
                        <button
                          onClick={handleAddManualSkill}
                          className="p-3 bg-secondary text-white rounded-xl hover:bg-blue-700 transition-colors"
                        >
                          <FaPlus size={24} />
                        </button>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-3 min-h-[100px] p-6 rounded-2xl bg-surface-container-low border border-outline-variant">
                      {manualSkills.length === 0 && (
                        <div className="w-full flex flex-col items-center justify-center text-primary/40 italic py-4">
                          <FaPlus size={32} className="opacity-20 mb-2" />
                          <p>No manual skills added yet.</p>
                        </div>
                      )}
                      {manualSkills.map((skill, idx) => (
                        <div key={idx} className="flex items-center gap-2 px-4 py-2 bg-secondary-container/10 border border-outline-variant rounded-full group">
                          <span className="font-bold text-primary">{skill.name}</span>
                          <span className="text-[10px] uppercase text-primary/40 bg-primary/5 px-2 py-0.5 rounded-md font-bold">{skill.category}</span>
                          <button
                            onClick={() => removeManualSkill(idx)}
                            className="p-1 hover:text-red-400 transition-colors"
                          >
                            <FaX size={14} />
                          </button>
                        </div>
                      ))}
                    </div>

                    <div className="flex justify-center">
                      <button
                        onClick={submitManualSkills}
                        disabled={manualSkills.length === 0}
                        className="btn-primary disabled:opacity-50 disabled:hover:scale-100 flex items-center gap-2"
                      >
                        Confirm Skills <FaArrowRight size={20} />
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}

            {error && (
              <div className="w-full p-4 bg-red-50 border border-red-200/50 text-red-600 rounded-xl text-center text-sm font-bold">
                {error}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-8 animate-in fade-in zoom-in-95 duration-700">
          <div className="glass rounded-2xl p-10 shadow-ambient">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
              <div className="flex items-center gap-4 text-emerald-500">
                <div className="p-4 rounded-2xl bg-emerald-500/10">
                  <FaCircleCheck size={40} />
                </div>
                <div>
                  <h2 className="text-3xl font-display font-extrabold text-primary">Matrix Established</h2>
                  <p className="text-primary/60">Identified {(configuredSkills.length || extractedSkills.length)} tactical competencies.</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setIsComplete(false);
                  setManualSkills([]);
                  setResumeText('');
                  setFileName(null);
                  setConfiguredSkills([]);
                  setSkillConfigs({});
                  setConfigsSaved(false);
                }}
                className="px-6 py-2 bg-surface-container-low rounded-xl text-sm font-bold text-primary hover:bg-primary/5 transition-colors border border-outline-variant"
              >
                Re-process Data
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {(configuredSkills.length > 0
                ? configuredSkills.map((skill) => ({ skill_name: skill.skill_name, category: skill.category }))
                : extractedSkills
              ).map((skill, i) => (
                <div key={`${skill.skill_name}-${i}`} className="p-5 rounded-xl bg-surface-container-lowest border border-outline-variant hover:border-secondary/30 hover:shadow-ambient transition-all group relative overflow-hidden">
                  <button
                    onClick={() => {
                      const match = configuredSkills.find((s) => s.skill_name === skill.skill_name);
                      if (match) setDeleteTarget(match);
                    }}
                    className="absolute top-2 right-2 p-2 rounded-lg text-primary/30 opacity-0 group-hover:opacity-100 hover:bg-red-50 hover:text-red-500 transition-all"
                    title={`Delete ${skill.skill_name}`}
                  >
                    <FaTrashCan size={14} />
                  </button>
                  <div className="font-bold text-lg text-primary">{skill.skill_name}</div>
                  <div className="text-xs text-secondary font-bold uppercase tracking-wider">{skill.category}</div>
                </div>
              ))}
            </div>

            {/* Per-skill Difficulty and Proficiency Selectors */}
            <div className="mt-12 space-y-8 p-8 rounded-2xl bg-surface-container-low border border-outline-variant">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <h3 className="text-xl font-display font-bold text-primary">Configure Every Skill Before Initialization</h3>
                <button
                  onClick={handleSaveConfigurations}
                  disabled={isSavingConfigs || configuredSkills.length === 0}
                  className="btn-secondary disabled:opacity-50"
                >
                  {isSavingConfigs ? 'Saving...' : 'Save Skill Configuration'}
                </button>
              </div>

              {configuredSkills.length === 0 ? (
                <p className="text-sm text-primary/50">Loading skills for configuration...</p>
              ) : (
                <div className="space-y-4">
                  {configuredSkills.map((skill) => {
                    const config = skillConfigs[skill.skill_id] || { difficulty: null, proficiency_claimed: null };
                    return (
                      <div key={skill.skill_id} className="grid grid-cols-1 md:grid-cols-[1fr_1fr_1fr_auto] gap-4 p-4 rounded-xl bg-surface-container-lowest border border-outline-variant">
                        <div>
                          <p className="font-bold text-lg text-primary">{skill.skill_name}</p>
                          <p className="text-xs text-primary/50 uppercase tracking-wider font-semibold">{skill.category}</p>
                        </div>

                        <label className="space-y-1">
                          <span className="text-xs font-bold uppercase tracking-wider text-primary/50">Difficulty</span>
                          <select
                            value={config.difficulty ?? ''}
                            onChange={(e) => updateSkillConfig(skill.skill_id, 'difficulty', parseInt(e.target.value, 10))}
                            className="w-full bg-surface-container-low border border-outline-variant rounded-lg px-3 py-2 text-primary focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary/40"
                          >
                            <option value="">Select</option>
                            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((level) => (
                              <option key={level} value={level}>{level}/10</option>
                            ))}
                          </select>
                        </label>

                        <label className="space-y-1">
                          <span className="text-xs font-bold uppercase tracking-wider text-primary/50">Claimed Proficiency</span>
                          <select
                            value={config.proficiency_claimed ?? ''}
                            onChange={(e) => updateSkillConfig(skill.skill_id, 'proficiency_claimed', parseInt(e.target.value, 10))}
                            className="w-full bg-surface-container-low border border-outline-variant rounded-lg px-3 py-2 text-primary focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary/40"
                          >
                            <option value="">Select</option>
                            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((level) => (
                              <option key={level} value={level}>{level}/10</option>
                            ))}
                          </select>
                        </label>

                        <div className="flex items-end">
                          <button
                            onClick={() => setDeleteTarget(skill)}
                            className="p-2.5 rounded-xl text-primary/30 opacity-60 hover:opacity-100 hover:bg-red-50 hover:text-red-500 transition-all"
                            title={`Delete ${skill.skill_name}`}
                          >
                            <FaTrashCan size={16} />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {!allSkillsConfigured && (
                <p className="text-sm text-amber-600 font-medium">
                  Select both difficulty and proficiency for every skill to continue.
                </p>
              )}
              {allSkillsConfigured && !configsSaved && (
                <p className="text-sm text-amber-600 font-medium">
                  Save your skill configuration before initializing dashboard.
                </p>
              )}
              {allSkillsConfigured && configsSaved && (
                <p className="text-sm text-emerald-600 font-medium">
                  All skill settings saved. You can now initialize dashboard.
                </p>
              )}
            </div>

            <div className="flex justify-center mt-12">
              <button
                disabled={!canInitializeDashboard}
                onClick={() => navigate('/dashboard')}
                className="btn-primary px-12 py-5 rounded-2xl flex items-center gap-4 text-xl group disabled:opacity-50 disabled:hover:scale-100"
              >
                Initialize Dashboard
                <FaGlobe className="group-hover:rotate-12 transition-transform" size={24} />
              </button>
            </div>
          </div>

          <p className="text-center text-primary/40 text-sm italic">
            "Every artifact added strengthens your digital architectural footprint."
          </p>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-primary/40 backdrop-blur-sm"
            onClick={() => !isDeleting && setDeleteTarget(null)}
          />
          {/* Modal */}
          <div className="relative bg-surface-container-lowest border border-outline-variant rounded-2xl shadow-ambient p-8 w-full max-w-md mx-4 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex flex-col items-center text-center space-y-5">
              <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center">
                <FaTrashCan size={28} className="text-red-500" />
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-display font-bold text-primary">Delete Skill</h3>
                <p className="text-primary/60 text-sm">
                  Are you sure you want to remove <span className="text-primary font-bold">{deleteTarget.skill_name}</span> from your profile? This action cannot be undone.
                </p>
              </div>
              <div className="flex gap-3 w-full pt-2">
                <button
                  onClick={() => setDeleteTarget(null)}
                  disabled={isDeleting}
                  className="flex-1 px-6 py-3 rounded-xl font-bold bg-surface-container-low hover:bg-primary/5 border border-outline-variant text-primary transition-all disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteSkill}
                  disabled={isDeleting}
                  className="flex-1 px-6 py-3 rounded-xl font-bold bg-red-500 text-white hover:bg-red-600 transition-all shadow-lg shadow-red-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {isDeleting ? (
                    <><FaSpinner size={16} className="animate-spin" /> Deleting...</>
                  ) : (
                    'Delete'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SkillInput;



