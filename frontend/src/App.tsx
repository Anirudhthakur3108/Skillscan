import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import SkillInput from './pages/SkillInput';
import Assessment from './pages/Assessment';
import AssessmentTest from './pages/AssessmentTest';
import Results from './pages/Results';
import LearningPlan from './pages/LearningPlan';

const App: React.FC = () => {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<AuthPage />} />
          <Route path="/register" element={<AuthPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/skills" element={<SkillInput />} />
          <Route path="/assessment" element={<Assessment />} />
          <Route path="/assessment-test" element={<AssessmentTest />} />
          <Route path="/results" element={<Results />} />
          <Route path="/learning-plan" element={<LearningPlan />} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;
