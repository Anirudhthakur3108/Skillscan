import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useAuth } from '../context/AuthContext';
import { User as UserIcon, Search, Bell, BrainCircuit } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const { user, isAuthenticated } = useAuth();
  
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';
  const isLandingPage = location.pathname === '/';
  
  // Show sidebar only on internal pages (not landing or auth)
  const showSidebar = !isAuthPage && !isLandingPage;

  return (
    <div className="min-h-screen flex flex-col bg-background selection:bg-primary/30">
      {/* Top Navigation / Header */}
      {!isAuthPage && (
        <nav className="fixed top-0 w-full z-50 glass px-6 py-4 flex justify-between items-center shadow-ambient border-b border-white/5">
          <div className="flex items-center gap-10">
            <Link to="/" className="flex items-center gap-4 group">
              <img 
                src="/assets/branding/logo.png" 
                alt="SkillScan Symbol" 
                className="w-10 h-10 group-hover:scale-110 transition-transform" 
              />
              <img 
                src="/assets/branding/slogan.png" 
                alt="SkillScan Title and Slogan" 
                className="h-10 object-contain hidden sm:block" 
              />
            </Link>
          </div>
          
          <div className="flex items-center gap-6">
            {!isAuthenticated ? (
              <>
                <div className="hidden md:flex items-center gap-8 font-body font-bold text-foreground/70 text-sm">
                  <Link to="/#features" className="hover:text-primary transition-colors">Methodology</Link>
                  <Link to="/#pricing" className="hover:text-primary transition-colors">Institutions</Link>
                </div>
                <Link to="/login" className="btn-primary py-2.5 px-6 text-sm font-bold shadow-lg shadow-primary/20">
                  Sign In
                </Link>
              </>
            ) : (
              <div className="flex items-center gap-4">
                <button className="p-2.5 rounded-xl hover:bg-white/5 text-foreground-muted transition-all relative">
                  <Bell size={20} />
                  <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-primary rounded-full border-2 border-background" />
                </button>
              </div>
            )}
          </div>
        </nav>
      )}
      
      <div className="flex flex-1">
        {showSidebar && <Sidebar />}
        
        <main className={`flex-grow ${!isAuthPage ? 'pt-24' : ''} ${showSidebar ? 'lg:px-8' : ''}`}>
          <div className={showSidebar ? 'max-w-7xl mx-auto' : ''}>
            {children}
          </div>
          
          {/* Footer - Only on landing page or non-dashboard pages maybe? */}
          {isLandingPage && (
            <footer className="bg-surface-container-low py-12 px-8 border-t border-white/5 mt-24">
              <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 bg-primary rounded-md shadow-lg shadow-primary/20" />
                  <span className="font-display font-bold text-lg tracking-editorial">SkillScan</span>
                </div>
                <p className="text-sm text-foreground-muted font-medium">
                  &copy; 2026 Scholar Veritas. The Standard in Academic Skill Verification.
                </p>
                <div className="flex gap-6 text-xs font-bold uppercase tracking-widest text-foreground-muted">
                  <a href="#" className="hover:text-primary">Privacy</a>
                  <a href="#" className="hover:text-primary">Terms</a>
                </div>
              </div>
            </footer>
          )}
        </main>
      </div>
    </div>
  );
};

export default Layout;
