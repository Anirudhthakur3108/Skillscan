import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, CheckCircle, ArrowRight, Loader2, Cpu, Type, Plus, X, Globe, Terminal } from 'lucide-react';
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

type InputMethod = 'upload' | 'paste' | 'manual';

const SkillInput: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [activeMethod, setActiveMethod] = useState<InputMethod>('upload');
  const [resumeText, setResumeText] = useState('');
  const [fileName, setFileName] = useState<string | null>(null);
  const [manualSkills, setManualSkills] = useState<{name: string, category: string}[]>([]);
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillCategory, setNewSkillCategory] = useState('Technical');
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [extractedSkills, setExtractedSkills] = useState<ExtractedSkill[]>([]);
  const [error, setError] = useState<string | null>(null);

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
    if (!user?.id) {
      setError("User not authenticated.");
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
        setIsComplete(true);
      } else {
        setError(response.data.error || "Failed to extract skills");
      }
    } catch (err: any) {
      console.error("Extraction error:", err);
      setError(err.response?.data?.error || "An error occurred during extraction.");
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

  return (
    <div className="container mx-auto px-6 py-12 max-w-4xl">
      <div className="text-center space-y-4 mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-semibold border border-primary/20">
          <Cpu size={16} />
          Semantic Skill Extraction
        </div>
        <h1 className="text-4xl font-bold">Architect Your Portfolio</h1>
        <p className="text-lg text-foreground-muted max-w-2xl mx-auto">
          Choose your method to map your expertise against industry standards.
        </p>
      </div>

      {!isComplete ? (
        <div className="glass rounded-[2rem] border border-white/20 shadow-2xl overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-white/10 bg-white/5">
            {[
              { id: 'upload', label: 'File Upload', icon: Upload },
              { id: 'paste', label: 'Paste Text', icon: Type },
              { id: 'manual', label: 'Manual Entry', icon: Plus },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveMethod(tab.id as InputMethod)}
                className={`flex-1 flex items-center justify-center gap-2 py-4 text-sm font-bold transition-all ${
                  activeMethod === tab.id 
                    ? 'bg-primary text-white' 
                    : 'text-foreground-muted hover:bg-white/10'
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
                <div className="w-20 h-20 rounded-full bg-primary/20 flex items-center justify-center relative">
                  <Loader2 size={40} className="text-primary animate-spin" />
                  <div className="absolute inset-0 border-4 border-primary/30 border-t-transparent rounded-full" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-2xl font-bold">Synthesizing Skills...</h3>
                  <p className="text-foreground-muted">Our AI is mapping your experience to industry gold standards.</p>
                </div>
                <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                  <div className="bg-primary h-full animate-progress rounded-full" />
                </div>
              </div>
            ) : (
              <>
                {/* Method Specific Content */}
                {activeMethod === 'upload' && (
                  <div className="w-full flex flex-col items-center space-y-6">
                    <div 
                      onClick={() => fileInputRef.current?.click()}
                      className="w-full h-64 border-2 border-dashed border-white/10 rounded-3xl flex flex-col items-center justify-center space-y-4 hover:border-primary/50 hover:bg-white/5 transition-all cursor-pointer group"
                    >
                      <div className="p-5 rounded-2xl bg-white/5 group-hover:bg-primary/10 transition-colors">
                        <Upload size={48} className="text-foreground-muted group-hover:text-primary transition-colors" />
                      </div>
                      <div className="text-center">
                        <p className="text-xl font-bold">Drop your resume here</p>
                        <p className="text-sm text-foreground-muted">PDF or DOCX supported (Max 5MB)</p>
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
                      className="w-full h-64 bg-surface-container-low border border-white/10 rounded-2xl p-6 text-foreground focus:outline-none focus:border-primary/50 transition-colors resize-none shadow-inner"
                    />
                    <button 
                      onClick={() => analyzeText(resumeText)}
                      disabled={!resumeText.trim()}
                      className="px-10 py-4 bg-primary text-white rounded-xl font-bold shadow-lg shadow-primary/20 hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 transition-all flex items-center gap-2"
                    >
                      Process Experience <ArrowRight size={20} />
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
                          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-primary/50 transition-colors"
                          onKeyPress={(e) => e.key === 'Enter' && handleAddManualSkill()}
                        />
                      </div>
                      <div className="flex gap-2">
                        <select 
                          value={newSkillCategory}
                          onChange={(e) => setNewSkillCategory(e.target.value)}
                          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-3 focus:outline-none focus:border-primary/50 transition-colors appearance-none"
                        >
                          <option value="Technical" className="bg-surface">Technical</option>
                          <option value="Soft Skill" className="bg-surface">Soft Skill</option>
                          <option value="Domain" className="bg-surface">Domain</option>
                          <option value="Tool" className="bg-surface">Tool</option>
                        </select>
                        <button 
                          onClick={handleAddManualSkill}
                          className="p-3 bg-primary text-white rounded-xl hover:bg-primary-dark transition-colors"
                        >
                          <Plus size={24} />
                        </button>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-3 min-h-[100px] p-6 rounded-2xl bg-white/5 border border-white/10">
                      {manualSkills.length === 0 && (
                        <div className="w-full flex flex-col items-center justify-center text-foreground-muted italic py-4">
                          <Plus size={32} className="opacity-20 mb-2" />
                          <p>No manual skills added yet.</p>
                        </div>
                      )}
                      {manualSkills.map((skill, idx) => (
                        <div key={idx} className="flex items-center gap-2 px-4 py-2 bg-white/10 border border-white/10 rounded-full group">
                          <span className="font-bold">{skill.name}</span>
                          <span className="text-[10px] uppercase opacity-50 bg-white/10 px-2 py-0.5 rounded-md">{skill.category}</span>
                          <button 
                            onClick={() => removeManualSkill(idx)}
                            className="p-1 hover:text-red-400 transition-colors"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ))}
                    </div>

                    <div className="flex justify-center">
                      <button 
                        onClick={submitManualSkills}
                        disabled={manualSkills.length === 0}
                        className="px-10 py-4 bg-primary text-white rounded-xl font-bold shadow-lg shadow-primary/20 hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 transition-all flex items-center gap-2"
                      >
                        Confirm Skills <ArrowRight size={20} />
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}

            {error && (
              <div className="w-full p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-center text-sm font-bold animate-shake">
                {error}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-8 animate-in fade-in zoom-in-95 duration-700">
          <div className="glass rounded-[2rem] p-10 border border-white/20 shadow-2xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
              <div className="flex items-center gap-4 text-emerald-500">
                <div className="p-4 rounded-2xl bg-emerald-500/10">
                  <CheckCircle size={40} />
                </div>
                <div>
                  <h2 className="text-3xl font-bold">Matrix Established</h2>
                  <p className="text-foreground-muted">Identified {extractedSkills.length} tactical competencies.</p>
                </div>
              </div>
              <button 
                onClick={() => { setIsComplete(false); setManualSkills([]); setResumeText(''); setFileName(null); }}
                className="px-6 py-2 bg-white/10 rounded-xl text-sm font-bold hover:bg-white/20 transition-colors border border-white/5"
              >
                Re-process Data
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {extractedSkills.map((skill, i) => (
                <div key={i} className="p-5 rounded-2xl bg-white/5 border border-white/10 hover:border-primary/50 transition-all group relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-30 transition-opacity">
                    <Terminal size={14} />
                  </div>
                  <div className="font-bold text-lg">{skill.skill_name}</div>
                  <div className="text-xs text-primary font-bold uppercase tracking-wider">{skill.category}</div>
                </div>
              ))}
            </div>

            <div className="flex justify-center mt-12">
              <button 
                onClick={() => navigate('/dashboard')}
                className="px-12 py-5 bg-primary text-white rounded-2xl font-bold hover:bg-primary-dark transition-all shadow-xl shadow-primary/30 flex items-center gap-4 text-xl group"
              >
                Initialize Dashboard
                <Globe className="group-hover:rotate-12 transition-transform" size={24} />
              </button>
            </div>
          </div>
          
          <p className="text-center text-foreground-muted text-sm italic opacity-50">
            "Every artifact added strengthens your digital architectural footprint."
          </p>
        </div>
      )}
    </div>
  );
};

export default SkillInput;
