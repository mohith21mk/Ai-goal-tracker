import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  Zap, 
  Target, 
  ClipboardList, 
  MapPin, 
  Moon, 
  Bell,
  LogOut,
  CheckCheck,
  Trash2,
  MessageSquare,
  ShieldCheck
} from 'lucide-react';
import {
  searchApplication,
  getUser,
  logoutUser,
  getNotifications,
  getUnreadNotificationCount,
  markNotificationRead,
  markAllNotificationsRead,
  deleteNotification
} from '../services/api';
import { useNotificationsSocket } from '../hooks/useNotificationsSocket';
import FeedbackModal from './FeedbackModal';
import { ROUTES } from '../constants/routes';
import './TopBar.css';

const TopBar = ({ user }) => {
  const [searchValue, setSearchValue] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false);
  const [isNotifDropdownOpen, setIsNotifDropdownOpen] = useState(false);
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [userProfile, setUserProfile] = useState(user || null);
  const searchInputRef = useRef(null);
  const navigate = useNavigate();

  const handleIncomingNotification = useCallback((notif) => {
    setNotifications((prev) => {
      if (prev.some((n) => n.id === notif.id)) return prev;
      return [notif, ...prev];
    });
    setUnreadCount((prev) => prev + 1);
  }, []);

  useNotificationsSocket(handleIncomingNotification);


  const handleMarkSingleRead = async (id, e) => {
    if (e) e.stopPropagation();
    try {
      await markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: 1 } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Failed to mark read:', err);
    }
  };

  const handleNotificationClick = async (n) => {
    if (!n) return;
    if (!n.is_read) {
      handleMarkSingleRead(n.id);
    }
    setIsNotifDropdownOpen(false);

    const notifType = n.type || n.data?.type || n.reference_type;
    const reqId = n.request_id || n.data?.request_id || (notifType === 'connection_request' ? n.reference_id : null);
    const convId = n.conversation_id || n.data?.conversation_id || (notifType === 'message' || notifType === 'chat_message' ? n.reference_id : null);
    const senderId = n.sender_id || n.data?.sender_id;
    const credId = n.credential_id || n.data?.credential_id || (notifType === 'credential_unlocked' ? n.reference_id : null);

    if (notifType === 'connection_request') {
      const qs = reqId ? `&requestId=${reqId}` : '';
      navigate(`${ROUTES.CHAT_ALIAS}?tab=requests${qs}`, { state: { tab: 'requests', requestId: reqId, senderId } });
    } else if (notifType === 'message' || notifType === 'chat_message' || notifType === 'new_message') {
      const convParam = convId ? `&conversationId=${convId}` : (senderId ? `&userId=${senderId}` : '');
      navigate(`${ROUTES.CHAT_ALIAS}?tab=conversations${convParam}`, { state: { tab: 'conversations', conversationId: convId, userId: senderId } });
    } else if (notifType === 'connection_accepted') {
      const userParam = senderId ? `&userId=${senderId}` : '';
      navigate(`${ROUTES.CHAT_ALIAS}?tab=conversations${userParam}`, { state: { tab: 'conversations', userId: senderId } });
    } else if (notifType === 'post_like' || notifType === 'post_comment') {
      navigate(ROUTES.COMMUNITY);
    } else if (notifType === 'credential_unlocked' || notifType === 'level_up') {
      const credParam = credId ? `?cred=${credId}` : '';
      navigate(`${ROUTES.PROFILE}${credParam}`);
    } else if (notifType === 'admin_feedback') {
      navigate(ROUTES.SETTINGS);
    } else {
      navigate(ROUTES.DASHBOARD);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: 1 })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all read:', err);
    }
  };

  const handleDeleteNotif = async (id, e) => {
    if (e) e.stopPropagation();
    try {
      await deleteNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Failed to delete notification:', err);
    }
  };

  const handleLogout = async () => {
    try {
      await logoutUser();
      navigate(ROUTES.LOGIN);
    } catch (err) {
      console.error('Logout failed:', err);
      navigate(ROUTES.LOGIN);
    }
  };

  useEffect(() => {
    let isMounted = true;
    async function loadTopBarData() {
      try {
        const [u, notifList, unreadData] = await Promise.all([
          getUser().catch(() => null),
          getNotifications(20, 0).catch(() => []),
          getUnreadNotificationCount().catch(() => ({ unread_count: 0 })),
        ]);
        if (isMounted) {
          if (u) setUserProfile(u);
          if (notifList) setNotifications(notifList);
          if (unreadData) setUnreadCount(unreadData.unread_count || 0);
        }
      } catch (err) {
        console.warn('TopBar data sync warning:', err);
      }
    }
    loadTopBarData();

    const handleProgressUpdate = () => {
      loadTopBarData();
    };
    window.addEventListener('mkc:progress-updated', handleProgressUpdate);

    return () => {
      isMounted = false;
      window.removeEventListener('mkc:progress-updated', handleProgressUpdate);
    };
  }, []);

  const displayName = userProfile?.full_name || user?.full_name || 'Mohith K';
  const usernameDisplay = userProfile?.username ? `@${userProfile.username}` : (user?.username ? `@${user.username}` : '@mohith_ai');
  const avatarInitials = userProfile?.avatar_initials || 'MK';

  // Debounced search logic (250ms)
  useEffect(() => {
    const trimmed = searchValue.trim();
    if (!trimmed) {
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await searchApplication(trimmed);
        setSearchResults(results);
        setIsDropdownOpen(true);
      } catch (err) {
        console.error('Search failed:', err);
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [searchValue]);

  const handleInputChange = (e) => {
    const val = e.target.value;
    setSearchValue(val);
    if (!val.trim()) {
      setSearchResults(null);
      setIsDropdownOpen(false);
    }
  };

  // Keyboard shortcut listener (Ctrl+K / Cmd+K)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (searchInputRef.current) {
          searchInputRef.current.focus();
        }
      } else if (e.key === 'Escape') {
        setIsDropdownOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleResultClick = (route) => {
    setIsDropdownOpen(false);
    setSearchValue('');
    navigate(route);
  };

  const handleThemeToggleQuick = () => {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  };

  return (
    <header className="topbar-container" style={{ position: 'relative' }}>
      {/* Search Input Field */}
      <div className="topbar-search glass-panel">
        <Search className="search-icon" size={18} strokeWidth={1.8} aria-hidden="true" style={{ color: 'var(--text-tertiary)' }} />
        <input
          ref={searchInputRef}
          type="text"
          placeholder="Search habits, goals, missions, blueprint..."
          value={searchValue}
          onChange={handleInputChange}
          onFocus={() => { if (searchResults && searchResults.count > 0) setIsDropdownOpen(true); }}
          className="search-input"
        />
        <kbd className="search-shortcut">⌘K</kbd>
      </div>

      {/* Live Search Results Dropdown */}
      {isDropdownOpen && searchResults && (
        <div style={{
          position: 'absolute',
          top: '60px',
          left: '0',
          width: '460px',
          maxHeight: '420px',
          overflowY: 'auto',
          background: 'var(--bg-modal, rgba(7, 20, 38, 0.95))',
          backdropFilter: 'blur(16px)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '16px',
          boxShadow: '0 8px 32px var(--mkc-shadow, rgba(0, 0, 0, 0.4))',
          padding: '16px',
          zIndex: 999,
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--cyan)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              {isSearching ? 'Searching...' : `Found ${searchResults.count} Results`}
            </span>
            <button onClick={() => setIsDropdownOpen(false)} style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', fontSize: '12px' }}>
              Esc to close
            </button>
          </div>

          {searchResults.count === 0 ? (
            <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '13px' }}>
              No matches found for "{searchValue}"
            </div>
          ) : (
            <>
              {/* Habits */}
              {searchResults.habits?.length > 0 && (
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: '600', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Zap size={18} strokeWidth={1.8} aria-hidden="true" /> HABITS ({searchResults.habits.length})
                  </div>
                  {searchResults.habits.map(h => (
                    <div
                      key={h.id}
                      onClick={() => handleResultClick('/habits')}
                      style={{ padding: '8px 12px', background: 'rgba(10, 22, 40, 0.6)', borderRadius: '8px', cursor: 'pointer', marginBottom: '4px', transition: 'background 0.2s' }}
                      onMouseOver={(e) => e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)'}
                      onMouseOut={(e) => e.currentTarget.style.background = 'rgba(10, 22, 40, 0.6)'}
                    >
                      <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>{h.title}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>{h.category} • {h.status}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Goals */}
              {searchResults.goals?.length > 0 && (
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: '600', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Target size={18} strokeWidth={1.8} aria-hidden="true" /> GOALS ({searchResults.goals.length})
                  </div>
                  {searchResults.goals.map(g => (
                    <div
                      key={g.id}
                      onClick={() => handleResultClick('/goals')}
                      style={{ padding: '8px 12px', background: 'rgba(10, 22, 40, 0.6)', borderRadius: '8px', cursor: 'pointer', marginBottom: '4px' }}
                      onMouseOver={(e) => e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)'}
                      onMouseOut={(e) => e.currentTarget.style.background = 'rgba(10, 22, 40, 0.6)'}
                    >
                      <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>{g.title}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>{g.category} • {g.status}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Missions */}
              {searchResults.missions?.length > 0 && (
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: '600', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <ClipboardList size={18} strokeWidth={1.8} aria-hidden="true" /> MISSIONS ({searchResults.missions.length})
                  </div>
                  {searchResults.missions.map(m => (
                    <div
                      key={m.id}
                      onClick={() => handleResultClick('/missions')}
                      style={{ padding: '8px 12px', background: 'rgba(10, 22, 40, 0.6)', borderRadius: '8px', cursor: 'pointer', marginBottom: '4px' }}
                      onMouseOver={(e) => e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)'}
                      onMouseOut={(e) => e.currentTarget.style.background = 'rgba(10, 22, 40, 0.6)'}
                    >
                      <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>{m.title}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>{m.category || 'general'} • {m.completed ? 'Completed' : 'Pending'}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Blueprint Milestones */}
              {searchResults.milestones?.length > 0 && (
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: '600', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <MapPin size={18} strokeWidth={1.8} aria-hidden="true" /> MILESTONES ({searchResults.milestones.length})
                  </div>
                  {searchResults.milestones.map(ms => (
                    <div
                      key={ms.id}
                      onClick={() => handleResultClick('/blueprint')}
                      style={{ padding: '8px 12px', background: 'rgba(10, 22, 40, 0.6)', borderRadius: '8px', cursor: 'pointer', marginBottom: '4px' }}
                      onMouseOver={(e) => e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)'}
                      onMouseOut={(e) => e.currentTarget.style.background = 'rgba(10, 22, 40, 0.6)'}
                    >
                      <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>{ms.title}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>Target: {ms.target_date || 'N/A'}</div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Brand Text - Centered */}
      <div style={{
        flex: 1,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        pointerEvents: 'none',
        padding: '0 12px',
        minWidth: 0,
        overflow: 'hidden'
      }}>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontSize: '14px',
          fontWeight: '700',
          letterSpacing: '1.5px',
          color: 'var(--text-primary)',
          opacity: 0.9,
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis'
        }}>MASTERY KEY <span style={{ color: 'var(--cyan)' }}>•</span> COACH</span>
      </div>

      {/* Right User & AI Status Area */}
      <div className="topbar-actions">
        {/* Quick Theme Switch Button */}
        <button
          onClick={handleThemeToggleQuick}
          title="Toggle Theme"
          aria-label="Toggle theme"
          style={{
            padding: '6px 10px',
            background: 'var(--bg-chip, rgba(10, 22, 40, 0.6))',
            border: '1px solid var(--border-subtle)',
            borderRadius: '9999px',
            color: 'var(--text-primary)',
            fontSize: '12px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <Moon size={18} strokeWidth={1.8} aria-hidden="true" />
          <span>Theme</span>
        </button>

        {/* Notification Bell with Badge & Dropdown */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setIsNotifDropdownOpen(!isNotifDropdownOpen)}
            className="notification-bell-btn"
            title="Notifications"
            aria-label="Toggle notifications"
            style={{
              padding: '8px',
              background: 'var(--bg-chip, rgba(10, 22, 40, 0.6))',
              border: '1px solid var(--border-subtle)',
              borderRadius: '50%',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative'
            }}
          >
            <Bell size={18} strokeWidth={1.8} aria-hidden="true" />
            {unreadCount > 0 && (
              <span style={{
                position: 'absolute',
                top: '-4px',
                right: '-4px',
                background: 'var(--cyan)',
                color: '#090D16',
                borderRadius: '9999px',
                padding: '2px 5px',
                fontSize: '10px',
                fontWeight: '700',
                lineHeight: 1
              }}>
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>

          {/* Notifications Dropdown Panel */}
          {isNotifDropdownOpen && (
            <div style={{
              position: 'absolute',
              top: 'calc(100% + 12px)',
              right: 0,
              width: '320px',
              maxHeight: '420px',
              background: 'var(--bg-modal, rgba(7, 20, 38, 0.95))',
              backdropFilter: 'blur(16px)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              boxShadow: '0 8px 32px var(--mkc-shadow, rgba(0, 0, 0, 0.5))',
              zIndex: 1000,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}>
              <div style={{
                padding: '12px 16px',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)' }}>
                  Notifications {unreadCount > 0 && `(${unreadCount})`}
                </span>
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllRead}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--cyan)',
                      fontSize: '11px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <CheckCheck size={14} /> Mark all read
                  </button>
                )}
              </div>

              <div style={{ overflowY: 'auto', flex: 1, padding: '8px 0' }}>
                {notifications.length === 0 ? (
                  <div style={{ padding: '24px 16px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '12px' }}>
                    No system notifications.
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      onClick={() => handleNotificationClick(n)}
                      style={{
                        padding: '10px 16px',
                        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                        background: n.is_read ? 'transparent' : 'rgba(56, 189, 248, 0.06)',
                        display: 'flex',
                        gap: '10px',
                        cursor: 'pointer',
                        transition: 'background 0.2s'
                      }}
                      onMouseOver={(e) => e.currentTarget.style.background = 'rgba(56, 189, 248, 0.12)'}
                      onMouseOut={(e) => e.currentTarget.style.background = n.is_read ? 'transparent' : 'rgba(56, 189, 248, 0.06)'}
                    >
                      <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: n.is_read ? 'transparent' : 'var(--cyan)', marginTop: '6px', flexShrink: 0 }} />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: '12px', fontWeight: n.is_read ? '500' : '700', color: 'var(--text-primary)', marginBottom: '2px' }}>
                          {n.title}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', lineHeight: '1.4', marginBottom: '4px' }}>
                          {n.message}
                        </div>
                        <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', opacity: 0.7 }}>
                          {n.created_at || 'Just now'}
                        </div>
                      </div>
                      <button
                        onClick={(e) => handleDeleteNotif(n.id, e)}
                        title="Delete notification"
                        style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', opacity: 0.6, padding: '2px' }}
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* AI Coach Online Pill */}
        <div className="ai-status-pill">
          <span className="pulsing-dot" />
          <span className="ai-status-text">AI Coach Online</span>
        </div>

        {/* User Profile & Badge */}
        <div style={{ position: 'relative' }}>
          <div
            onClick={() => setIsProfileDropdownOpen(!isProfileDropdownOpen)}
            className="user-profile-wrapper glass-panel"
            style={{ cursor: 'pointer', transition: 'all 0.2s' }}
            title="Profile Options"
          >
            <div className="user-level-badge">
              <Zap className="badge-star" size={18} strokeWidth={1.8} aria-hidden="true" />
              <span className="badge-text">{displayName} • {usernameDisplay}</span>
            </div>
            <div className="avatar-wrapper" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 32, height: 32, borderRadius: '50%', background: 'rgba(56, 189, 248, 0.15)', border: '1px solid var(--cyan)', color: 'var(--cyan)', fontWeight: '700', fontSize: '12px' }}>
              {avatarInitials}
            </div>
          </div>
          
          {/* Profile Dropdown Menu */}
          {isProfileDropdownOpen && (
            <div style={{
              position: 'absolute',
              top: 'calc(100% + 12px)',
              right: 0,
              width: '220px',
              background: 'var(--bg-modal, rgba(7, 20, 38, 0.95))',
              backdropFilter: 'blur(16px)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              padding: '8px',
              boxShadow: '0 8px 32px var(--mkc-shadow, rgba(0, 0, 0, 0.4))',
              zIndex: 1000,
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}>
              <div
                onClick={() => {
                  setIsProfileDropdownOpen(false);
                  navigate(ROUTES.PROFILE);
                }}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: '600',
                  color: 'var(--text-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'background 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)'}
                onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
              >
                My Identity Profile
              </div>
              {userProfile?.role === 'admin' && (
                <div
                  onClick={() => {
                    setIsProfileDropdownOpen(false);
                    navigate(ROUTES.ADMIN);
                  }}
                  style={{
                    padding: '10px 12px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: '600',
                    color: '#EC4899',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    transition: 'background 0.2s'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.background = 'rgba(236, 72, 153, 0.15)'}
                  onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <ShieldCheck size={16} strokeWidth={1.8} />
                  Admin Dashboard
                </div>
              )}
              <div
                onClick={() => {
                  setIsProfileDropdownOpen(false);
                  setIsFeedbackOpen(true);
                }}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: '600',
                  color: 'var(--text-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'background 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)'}
                onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <MessageSquare size={16} strokeWidth={1.8} />
                Send Feedback
              </div>
              <div style={{ height: '1px', background: 'var(--border-subtle)', margin: '4px 0' }} />
              <div
                onClick={handleLogout}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: '600',
                  color: 'var(--accent-red, #ef4444)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'background 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.15)'}
                onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <LogOut size={16} strokeWidth={2} />
                Sign Out
              </div>
            </div>
          )}
        </div>
      </div>

      <FeedbackModal
        isOpen={isFeedbackOpen}
        onClose={() => setIsFeedbackOpen(false)}
      />
    </header>
  );
};

export default TopBar;

