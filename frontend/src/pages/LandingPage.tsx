import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowUpRight, CheckCircle2, Cpu, GraduationCap, BarChart3, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const LandingPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="flex flex-col gap-24 pb-24">
      {/* Hero Section */}
      <section className="relative min-h-[80vh] flex items-center pt-20">
        <div className="container mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-8 animate-in fade-in slide-in-from-left-8 duration-700">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-semibold border border-primary/20">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
              Next-Generation Skill Verification
            </div>
            <h1 className="text-5xl lg:text-7xl font-bold leading-tight">
              Verify Your Skills, <br />
              <span className="text-primary">Bridge the Gap</span>
            </h1>
            <p className="text-xl text-foreground-muted max-w-xl leading-relaxed">
              Our AI-powered assessments evaluate your real-world skills and bridge the gap between education and employment. Join the scholarly architect of professional identities.
            </p>
            {!isAuthenticated && (
              <div className="flex flex-wrap gap-4 pt-4">
                <Link
                  to="/register"
                  className="px-8 py-4 bg-primary text-white rounded-xl font-bold hover:bg-primary-dark transition-all shadow-lg shadow-primary/20 flex items-center gap-2"
                >
                  Get Started <ArrowUpRight size={20} />
                </Link>
                <Link
                  to="/login"
                  className="px-8 py-4 bg-surface-container text-foreground rounded-xl font-bold border border-foreground/10 hover:bg-surface-container-high transition-all"
                >
                  View Demo
                </Link>
              </div>
            )}
            {isAuthenticated && (
              <div className="flex flex-wrap gap-4 pt-4">
                <Link
                  to="/dashboard"
                  className="px-8 py-4 bg-primary text-white rounded-xl font-bold hover:bg-primary-dark transition-all shadow-lg shadow-primary/20 flex items-center gap-2"
                >
                  Go to Dashboard <ArrowRight size={20} />
                </Link>
              </div>
            )}
          </div>
          
          <div className="relative animate-in fade-in slide-in-from-right-8 duration-700 delay-200">
            <div className="relative rounded-3xl overflow-hidden glass shadow-2xl border border-white/20 aspect-square lg:aspect-video flex items-center justify-center bg-primary/5">
              {/* Abstract Academic Background Composition */}
              <div className="absolute inset-0 opacity-20">
                <div className="absolute top-0 right-0 w-64 h-64 bg-primary/30 rounded-full blur-3xl" />
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-primary/20 rounded-full blur-3xl" />
              </div>
              <div className="relative z-10 flex flex-col items-center gap-6">
                <div className="p-8 rounded-3xl bg-white/5 backdrop-blur-xl border border-white/10 shadow-2xl group hover:scale-105 transition-transform duration-500">
                  <GraduationCap size={80} className="text-primary animate-pulse" />
                </div>
                <div className="text-center space-y-2">
                  <div className="text-2xl font-black tracking-tighter text-primary/80">SCHOLAR VERITAS</div>
                  <div className="text-xs font-bold tracking-[0.3em] uppercase text-foreground-muted">Verified Integrity</div>
                </div>
              </div>
              <div className="absolute inset-0 bg-gradient-to-t from-background/40 to-transparent" />
            </div>
            
            {/* Floating Stats Card */}
            <div className="absolute -bottom-8 -left-8 glass p-6 rounded-2xl shadow-xl border border-white/20 max-w-[200px] hidden md:block">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-500">
                  <CheckCircle2 size={24} />
                </div>
                <div className="text-sm font-bold">98% Accuracy</div>
              </div>
              <div className="text-xs text-foreground-muted">Verified by AI assessment engines</div>
            </div>
          </div>
        </div>
      </section>

      {/* Verification Ecosystem */}
      <section id="features" className="container mx-auto px-6">
        <div className="text-center space-y-4 mb-16">
          <h2 className="text-3xl lg:text-5xl font-bold">Verification Ecosystem</h2>
          <p className="text-foreground-muted max-w-2xl mx-auto">
            A comprehensive suite of tools designed to architect your professional identity with academic precision and industrial relevance.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            {
              title: "Upload Resume",
              desc: "Our semantic parser extracts core competencies and identifies dormant strengths with academic precision.",
              icon: <Cpu className="text-primary" size={32} />,
              link: "Upload Now",
              to: "/skills"
            },
            {
              title: "Take AI Assessment",
              desc: "Challenge yourself with adaptive, scenario-based evaluations that mirror real-world industrial problems.",
              icon: <GraduationCap className="text-primary" size={32} />,
              link: "Start Assessment",
              to: "/assessment"
            },
            {
              title: "Get Learning Plan",
              desc: "Receive a curated roadmap to bridge identified gaps, complete with scholarly resources and verified milestones.",
              icon: <BarChart3 className="text-primary" size={32} />,
              link: "View Roadmap",
              to: "/results"
            }
          ].map((feature, i) => (
            <div 
              key={i}
              className="group glass p-8 rounded-3xl border border-white/10 hover:border-primary/30 transition-all duration-300 hover:-translate-y-2"
            >
              <div className="p-4 rounded-2xl bg-primary/10 inline-block mb-6 group-hover:scale-110 transition-transform">
                {feature.icon}
              </div>
              <h3 className="text-2xl font-bold mb-4">{feature.title}</h3>
              <p className="text-foreground-muted mb-8 leading-relaxed">
                {feature.desc}
              </p>
              <Link to={feature.to} className="inline-flex items-center gap-2 text-primary font-bold hover:gap-3 transition-all">
                {feature.link} <ArrowUpRight size={18} />
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Stats Section */}
      <section className="bg-surface-container-low py-20 relative overflow-hidden">
        <div className="container mx-auto px-6 grid grid-cols-2 lg:grid-cols-4 gap-12 text-center">
          {[
            { label: "University Partners Worldwide", value: "150+" },
            { label: "Accuracy Rate", value: "98%" },
            { label: "Verified Credentials", value: "45k+" },
            { label: "Ivy-League Graduates", value: "12k+" }
          ].map((stat, i) => (
            <div key={i} className="space-y-2">
              <div className="text-4xl lg:text-6xl font-bold text-primary">{stat.value}</div>
              <div className="text-sm text-foreground-muted uppercase tracking-wider font-semibold">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-6">
        <div className="glass rounded-[3rem] p-12 lg:p-24 text-center space-y-8 relative overflow-hidden border border-white/20">
          <div className="absolute top-0 right-0 w-96 h-96 bg-primary/20 rounded-full blur-[120px] -mr-48 -mt-48" />
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-primary/10 rounded-full blur-[120px] -ml-48 -mb-48" />
          
          <h2 className="text-4xl lg:text-6xl font-bold relative z-10">
            {isAuthenticated ? "Continue Your Verification Journey" : "Ready to architect your career?"}
          </h2>
          <p className="text-xl text-foreground-muted max-w-2xl mx-auto relative z-10">
            {isAuthenticated ? "Access your tools to upload resumes, take assessments, and view your learning plans." : "Take the first step towards a verified professional identity. Start your journey with SkillScan today."}
          </p>
          <div className="flex flex-wrap justify-center gap-4 relative z-10">
            {!isAuthenticated ? (
              <Link
                to="/register"
                className="px-12 py-5 bg-primary text-white rounded-2xl font-bold hover:bg-primary-dark transition-all shadow-xl shadow-primary/30 flex items-center gap-3 text-lg"
              >
                Get Started Now <ArrowUpRight size={24} />
              </Link>
            ) : (
              <>
                <Link
                  to="/skills"
                  className="px-8 py-4 bg-primary text-white rounded-xl font-bold hover:bg-primary-dark transition-all shadow-lg shadow-primary/30 flex items-center gap-2"
                >
                  <Cpu size={20} /> Upload Resume
                </Link>
                <Link
                  to="/assessment"
                  className="px-8 py-4 bg-surface-container text-foreground rounded-xl font-bold border border-foreground/10 hover:bg-surface-container-high transition-all flex items-center gap-2"
                >
                  <GraduationCap size={20} /> AI Assessment
                </Link>
                <Link
                  to="/results"
                  className="px-8 py-4 bg-surface-container text-foreground rounded-xl font-bold border border-foreground/10 hover:bg-surface-container-high transition-all flex items-center gap-2"
                >
                  <BarChart3 size={20} /> Learning Plan
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="container mx-auto px-6 pt-24 border-t border-foreground/5">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-12 mb-12">
          <div className="col-span-2 space-y-6">
            <div className="text-2xl font-black tracking-tighter flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white">
                <Cpu size={20} />
              </div>
              SKILLSCAN
            </div>
            <p className="text-foreground-muted max-w-xs leading-relaxed">
              Architecting professional identities through scholarly AI-driven skill verification.
            </p>
          </div>
          <div className="space-y-4">
            <h4 className="font-bold text-lg">Platform</h4>
            <ul className="space-y-2 text-foreground-muted">
              <li><Link to="/skills" className="hover:text-primary transition-colors">Skill Matrix</Link></li>
              <li><Link to="/assessment" className="hover:text-primary transition-colors">Assessments</Link></li>
              <li><Link to="/results" className="hover:text-primary transition-colors">Learning Paths</Link></li>
            </ul>
          </div>
          <div className="space-y-4">
            <h4 className="font-bold text-lg">Legal</h4>
            <ul className="space-y-2 text-foreground-muted">
              <li><Link to="#" className="hover:text-primary transition-colors">Privacy Policy</Link></li>
              <li><Link to="#" className="hover:text-primary transition-colors">Terms of Service</Link></li>
              <li><Link to="#" className="hover:text-primary transition-colors">Contact Us</Link></li>
            </ul>
          </div>
        </div>
        <div className="text-center py-8 text-foreground-muted text-sm">
          © 2026 SkillScan Inc. All rights reserved. Architected with precision.
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
