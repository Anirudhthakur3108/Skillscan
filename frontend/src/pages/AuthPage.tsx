import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LogIn, UserPlus, Mail, Lock, GraduationCap, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';

const AuthPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      if (isLogin) {
        const response = await apiClient.post('/auth/login', { email, password });
        login(response.data.access_token, {
          id: response.data.student.id,
          email: response.data.student.email,
          name: response.data.student.full_name
        });
      } else {
        const response = await apiClient.post('/auth/register', { 
          email, 
          password,
          full_name: fullName 
        });
        login(response.data.access_token, {
          id: response.data.student.id,
          email: response.data.student.email,
          name: response.data.student.full_name
        });
      }
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.error || 'An error occurred during authentication');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center pt-20 px-6 relative overflow-hidden">
      {/* Decorative background elements matching the Academic Architect theme */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-[120px] -z-10" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary/5 rounded-full blur-[120px] -z-10" />

      <div className="w-full max-w-md animate-in fade-in zoom-in-95 duration-500">
        <div className="text-center mb-10 space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-primary/10 text-primary mb-4">
            <GraduationCap size={32} />
          </div>
          <h2 className="text-3xl font-bold tracking-tight">
            {isLogin ? 'Welcome Back' : 'Define Your Legacy'}
          </h2>
          <p className="text-foreground-muted">
            {isLogin 
              ? 'Sign in to continue your skill validation journey' 
              : 'Join the global network of verified scholars'}
          </p>
        </div>

        <div className="glass p-8 rounded-[2rem] border border-white/20 shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-500 rounded-xl text-sm font-medium text-center">
                {error}
              </div>
            )}
            {!isLogin && (
              <div className="space-y-2">
                <label className="text-sm font-semibold ml-1">Full Name</label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-foreground-muted group-focus-within:text-primary transition-colors">
                    <UserPlus size={18} />
                  </div>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Enter your full name"
                    className="w-full bg-surface-container-low border-none rounded-xl py-3.5 pl-11 pr-4 focus:ring-2 focus:ring-primary/20 transition-all placeholder:text-foreground-muted/50"
                  />
                </div>
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-semibold ml-1">Academic Email</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-foreground-muted group-focus-within:text-primary transition-colors">
                  <Mail size={18} />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@university.edu"
                  className="w-full bg-surface-container-low border-none rounded-xl py-3.5 pl-11 pr-4 focus:ring-2 focus:ring-primary/20 transition-all placeholder:text-foreground-muted/50"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center px-1">
                <label className="text-sm font-semibold">Password</label>
                {isLogin && (
                  <button type="button" className="text-xs text-primary hover:underline font-medium">
                    Forgot?
                  </button>
                )}
              </div>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-foreground-muted group-focus-within:text-primary transition-colors">
                  <Lock size={18} />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-surface-container-low border-none rounded-xl py-3.5 pl-11 pr-4 focus:ring-2 focus:ring-primary/20 transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-4 bg-primary text-white rounded-xl font-bold hover:bg-primary-dark transition-all shadow-lg shadow-primary/20 flex items-center justify-center gap-2 group disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <Loader2 size={20} className="animate-spin" />
              ) : isLogin ? (
                <>Sign In <LogIn size={20} className="group-hover:translate-x-1 transition-transform" /></>
              ) : (
                <>Create Account <UserPlus size={20} className="group-hover:translate-x-1 transition-transform" /></>
              )}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-sm text-foreground-muted">
              {isLogin ? "Don't have an account?" : "Already a member?"}{' '}
              <button
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError('');
                }}
                className="text-primary font-bold hover:underline"
              >
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </div>
        </div>

        <div className="mt-12 flex justify-center gap-6 text-xs text-foreground-muted font-medium uppercase tracking-widest">
          <Link to="/" className="hover:text-primary">Privacy</Link>
          <Link to="/" className="hover:text-primary">Terms</Link>
          <Link to="/" className="hover:text-primary">Support</Link>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
