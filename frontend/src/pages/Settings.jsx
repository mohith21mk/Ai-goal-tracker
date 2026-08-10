import { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import { getSettings, updateSettings } from '../services/api';
import './Settings.css';

const Settings = () => {
  const [theme, setTheme] = useState('dark');
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [coachStyle, setCoachStyle] = useState('strategic');
  const [dailyReminderTime, setDailyReminderTime] = useState('08:00');
  const [profileVisibility, setProfileVisibility] = useState('public');

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function load() {
      try {
        const s = await getSettings();
        if (isMounted && s) {
          const loadedTheme = s.theme || 'dark';
          setTheme(loadedTheme);
          document.documentElement.setAttribute('data-theme', loadedTheme);
          localStorage.setItem('theme', loadedTheme);

          setNotificationsEnabled(Boolean(s.notifications_enabled));
          setCoachStyle(s.coach_style || 'strategic');
          setDailyReminderTime(s.daily_reminder_time || '08:00');
          setProfileVisibility(s.profile_visibility || 'public');
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to load settings:', err);
          setStatusMessage({ type: 'error', text: 'Could not load preferences from backend.' });
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleThemeChange = (newTheme) => {
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  };

  const handleNotificationToggle = (checked) => {
    setNotificationsEnabled(checked);
    if (checked && 'Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().catch(() => {});
    }
  };

  const handleSaveSettings = async (e) => {
    if (e) e.preventDefault();
    setSaving(true);
    setStatusMessage(null);

    try {
      const updated = await updateSettings({
        theme,
        notifications_enabled: notificationsEnabled,
        coach_style: coachStyle,
        daily_reminder_time: dailyReminderTime,
        profile_visibility: profileVisibility
      });

      if (updated) {
        const nextTheme = updated.theme || theme;
        setTheme(nextTheme);
        document.documentElement.setAttribute('data-theme', nextTheme);
        localStorage.setItem('theme', nextTheme);

        setNotificationsEnabled(Boolean(updated.notifications_enabled));
        setCoachStyle(updated.coach_style);
        setDailyReminderTime(updated.daily_reminder_time);
        setProfileVisibility(updated.profile_visibility);
      }

      setStatusMessage({ type: 'success', text: 'Settings updated and live application synchronized!' });
    } catch (err) {
      console.error('Failed to update settings:', err);
      setStatusMessage({ type: 'error', text: err.message || 'Failed to save settings.' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-viewport">
        <TopBar />
        <div className="settings-container">
          {/* Header */}
          <div className="settings-header">
            <h1 className="font-serif">System Preferences</h1>
            <p>Customize your AI Coach persona, notification protocols, and privacy parameters.</p>
          </div>

          {statusMessage && (
            <div style={{
              padding: '12px 16px',
              background: statusMessage.type === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(56, 189, 248, 0.1)',
              border: `1px solid ${statusMessage.type === 'error' ? '#EF4444' : 'var(--cyan)'}`,
              borderRadius: '12px',
              color: statusMessage.type === 'error' ? '#EF4444' : 'var(--cyan)',
              marginBottom: '24px',
              fontSize: '13px'
            }}>
              {statusMessage.type === 'error' ? '⚠️' : '✅'} {statusMessage.text}
            </div>
          )}

          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-tertiary)' }}>Loading System Preferences...</div>
          ) : (
            <form onSubmit={handleSaveSettings}>
              <div className="settings-grid">
                {/* 1. Appearance */}
                <div className="settings-card glass-panel">
                  <div className="settings-card-header">
                    <span className="settings-card-icon">🎨</span>
                    <h3>Appearance & Interface</h3>
                  </div>
                  <p className="settings-card-desc">Choose the visual theme for your mastery operating system.</p>

                  <div className="settings-field-group">
                    <label className="settings-label">Theme Mode</label>
                    <div className="segmented-control">
                      <button
                        type="button"
                        onClick={() => handleThemeChange('dark')}
                        className={`segmented-btn ${theme === 'dark' ? 'active' : ''}`}
                      >
                        🌙 Dark Cyberpunk
                      </button>
                      <button
                        type="button"
                        onClick={() => handleThemeChange('light')}
                        className={`segmented-btn ${theme === 'light' ? 'active' : ''}`}
                      >
                        ☀️ Light Mode
                      </button>
                    </div>
                  </div>
                </div>

                {/* 2. AI Coach Persona */}
                <div className="settings-card glass-panel">
                  <div className="settings-card-header">
                    <span className="settings-card-icon">🤖</span>
                    <h3>AI Coach Persona</h3>
                  </div>
                  <p className="settings-card-desc">Configure the tone and advice style of your AI mentor.</p>

                  <div className="settings-field-group">
                    <label className="settings-label">Coaching Philosophy</label>
                    <select
                      value={coachStyle}
                      onChange={(e) => setCoachStyle(e.target.value)}
                      className="settings-select"
                    >
                      <option value="strategic">Strategic (Direct, analytical, data-driven)</option>
                      <option value="empathetic">Empathetic (Supportive, encouraging, balanced)</option>
                      <option value="relentless">Relentless (High-intensity, non-negotiable execution)</option>
                    </select>
                  </div>
                </div>

                {/* 3. Notifications & Reminders */}
                <div className="settings-card glass-panel">
                  <div className="settings-card-header">
                    <span className="settings-card-icon">🔔</span>
                    <h3>Notifications & Protocols</h3>
                  </div>
                  <p className="settings-card-desc">Manage system alerts and daily discipline reminders.</p>

                  <div className="toggle-switch-wrapper">
                    <div>
                      <div className="toggle-switch-label">Enable Daily Reminders</div>
                      <div className="toggle-switch-sub">Receive daily protocol push prompts</div>
                    </div>
                    <input
                      type="checkbox"
                      checked={notificationsEnabled}
                      onChange={(e) => handleNotificationToggle(e.target.checked)}
                      style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                    />
                  </div>

                  <div className="settings-field-group">
                    <label className="settings-label">Daily Reminder Time</label>
                    <input
                      type="text"
                      placeholder="08:00"
                      value={dailyReminderTime}
                      onChange={(e) => setDailyReminderTime(e.target.value)}
                      className="settings-input"
                    />
                    <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '4px' }}>
                      {notificationsEnabled
                        ? `⚡ In-App Protocol Reminder set for ${dailyReminderTime} ${
                            typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'granted'
                              ? '(Browser Push Granted)'
                              : '(In-App Protocol Active)'
                          }`
                        : 'Reminders currently disabled.'}
                    </div>
                  </div>
                </div>

                {/* 4. Privacy & Visibility */}
                <div className="settings-card glass-panel">
                  <div className="settings-card-header">
                    <span className="settings-card-icon">🛡️</span>
                    <h3>Profile & Privacy</h3>
                  </div>
                  <p className="settings-card-desc">Control whether your profile is visible in the community feed.</p>

                  <div className="settings-field-group">
                    <label className="settings-label">Profile Visibility</label>
                    <select
                      value={profileVisibility}
                      onChange={(e) => setProfileVisibility(e.target.value)}
                      className="settings-select"
                    >
                      <option value="public">Public (Visible in Community Feed)</option>
                      <option value="private">Private (Masked as Anonymous Member)</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Save Footer */}
              <div className="settings-save-footer glass-panel">
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  All changes persist cleanly to your SQLite database and update live.
                </div>
                <button
                  type="submit"
                  disabled={saving}
                  className="btn-save-settings"
                >
                  {saving ? 'Saving Changes...' : 'Save Preferences'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
