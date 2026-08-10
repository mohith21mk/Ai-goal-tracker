import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchApplication, getSettings, getUser } from '../services/api';
import './TopBar.css';

const TopBar = ({ user }) => {
  const [searchValue, setSearchValue] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [settings, setSettings] = useState(null);
  const [userProfile, setUserProfile] = useState(user || null);
  const searchInputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    async function loadTopBarData() {
      try {
        const [s, u] = await Promise.all([
          getSettings().catch(() => null),
          getUser().catch(() => null),
        ]);
        if (isMounted) {
          if (s) setSettings(s);
          if (u) setUserProfile(u);
        }
      } catch (err) {
        console.warn('TopBar settings sync warning:', err);
      }
    }
    loadTopBarData();
    return () => { isMounted = false; };
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
        <svg className="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
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
          background: 'rgba(7, 20, 38, 0.95)',
          backdropFilter: 'blur(16px)',
          border: '1px solid var(--cyan)',
          borderRadius: '16px',
          boxShadow: '0 0 30px rgba(56, 189, 248, 0.3)',
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
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: '600', marginBottom: '6px' }}>⚡ HABITS ({searchResults.habits.length})</div>
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
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: '600', marginBottom: '6px' }}>🎯 GOALS ({searchResults.goals.length})</div>
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
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: '600', marginBottom: '6px' }}>📋 MISSIONS ({searchResults.missions.length})</div>
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
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: '600', marginBottom: '6px' }}>🗺️ MILESTONES ({searchResults.milestones.length})</div>
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

      {/* Right User & AI Status Area */}
      <div className="topbar-actions">
        {/* Quick Theme Switch Button */}
        <button
          onClick={handleThemeToggleQuick}
          title="Toggle Theme"
          style={{
            padding: '6px 10px',
            background: 'rgba(10, 22, 40, 0.6)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '9999px',
            color: 'var(--text-primary)',
            fontSize: '12px',
            cursor: 'pointer'
          }}
        >
          🌓 Theme
        </button>

        {/* Active Notification Protocol Indicator */}
        {settings?.notifications_enabled && (
          <div style={{
            fontSize: '11px',
            fontWeight: '600',
            color: 'var(--cyan)',
            padding: '4px 10px',
            background: 'rgba(56, 189, 248, 0.1)',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            borderRadius: '9999px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            <span>🔔</span>
            <span>{settings.daily_reminder_time || '08:00'} Protocol</span>
          </div>
        )}

        {/* AI Coach Online Pill */}
        <div className="ai-status-pill">
          <span className="pulsing-dot" />
          <span className="ai-status-text">AI Coach Online</span>
        </div>

        {/* User Profile & Badge */}
        <div
          onClick={() => navigate('/profile')}
          className="user-profile-wrapper glass-panel"
          style={{ cursor: 'pointer', transition: 'all 0.2s' }}
          title="View & Edit Identity Profile"
        >
          <div className="user-level-badge">
            <span className="badge-star">⚡</span>
            <span className="badge-text">{displayName} • {usernameDisplay}</span>
          </div>
          <div className="avatar-wrapper" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 32, height: 32, borderRadius: '50%', background: 'rgba(56, 189, 248, 0.15)', border: '1px solid var(--cyan)', color: 'var(--cyan)', fontWeight: '700', fontSize: '12px' }}>
            {avatarInitials}
          </div>
        </div>
      </div>
    </header>
  );
};

export default TopBar;
