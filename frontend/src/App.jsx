import { useEffect, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Core & Authentication Pages (Static Imports)
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Missions from './pages/Missions';
import Goals from './pages/Goals';
import AICoach from './pages/AICoach';
import Habits from './pages/Habits';
import Journal from './pages/Journal';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import VerifyEmail from './pages/VerifyEmail';

// Secondary Application Pages (Code-Split / Lazy-Loaded)
const Analytics = lazy(() => import('./pages/Analytics'));
const Blueprint = lazy(() => import('./pages/Blueprint'));
const Settings = lazy(() => import('./pages/Settings'));
const Community = lazy(() => import('./pages/Community'));
const Chat = lazy(() => import('./pages/Chat'));
const Profile = lazy(() => import('./pages/Profile'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));

import ErrorBoundary from './components/ErrorBoundary';
import { AuthProvider, useAuth } from './context/AuthContext';
import { getSettings } from './services/api';
import { ROUTES } from './constants/routes';

import './styles/globals.css';

// Immediate theme bootstrap from localStorage to prevent render flicker
const savedTheme = localStorage.getItem('theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);

const PageLoader = () => (
  <div style={{
    minHeight: '80vh',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'transparent',
    color: 'var(--cyan, #38bdf8)',
    fontSize: '14px',
    fontWeight: '600',
    gap: '12px'
  }}>
    <div style={{
      width: '28px',
      height: '28px',
      border: '2px solid rgba(56, 189, 248, 0.2)',
      borderTopColor: 'var(--cyan, #38bdf8)',
      borderRadius: '50%',
      animation: 'spin 0.8s linear infinite'
    }} />
    <span style={{ color: 'var(--text-secondary, #94a3b8)', fontSize: '13px' }}>
      Loading module...
    </span>
  </div>
);

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--dark-bg)', color: 'var(--cyan)', fontSize: '14px' }}>
        Authenticating Session...
      </div>
    );
  }
  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }
  return children;
};

const PublicOnlyRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return null;
  if (isAuthenticated) {
    return <Navigate to={ROUTES.DASHBOARD} replace />;
  }
  return children;
};

function AppContent() {
  const { user, loading } = useAuth();

  useEffect(() => {
    if (user) {
      getSettings()
        .then((data) => {
          if (data && data.theme) {
            document.documentElement.setAttribute('data-theme', data.theme);
          }
        })
        .catch((err) => console.error('Failed to load user settings for theme:', err));
    }
  }, [user]);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: 'var(--dark-bg, #020914)',
        color: 'var(--text-secondary, #94A3B8)',
        fontFamily: 'sans-serif'
      }}>
        Loading Mastery Key Coach...
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public Routes */}
          <Route path={ROUTES.LOGIN} element={<PublicOnlyRoute><Login /></PublicOnlyRoute>} />
          <Route path={ROUTES.REGISTER} element={<PublicOnlyRoute><Register /></PublicOnlyRoute>} />
          <Route path={ROUTES.FORGOT_PASSWORD} element={<PublicOnlyRoute><ForgotPassword /></PublicOnlyRoute>} />
          <Route path={ROUTES.RESET_PASSWORD} element={<PublicOnlyRoute><ResetPassword /></PublicOnlyRoute>} />
          <Route path={ROUTES.VERIFY_EMAIL} element={<VerifyEmail />} />
          <Route path={ROUTES.LANDING} element={<Landing />} />

          {/* Protected Application Routes */}
          <Route path={ROUTES.ROOT} element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path={ROUTES.DASHBOARD} element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path={ROUTES.ANALYTICS} element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
          <Route path={ROUTES.MISSIONS} element={<ProtectedRoute><Missions /></ProtectedRoute>} />
          <Route path={ROUTES.GOALS} element={<ProtectedRoute><Goals /></ProtectedRoute>} />
          <Route path={ROUTES.COACH} element={<ProtectedRoute><AICoach /></ProtectedRoute>} />
          <Route path={ROUTES.AI_COACH_ALIAS} element={<ProtectedRoute><AICoach /></ProtectedRoute>} />
          <Route path={ROUTES.HABITS} element={<ProtectedRoute><Habits /></ProtectedRoute>} />
          <Route path={ROUTES.STREAKS_ALIAS} element={<ProtectedRoute><Habits /></ProtectedRoute>} />
          <Route path={ROUTES.JOURNAL} element={<ProtectedRoute><Journal /></ProtectedRoute>} />
          <Route path={ROUTES.BLUEPRINT} element={<ProtectedRoute><Blueprint /></ProtectedRoute>} />
          <Route path={ROUTES.LIFE_BLUEPRINT_ALIAS} element={<ProtectedRoute><Blueprint /></ProtectedRoute>} />
          <Route path={ROUTES.SETTINGS} element={<ProtectedRoute><Settings /></ProtectedRoute>} />
          <Route path={ROUTES.COMMUNITY} element={<ProtectedRoute><Community /></ProtectedRoute>} />
          <Route path={ROUTES.MESSAGES} element={<ProtectedRoute><Chat /></ProtectedRoute>} />
          <Route path={ROUTES.CHAT_ALIAS} element={<ProtectedRoute><Chat /></ProtectedRoute>} />
          <Route path={ROUTES.PROFILE} element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path={ROUTES.MY_IDENTITY_ALIAS} element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path={ROUTES.ADMIN} element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />

          {/* Catch-all fallback */}
          <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;