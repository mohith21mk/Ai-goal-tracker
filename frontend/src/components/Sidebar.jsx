import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  CheckSquare,
  Target,
  Bot,
  BookOpen,
  Zap,
  BarChart3,
  Layers,
  Settings,
  Users,
  MessageSquare,
  User,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import MKCLogo from './MKCLogo';
import { getProgress } from '../services/api';
import './Sidebar.css';

const rawNavItems = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    path: '/',
    icon: <LayoutDashboard size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'analytics',
    label: 'Analytics',
    path: '/analytics',
    icon: <BarChart3 size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'missions',
    label: 'Missions',
    path: '/missions',
    icon: <CheckSquare size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'goals',
    label: 'Goals',
    path: '/goals',
    icon: <Target size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'coach',
    label: 'AI Coach',
    path: '/coach',
    icon: <Bot size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'habits',
    label: 'Habits',
    path: '/habits',
    icon: <Zap size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'journal',
    label: 'Journal',
    path: '/journal',
    icon: <BookOpen size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'blueprint',
    label: 'Life Blueprint',
    path: '/blueprint',
    icon: <Layers size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'settings',
    label: 'Settings',
    path: '/settings',
    icon: <Settings size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'community',
    label: 'Community',
    path: '/community',
    icon: <Users size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'chat',
    label: 'Messages',
    path: '/messages',
    icon: <MessageSquare size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'profile',
    label: 'My Identity',
    path: '/profile',
    icon: <User size={18} strokeWidth={1.8} aria-hidden="true" />
  },
];

const Sidebar = () => {
  const location = useLocation();
  const [progress, setProgress] = useState({ completed: 0, total: 0, percentage: 0 });

  useEffect(() => {
    let isMounted = true;
    async function loadProgress() {
      try {
        const data = await getProgress();
        if (isMounted && data) {
          setProgress(data);
        }
      } catch (err) {
        console.warn('Sidebar progress fetch error:', err);
      }
    }
    loadProgress();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <aside className="sidebar-container">
      {/* Brand Header */}
      <div className="sidebar-brand">
        <div className="brand-icon-wrapper">
          <MKCLogo className="brand-anchor-icon" style={{ width: 36, height: 36 }} aria-hidden="true" />
        </div>
        <div className="brand-text">
          <span className="brand-title font-display">Mastery Key</span>
          <span className="brand-subtitle font-display">Coach</span>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="sidebar-nav">
        {rawNavItems.map((item) => {
          const isActive = item.id === 'goals'
            ? location.pathname === '/goals'
            : item.id === 'missions'
            ? location.pathname === '/missions'
            : item.id === 'coach'
            ? location.pathname === '/coach'
            : item.id === 'streaks'
            ? location.pathname === '/habits' || location.pathname === '/streaks'
            : item.id === 'journal'
            ? location.pathname === '/journal'
            : item.id === 'blueprint'
            ? location.pathname === '/blueprint'
            : item.id === 'settings'
            ? location.pathname === '/settings'
            : item.id === 'community'
            ? location.pathname === '/community'
            : item.id === 'profile'
            ? location.pathname === '/profile'
            : item.id === 'analytics'
            ? location.pathname === '/analytics'
            : (location.pathname === '/' || location.pathname === '/dashboard') && item.id === 'dashboard';

          if (item.path.startsWith('/')) {
            return (
              <Link
                key={item.id}
                to={item.path}
                className={`nav-item ${isActive ? 'active' : ''}`}
              >
                <div className="nav-item-content">
                  <span className="nav-icon">{item.icon}</span>
                  <span className="nav-label">{item.label}</span>
                </div>
                {isActive && <div className="active-indicator" />}
              </Link>
            );
          }

          return (
            <a
              key={item.id}
              href={item.path}
              className={`nav-item ${isActive ? 'active' : ''}`}
            >
              <div className="nav-item-content">
                <span className="nav-icon">{item.icon}</span>
                <span className="nav-label">{item.label}</span>
              </div>
              {isActive && <div className="active-indicator" />}
            </a>
          );
        })}
      </nav>

      {/* Bottom Dynamic Legacy Progress Card */}
      <div className="sidebar-legacy-card glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '10px', padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <div className="legacy-icon">
            <Sparkles size={20} strokeWidth={1.8} aria-hidden="true" />
          </div>
          <div className="legacy-content" style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
              <h4 style={{ fontSize: '13px', fontWeight: '700', margin: 0, color: 'var(--text-primary)' }}>Daily Legacy</h4>
              <span style={{ fontSize: '12px', fontWeight: '800', color: 'var(--cyan)', flexShrink: 0, marginLeft: '6px' }}>
                {progress.percentage ?? 0}%
              </span>
            </div>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px', marginBottom: '2px', fontWeight: '500' }}>
              {progress.completed || 0} / {progress.total || 0} Actions Done
            </p>
            <p style={{ fontSize: '10px', color: 'var(--text-tertiary)', margin: 0 }}>
              {(progress.percentage || 0) === 100
                ? 'All protocols complete!'
                : ((progress.total || 0) - (progress.completed || 0)) > 0
                ? `${(progress.total || 0) - (progress.completed || 0)} actions remaining`
                : 'No actions scheduled'}
            </p>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
          <div style={{ 
            height: '100%', 
            width: `${Math.max(0, Math.min(100, progress.percentage || 0))}%`, 
            background: 'var(--cyan)',
            transition: 'width 0.5s ease-out'
          }} />
        </div>
        
        <Link to="/analytics" style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '12px',
          fontWeight: '600',
          color: 'var(--cyan)',
          textDecoration: 'none',
          paddingTop: '2px'
        }}>
          View Progress
          <ArrowRight size={14} />
        </Link>
        <div className="legacy-glow-bar" />
      </div>
    </aside>
  );
};

export default Sidebar;