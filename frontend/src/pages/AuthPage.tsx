import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { FaUserPlus, FaEnvelope, FaLock, FaSpinner } from 'react-icons/fa6';
import { FiLogIn, FiShield } from 'react-icons/fi';
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
  const location = useLocation();
  const { login } = useAuth();

  // Check URL path to determine if we should show login or register form
  useEffect(() => {
    if (location.pathname === '/register') {
      setIsLogin(false);
    } else if (location.pathname === '/login') {
      setIsLogin(true);
    }
  }, [location.pathname]);

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
    <div className="min-h-screen flex items-center justify-center px-6 py-16 bg-background relative overflow-hidden">
      {/* Decorative background blurs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-secondary/8 rounded-full blur-[120px] -z-10" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-emerald/6 rounded-full blur-[120px] -z-10" />

      <div className="w-full max-w-md animate-in fade-in zoom-in-95 duration-500">
        {/* Header */}
        <div className="text-center mb-10 space-y-3">
          <div className="inline-flex p-3.5 rounded-2xl bg-secondary-container/20 text-secondary mb-2">
            <FiShield size={32} />
          </div>
          <h1 className="text-3xl font-display font-extrabold text-primary tracking-tight">
            {isLogin ? 'Welcome Back' : 'Create Your Account'}
          </h1>
          <p className="text-primary/60 font-medium">
            {isLogin
              ? 'Sign in to continue your skill verification journey'
              : 'Join the platform to verify and showcase your skills'}
          </p>
        </div>

        {/* Form Card */}
        <div className="glass p-8 rounded-2xl shadow-ambient">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-3.5 bg-red-50 border border-red-200/50 text-red-600 rounded-xl text-sm font-semibold text-center">
                {error}
              </div>
            )}

            {!isLogin && (
              <div className="space-y-1.5">
                <label className="text-sm font-bold text-primary/70 ml-1">Full Name</label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-primary/30 group-focus-within:text-secondary transition-colors">
                    <FaUserPlus size={16} />
                  </div>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Enter your full name"
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl py-3 pl-11 pr-4 text-primary font-medium focus:ring-2 focus:ring-secondary/20 focus:border-secondary/40 transition-all placeholder:text-primary/30 outline-none"
                  />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-sm font-bold text-primary/70 ml-1">Email</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-primary/30 group-focus-within:text-secondary transition-colors">
                  <FaEnvelope size={16} />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@email.com"
                  className="w-full bg-surface-container-low border border-outline-variant rounded-xl py-3 pl-11 pr-4 text-primary font-medium focus:ring-2 focus:ring-secondary/20 focus:border-secondary/40 transition-all placeholder:text-primary/30 outline-none"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between items-center px-1">
                <label className="text-sm font-bold text-primary/70">Password</label>
                {isLogin && (
                  <button type="button" className="text-xs text-secondary hover:underline font-semibold">
                    Forgot?
                  </button>
                )}
              </div>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-primary/30 group-focus-within:text-secondary transition-colors">
                  <FaLock size={16} />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-surface-container-low border border-outline-variant rounded-xl py-3 pl-11 pr-4 text-primary font-medium focus:ring-2 focus:ring-secondary/20 focus:border-secondary/40 transition-all placeholder:text-primary/30 outline-none"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 btn-primary flex items-center justify-center gap-2 group disabled:opacity-70 disabled:cursor-not-allowed rounded-xl"
            >
              {isLoading ? (
                <FaSpinner size={20} className="animate-spin" />
              ) : isLogin ? (
                <>Sign In <FiLogIn size={18} className="group-hover:translate-x-1 transition-transform" /></>
              ) : (
                <>Create Account <FaUserPlus size={18} className="group-hover:translate-x-1 transition-transform" /></>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-outline-variant text-center">
            <p className="text-sm text-primary/60 font-medium">
              {isLogin ? "Don't have an account?" : "Already a member?"}{' '}
              <button
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError('');
                }}
                className="text-secondary font-bold hover:underline"
              >
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </div>
        </div>

        {/* Footer links */}
        <div className="mt-10 flex justify-center gap-6 text-xs text-primary/40 font-semibold uppercase tracking-widest">
          <Link to="/" className="hover:text-secondary transition-colors">Privacy</Link>
          <Link to="/" className="hover:text-secondary transition-colors">Terms</Link>
          <Link to="/" className="hover:text-secondary transition-colors">Support</Link>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
