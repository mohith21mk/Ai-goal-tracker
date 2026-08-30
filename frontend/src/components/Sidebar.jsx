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
import { getProgress, getDailyProgress, getConversations } from '../services/api';
import { useNotificationsSocket } from '../hooks/useNotificationsSocket';
import { ROUTES } from '../constants/routes';
import './Sidebar.css';

const rawNavItems = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    path: ROUTES.ROOT,
    icon: <LayoutDashboard size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'analytics',
    label: 'Analytics',
    path: ROUTES.ANALYTICS,
    icon: <BarChart3 size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'missions',
    label: 'Missions',
    path: ROUTES.MISSIONS,
    icon: <CheckSquare size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'goals',
    label: 'Goals',
    path: ROUTES.GOALS,
    icon: <Target size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'coach',
    label: 'AI Coach',
    path: ROUTES.COACH,
    icon: <Bot size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'habits',
    label: 'Habits',
    path: ROUTES.HABITS,
    icon: <Zap size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'journal',
    label: 'Journal',
    path: ROUTES.JOURNAL,
    icon: <BookOpen size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'blueprint',
    label: 'Life Blueprint',
    path: ROUTES.BLUEPRINT,
    icon: <Layers size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'settings',
    label: 'Settings',
    path: ROUTES.SETTINGS,
    icon: <Settings size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'community',
    label: 'Community',
    path: ROUTES.COMMUNITY,
    icon: <Users size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'chat',
    label: 'Messages',
    path: ROUTES.MESSAGES,
    icon: <MessageSquare size={18} strokeWidth={1.8} aria-hidden="true" />
  },
  {
    id: 'profile',
    label: 'My Identity',
    path: ROUTES.PROFILE,
    icon: <User size={18} strokeWidth={1.8} aria-hidden="true" />
  },
];

const Sidebar = () => {
  const location = useLocation();
  const [progress, setProgress] = useState({ completed: 0, total: 0, percentage: 0 });
  const [unreadChatCount, setUnreadChatCount] = useState(0);

  const loadUnreadChat = async () => {
    try {
      const convs = await getConversations();
      if (Array.isArray(convs)) {
        const total = convs.reduce((acc, c) => acc + (c.unread_count || 0), 0);
        setUnreadChatCount(total);
      }
    } catch {
      // Ignore background unread fetch failure
    }
  };

  useNotificationsSocket((notif) => {
    const nType = notif?.type || notif?.data?.type || notif?.reference_type;
    if (nType === 'chat_message' || nType === 'new_message') {
      loadUnreadChat();
    }
  });

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        const [dailyProg, convs] = await Promise.all([
          getDailyProgress().catch(() => getProgress().catch(() => null)),
          getConversations().catch(() => [])
        ]);
        if (isMounted) {
          if (dailyProg) {
            setProgress({
              completed: dailyProg.completed_actions !== undefined ? dailyProg.completed_actions : (dailyProg.completed || 0),
              total: dailyProg.total_actions !== undefined ? dailyProg.total_actions : (dailyProg.total || 0),
              percentage: dailyProg.completion_percentage !== undefined ? dailyProg.completion_percentage : (dailyProg.percentage || 0),
            });
          }
          if (Array.isArray(convs)) {
            const total = convs.reduce((acc, c) => acc + (c.unread_count || 0), 0);
            setUnreadChatCount(total);
          }
        }
      } catch (err) {
        console.warn('Sidebar data fetch error:', err);
      }
    }
    loadData();

    const handleProgressUpdate = () => {
      loadData();
    };
    window.addEventListener('mkc:progress-updated', handleProgressUpdate);

    return () => {
      isMounted = false;
      window.removeEventListener('mkc:progress-updated', handleProgressUpdate);
    };
  }, [location.pathname]);

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
          const isActive =
            item.id === 'goals'
              ? location.pathname === ROUTES.GOALS
              : item.id === 'missions'
              ? location.pathname === ROUTES.MISSIONS
              : item.id === 'coach'
              ? location.pathname === ROUTES.COACH || location.pathname === ROUTES.AI_COACH_ALIAS
              : item.id === 'habits'
              ? location.pathname === ROUTES.HABITS || location.pathname === ROUTES.STREAKS_ALIAS
              : item.id === 'journal'
              ? location.pathname === ROUTES.JOURNAL
              : item.id === 'blueprint'
              ? location.pathname === ROUTES.BLUEPRINT || location.pathname === ROUTES.LIFE_BLUEPRINT_ALIAS
              : item.id === 'settings'
              ? location.pathname === ROUTES.SETTINGS
              : item.id === 'community'
              ? location.pathname === ROUTES.COMMUNITY
              : item.id === 'chat'
              ? location.pathname === ROUTES.MESSAGES || location.pathname === ROUTES.CHAT_ALIAS
              : item.id === 'profile'
              ? location.pathname === ROUTES.PROFILE || location.pathname === ROUTES.MY_IDENTITY_ALIAS
              : item.id === 'analytics'
              ? location.pathname === ROUTES.ANALYTICS
              : (location.pathname === ROUTES.ROOT || location.pathname === ROUTES.DASHBOARD) && item.id === 'dashboard';

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
                  {item.id === 'chat' && unreadChatCount > 0 && (
                    <span className="sidebar-unread-pill">{unreadChatCount}</span>
                  )}
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
                {item.id === 'chat' && unreadChatCount > 0 && (
                  <span className="sidebar-unread-pill">{unreadChatCount}</span>
                )}
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
        
        <Link to={ROUTES.ANALYTICS} style={{
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