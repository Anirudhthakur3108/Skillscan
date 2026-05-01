import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  FaChartLine,
  FaQuestion,
  FaBrain,
  FaBookOpenReader
} from 'react-icons/fa6';
import { FaCheckCircle, FaSignOutAlt } from 'react-icons/fa';
import { useAuth } from '../context/AuthContext';

const Sidebar: React.FC = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navItems = [
    { label: 'Dashboard', icon: <FaChartLine size={20} />, to: '/dashboard' },
    { label: 'Skill Matrix', icon: <FaCheckCircle size={20} />, to: '/skills' },
    { label: 'My Assessments', icon: <FaBrain size={20} />, to: '/assessment' },
    { label: 'Learning Plans', icon: <FaBookOpenReader size={20} />, to: '/learning-plan' },
  ];

  return (
    <aside className="w-64 glass border-r border-white/10 hidden lg:flex flex-col h-screen sticky top-0 pt-24 pb-8 px-4 transition-all duration-300">
      <div className="flex-1 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `
              w-full flex items-center gap-3 px-4 py-3 rounded-xl font-semibold transition-all
              ${isActive
                ? 'bg-primary text-white shadow-lg shadow-primary/20'
                : 'text-foreground-muted hover:bg-white/5 hover:text-foreground'}
            `}
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </div>

      <div className="space-y-4">

        <div className="space-y-1">
          <NavLink to="/" className="w-full flex items-center gap-3 px-4 py-2 text-foreground-muted hover:text-foreground text-sm font-medium transition-colors">
            <FaQuestion size={18} /> Home
          </NavLink>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-2 text-red-400/80 hover:text-red-400 text-sm font-medium transition-colors"
          >
            <FaSignOutAlt size={18} /> Sign Out
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
