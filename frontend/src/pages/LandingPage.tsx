import React from 'react';
import { Link } from 'react-router-dom';
import logo from '../assets/logo.png';
import { FaArrowRight } from 'react-icons/fa6';
import { useAuth } from '../context/AuthContext';
import {
  FiArrowUpRight,
  FiCheckCircle,
  FiCpu,
  FiBookOpen,
  FiAward,
} from 'react-icons/fi';

const LandingPage: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="flex flex-col gap-24 pb-12 bg-background">

      {/* ─── Hero Section ──────────────────────────────────────────────── */}
      <section className="relative min-h-[80vh] flex items-center pt-20">
        <div className="container mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-8 animate-in fade-in slide-in-from-left-8 duration-700">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary-container/20 text-secondary text-sm font-semibold border border-secondary/10">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-secondary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-secondary"></span>
              </span>
              Next-Generation Skill Verification
            </div>
            <h1 className="text-5xl lg:text-7xl font-display font-extrabold text-primary leading-tight tracking-tight">
              Verify Your Skills, <br />
              <span className="text-secondary">Bridge the Gap</span>
            </h1>
            <p className="text-xl text-primary/60 max-w-xl leading-relaxed font-medium">
              Our AI-powered assessments evaluate your real-world skills and bridge the gap between education and employment.
            </p>
            {!isAuthenticated && (
              <div className="flex flex-wrap gap-4 pt-4">
                <Link
                  to="/register"
                  className="btn-primary flex items-center gap-2"
                >
                  Get Started <FiArrowUpRight size={20} />
                </Link>
                <Link
                  to="/login"
                  className="px-8 py-3 bg-surface-container-lowest border border-outline-variant rounded-md font-semibold text-primary hover:bg-surface-container-low transition-all"
                >
                  View Demo
                </Link>
              </div>
            )}
            {isAuthenticated && (
              <div className="flex flex-wrap gap-4 pt-4">
                <Link
                  to="/dashboard"
                  className="btn-primary flex items-center gap-2"
                >
                  Go to Dashboard <FaArrowRight size={18} />
                </Link>
              </div>
            )}
          </div>

          <div className="relative animate-in fade-in slide-in-from-right-8 duration-700 delay-200">
            <div className="relative rounded-3xl overflow-hidden glass shadow-ambient aspect-square lg:aspect-video flex items-center justify-center bg-gradient-to-br from-secondary/5 to-transparent">
              {/* Decorative blurs */}
              <div className="absolute inset-0 opacity-30">
                <div className="absolute top-0 right-0 w-64 h-64 bg-secondary/20 rounded-full blur-3xl" />
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-emerald/10 rounded-full blur-3xl" />
              </div>
              <div className="relative z-10 flex flex-col items-center gap-6">
                <div className="p-8 rounded-3xl glass shadow-ambient group hover:scale-110 transition-transform duration-500">
                  <img
                    src={logo}
                    alt="SkillScan Symbol"
                    className="w-15 h-15"
                  />
                </div>
                <div className="text-center space-y-1">
                  <div className="text-2xl font-display font-extrabold tracking-tight text-primary">SKILLSCAN</div>
                  <div className="text-xs font-bold tracking-[0.3em] uppercase text-primary/40">Verified Integrity</div>
                </div>
              </div>
            </div>

            {/* Floating Stats Card */}
            <div className="absolute -bottom-6 -left-6 glass p-5 rounded-xl shadow-ambient max-w-[190px] hidden md:block">
              <div className="flex items-center gap-2.5 mb-1.5">
                <div className="p-1.5 rounded-lg bg-emerald-100 text-emerald-600">
                  <FiCheckCircle size={20} />
                </div>
                <div className="text-sm font-bold text-primary">98% Accuracy</div>
              </div>
              <div className="text-xs text-primary/50 font-medium">Verified by AI assessment engines</div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Features / Verification Ecosystem ─────────────────────────── */}
      <section id="features" className="container mx-auto px-6">
        <div className="text-center space-y-3 mb-16">
          {isAuthenticated ? (
            <>
              <h2 className="text-3xl lg:text-5xl font-display font-extrabold text-primary tracking-tight">Continue Your Verification Journey</h2>
              <p className="text-primary/60 max-w-2xl mx-auto font-medium">
                Access your tools to upload resumes, take assessments, and view your learning plans.
              </p>
            </>
          ) : (
            <>
              <h2 className="text-3xl lg:text-5xl font-display font-extrabold text-primary tracking-tight">Verification Ecosystem</h2>
              <p className="text-primary/60 max-w-2xl mx-auto font-medium">
                A comprehensive suite of tools designed to validate your professional identity with academic precision and industrial relevance.
              </p>
            </>
          )}
        </div>

        {isAuthenticated ? (
          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/skills" className="btn-primary flex items-center gap-2">
              <FiCpu size={18} /> Upload Resume
            </Link>
            <Link to="/assessment" className="px-6 py-3 bg-surface-container-lowest border border-outline-variant rounded-md font-semibold text-primary hover:bg-surface-container-low transition-all flex items-center gap-2">
              <FiAward size={18} /> AI Assessment
            </Link>
            <Link to="/learning-plan" className="px-6 py-3 bg-surface-container-lowest border border-outline-variant rounded-md font-semibold text-primary hover:bg-surface-container-low transition-all flex items-center gap-2">
              <FiBookOpen size={18} /> Learning Plan
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                title: "Upload Resume",
                desc: "Our semantic parser extracts core competencies and identifies dormant strengths with precision.",
                icon: <FiCpu className="text-secondary" size={28} />,
                link: "Upload Now",
              },
              {
                title: "Take AI Assessment",
                desc: "Challenge yourself with adaptive, scenario-based evaluations that mirror real-world problems.",
                icon: <FiAward className="text-secondary" size={28} />,
                link: "Start Assessment",
              },
              {
                title: "Get Learning Plan",
                desc: "Receive a curated roadmap to bridge identified gaps, complete with resources and milestones.",
                icon: <FiBookOpen className="text-secondary" size={28} />,
                link: "View Roadmap",
              }
            ].map((feature, i) => (
              <div
                key={i}
                className="group glass p-8 rounded-2xl hover:shadow-ambient hover:-translate-y-1 transition-all duration-300"
              >
                <div className="p-3.5 rounded-xl bg-secondary-container/20 inline-block mb-6 group-hover:scale-110 transition-transform">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-display font-bold text-primary mb-3">{feature.title}</h3>
                <p className="text-primary/60 mb-6 leading-relaxed text-sm">
                  {feature.desc}
                </p>
                <div className="inline-flex items-center gap-1.5 text-secondary font-bold text-sm">
                  {feature.link} <FiArrowUpRight size={14} />
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ─── Stats Section ─────────────────────────────────────────────── */}
      <section className="bg-surface-container-low py-20 relative overflow-hidden">
        <div className="container mx-auto px-6 grid grid-cols-2 lg:grid-cols-4 gap-12 text-center">
          {[
            { label: "University Partners", value: "150+" },
            { label: "Accuracy Rate", value: "98%" },
            { label: "Verified Credentials", value: "45k+" },
            { label: "Graduates Served", value: "12k+" }
          ].map((stat, i) => (
            <div key={i} className="space-y-1.5">
              <div className="text-4xl lg:text-5xl font-display font-extrabold text-primary">{stat.value}</div>
              <div className="text-xs text-primary/50 uppercase tracking-wider font-semibold">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── Footer ────────────────────────────────────────────────────── */}
      <footer className="container mx-auto px-6 border-t border-outline-variant">
        <div className="grid grid-cols-2 md:grid-cols-4 mt-8 gap-12 mb-12">
          <div className="col-span-2 space-y-4">
            <div className="text-2xl font-display font-extrabold tracking-tight text-primary flex items-center gap-2">
              <img
                src={logo}
                alt="SkillScan Symbol"
                className="w-10 h-10"
              />
              SkillScan
            </div>
            <p className="text-primary/50 max-w-xs leading-relaxed text-sm">
              Validating professional identities through AI-driven skill verification.
            </p>
          </div>
          {isAuthenticated && (
            <div className="space-y-3">
              <h4 className="font-display font-bold text-primary">Platform</h4>
              <ul className="space-y-2 text-primary/60 text-sm">
                <li><Link to="/skills" className="hover:text-secondary transition-colors">Skill Matrix</Link></li>
                <li><Link to="/assessment" className="hover:text-secondary transition-colors">Assessments</Link></li>
                <li><Link to="/learning-plan" className="hover:text-secondary transition-colors">Learning Plans</Link></li>
              </ul>
            </div>
          )}
          <div className="space-y-3">
            <h4 className="font-display font-bold text-primary">Legal</h4>
            <ul className="space-y-2 text-primary/60 text-sm">
              <li><Link to="#" className="hover:text-secondary transition-colors">Privacy Policy</Link></li>
              <li><Link to="#" className="hover:text-secondary transition-colors">Terms of Service</Link></li>
              <li><Link to="#" className="hover:text-secondary transition-colors">Contact Us</Link></li>
            </ul>
          </div>
        </div>
        <div className="text-center py-8 text-primary/40 text-xs font-medium">
          © 2026 SkillScan Inc. All rights reserved.
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
