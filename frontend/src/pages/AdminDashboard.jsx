import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldCheck, 
  Users, 
  Activity, 
  MessageSquare, 
  TrendingUp, 
  Zap, 
  Rocket, 
  Search, 
  CheckCircle2, 
  Lock,
  RefreshCw
} from 'lucide-react';
import { 
  getUser, 
  getAdminOverview, 
  getAdminUsers, 
  updateUserRole, 
  updateUserStatus, 
  getAdminFeedback, 
  updateAdminFeedback, 
  getAdminFeedbackStats 
} from '../services/api';
import { ROUTES } from '../constants/routes';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [feedbackMessage, setFeedbackMessage] = useState(null);

  // Overview State
  const [overview, setOverview] = useState(null);

  // Users Directory State
  const [usersData, setUsersData] = useState({ items: [], total: 0, limit: 25, offset: 0 });
  const [userSearch, setUserSearch] = useState('');
  const [userRoleFilter, setUserRoleFilter] = useState('');
  const [userStatusFilter, setUserStatusFilter] = useState('');

  // Feedback Moderation State
  const [feedbackList, setFeedbackList] = useState({ items: [], total: 0 });
  const [feedbackFilterStatus, setFeedbackFilterStatus] = useState('');
  const [feedbackStats, setFeedbackStats] = useState(null);
  const [editingNotesId, setEditingNotesId] = useState(null);
  const [adminNotesText, setAdminNotesText] = useState('');

  const loadData = useCallback(async () => {
    try {
      const u = await getUser().catch(() => null);
      setCurrentUser(u);

      if (u && u.role === 'admin') {
        const [overviewRes, usersRes, fbRes, fbStatsRes] = await Promise.all([
          getAdminOverview().catch(() => null),
          getAdminUsers({ limit: 25, offset: 0 }).catch(() => ({ items: [], total: 0 })),
          getAdminFeedback({ limit: 50, offset: 0 }).catch(() => ({ items: [], total: 0 })),
          getAdminFeedbackStats().catch(() => null),
        ]);

        if (overviewRes) setOverview(overviewRes);
        if (usersRes) setUsersData(usersRes);
        if (fbRes) setFeedbackList(fbRes);
        if (fbStatsRes) setFeedbackStats(fbStatsRes);
      }
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    async function init() {
      if (isMounted) await loadData();
    }
    init();
    return () => { isMounted = false; };
  }, [loadData]);

  const handleUserSearch = async (e) => {
    e.preventDefault();
    try {
      const res = await getAdminUsers({
        q: userSearch,
        role: userRoleFilter || undefined,
        is_active: userStatusFilter !== '' ? userStatusFilter === 'active' : undefined,
        limit: 25,
        offset: 0
      });
      setUsersData(res);
    } catch (err) {
      console.error('User search failed:', err);
    }
  };

  const handleRoleToggle = async (userId, currentRole) => {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';
    if (!window.confirm(`Are you sure you want to change user ${userId} role to '${newRole}'?`)) return;

    try {
      await updateUserRole(userId, newRole);
      setUsersData(prev => ({
        ...prev,
        items: prev.items.map(u => u.id === userId ? { ...u, role: newRole } : u)
      }));
      setFeedbackMessage({ type: 'success', text: `User role successfully updated to ${newRole}.` });
      setTimeout(() => setFeedbackMessage(null), 3000);
    } catch (err) {
      alert(err.message || 'Failed to update role.');
    }
  };

  const handleStatusToggle = async (userId, currentActive) => {
    const newActive = !currentActive;
    if (!window.confirm(`Are you sure you want to ${newActive ? 'activate' : 'deactivate'} user ${userId}?`)) return;

    try {
      await updateUserStatus(userId, newActive);
      setUsersData(prev => ({
        ...prev,
        items: prev.items.map(u => u.id === userId ? { ...u, is_active: newActive ? 1 : 0 } : u)
      }));
      setFeedbackMessage({ type: 'success', text: `User account status updated.` });
      setTimeout(() => setFeedbackMessage(null), 3000);
    } catch (err) {
      alert(err.message || 'Failed to update status.');
    }
  };

  const handleFeedbackFilter = async (status) => {
    setFeedbackFilterStatus(status);
    try {
      const res = await getAdminFeedback({
        status: status || undefined,
        limit: 50,
        offset: 0
      });
      setFeedbackList(res);
    } catch (err) {
      console.error('Feedback filter error:', err);
    }
  };

  const handleFeedbackStatusChange = async (feedbackId, newStatus) => {
    try {
      const updated = await updateAdminFeedback(feedbackId, { status: newStatus });
      setFeedbackList(prev => ({
        ...prev,
        items: prev.items.map(item => item.id === feedbackId ? { ...item, status: updated.status } : item)
      }));
      const freshStats = await getAdminFeedbackStats().catch(() => null);
      if (freshStats) setFeedbackStats(freshStats);
    } catch (err) {
      alert(err.message || 'Failed to update feedback status.');
    }
  };

  const handleSaveNotes = async (feedbackId) => {
    try {
      const updated = await updateAdminFeedback(feedbackId, { admin_notes: adminNotesText });
      setFeedbackList(prev => ({
        ...prev,
        items: prev.items.map(item => item.id === feedbackId ? { ...item, admin_notes: updated.admin_notes } : item)
      }));
      setEditingNotesId(null);
      setAdminNotesText('');
    } catch (err) {
      alert(err.message || 'Failed to save admin notes.');
    }
  };

  if (!loading && (!currentUser || currentUser.role !== 'admin')) {
    return (
      <div className="admin-page-layout">
        <div className="admin-forbidden-card glass-panel">
          <div className="forbidden-icon">
            <Lock size={32} />
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: '800', margin: 0, color: 'var(--text-primary)' }}>
            Administrator Privileges Required
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
            This workspace is protected. You must be authenticated as an authorized system administrator to view executive analytics and directory telemetry.
          </p>
          <Link to={ROUTES.DASHBOARD} className="feedback-btn" style={{ textDecoration: 'none', padding: '10px 20px', marginTop: '12px' }}>
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const maxGrowth = overview?.user_growth_timeline ? Math.max(...overview.user_growth_timeline.map(t => t.count), 1) : 1;

  return (
    <div className="admin-page-layout">
          {/* Header Banner */}
          <header className="admin-header-card glass-panel">
            <div className="admin-header-title-group">
              <div className="admin-shield-icon">
                <ShieldCheck size={26} strokeWidth={2} />
              </div>
              <div>
                <h1 className="admin-title font-display">Owner & System Administration</h1>
                <p className="admin-subtitle">
                  Executive analytics, registered user telemetry, and live user feedback moderation.
                </p>
              </div>
            </div>

            <div className="admin-header-badges">
              <div className="admin-status-badge">
                <span className="admin-status-dot" />
                <span>Production Health: Optimal</span>
              </div>
              <button 
                onClick={loadData} 
                className="feedback-btn" 
                title="Refresh Intelligence Data"
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                Refresh
              </button>
            </div>
          </header>

          {/* Feedback Alert Message */}
          {feedbackMessage && (
            <div style={{
              padding: '12px 18px',
              borderRadius: '10px',
              background: feedbackMessage.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              border: `1px solid ${feedbackMessage.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
              color: feedbackMessage.type === 'success' ? '#10B981' : '#EF4444',
              fontSize: '13px',
              fontWeight: '600'
            }}>
              {feedbackMessage.text}
            </div>
          )}

          {/* Navigation Tabs Bar */}
          <div className="admin-tabs-bar">
            <button
              onClick={() => setActiveTab('overview')}
              className={`admin-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            >
              <Activity size={16} />
              Overview & Analytics
            </button>

            <button
              onClick={() => setActiveTab('users')}
              className={`admin-tab-btn ${activeTab === 'users' ? 'active' : ''}`}
            >
              <Users size={16} />
              User Directory
              {overview && <span className="tab-badge">{overview.total_users}</span>}
            </button>

            <button
              onClick={() => setActiveTab('feedback')}
              className={`admin-tab-btn ${activeTab === 'feedback' ? 'active' : ''}`}
            >
              <MessageSquare size={16} />
              Feedback Moderation
              {feedbackStats && feedbackStats.new > 0 && (
                <span className="tab-badge" style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#F59E0B' }}>
                  {feedbackStats.new} New
                </span>
              )}
            </button>
          </div>

          {/* ============================================================ */}
          {/* TAB 1: OVERVIEW & ENGAGEMENT                                 */}
          {/* ============================================================ */}
          {activeTab === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div className="admin-metrics-grid">
                <div className="admin-stat-card glass-panel">
                  <div className="admin-stat-header">
                    <span className="admin-stat-title">Total Registered</span>
                    <div className="admin-stat-icon" style={{ background: 'rgba(56, 189, 248, 0.15)', color: 'var(--cyan)' }}>
                      <Users size={18} />
                    </div>
                  </div>
                  <h3 className="admin-stat-val font-display">{overview?.total_users ?? '—'}</h3>
                  <span className="admin-stat-footer">+{overview?.new_users_7d || 0} in last 7 days</span>
                </div>

                <div className="admin-stat-card glass-panel">
                  <div className="admin-stat-header">
                    <span className="admin-stat-title">Active Users (7D)</span>
                    <div className="admin-stat-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10B981' }}>
                      <Activity size={18} />
                    </div>
                  </div>
                  <h3 className="admin-stat-val font-display">{overview?.active_users_7d ?? '—'}</h3>
                  <span className="admin-stat-footer">{overview?.active_users_30d || 0} active in 30 days</span>
                </div>

                <div className="admin-stat-card glass-panel">
                  <div className="admin-stat-header">
                    <span className="admin-stat-title">New Users (Today)</span>
                    <div className="admin-stat-icon" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#F59E0B' }}>
                      <TrendingUp size={18} />
                    </div>
                  </div>
                  <h3 className="admin-stat-val font-display">+{overview?.new_users_today ?? 0}</h3>
                  <span className="admin-stat-footer">+{overview?.new_users_30d || 0} this month</span>
                </div>

                <div className="admin-stat-card glass-panel">
                  <div className="admin-stat-header">
                    <span className="admin-stat-title">Total XP Awarded</span>
                    <div className="admin-stat-icon" style={{ background: 'rgba(167, 139, 250, 0.15)', color: '#A78BFA' }}>
                      <Rocket size={18} />
                    </div>
                  </div>
                  <h3 className="admin-stat-val font-display">{overview?.engagement?.total_xp_awarded?.toLocaleString() ?? 0}</h3>
                  <span className="admin-stat-footer">Compounded server XP</span>
                </div>
              </div>

              <div className="admin-growth-grid">
                <div className="admin-panel glass-panel">
                  <h3 className="admin-panel-title">
                    <TrendingUp size={18} style={{ color: 'var(--cyan)' }} />
                    14-Day New User Registration Trend
                  </h3>
                  <div className="timeline-bars">
                    {overview?.user_growth_timeline?.map((item, idx) => {
                      const heightPct = Math.max(8, Math.round((item.count / maxGrowth) * 100));
                      return (
                        <div key={idx} className="timeline-col" title={`${item.date}: ${item.count} new users`}>
                          <div 
                            className="timeline-bar" 
                            style={{ 
                              height: `${heightPct}%`,
                              background: item.count > 0 ? 'var(--cyan)' : 'var(--border-subtle)'
                            }} 
                          />
                          <span className="timeline-date">{item.date.slice(5)}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="admin-panel glass-panel">
                  <h3 className="admin-panel-title">
                    <Zap size={18} style={{ color: '#FBBF24' }} />
                    Platform Activity Pulse
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Missions Completed</span>
                      <strong className="font-display" style={{ color: 'var(--text-primary)' }}>
                        {overview?.engagement?.missions_completed ?? 0}
                      </strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Verified Habit Logs</span>
                      <strong className="font-display" style={{ color: 'var(--text-primary)' }}>
                        {overview?.engagement?.habit_logs ?? 0}
                      </strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Active Habits Tracked</span>
                      <strong className="font-display" style={{ color: 'var(--text-primary)' }}>
                        {overview?.engagement?.active_habits ?? 0}
                      </strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Life Blueprints Created</span>
                      <strong className="font-display" style={{ color: 'var(--text-primary)' }}>
                        {overview?.engagement?.blueprints_created ?? 0}
                      </strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px', borderTop: '1px solid var(--border-subtle)', paddingTop: '8px' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Pending Feedback Tickets</span>
                      <strong className="font-display" style={{ color: '#F59E0B' }}>
                        {overview?.feedback?.new ?? 0} Unreviewed
                      </strong>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ============================================================ */}
          {/* TAB 2: USER DIRECTORY & TELEMETRY                           */}
          {/* ============================================================ */}
          {activeTab === 'users' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <form onSubmit={handleUserSearch} className="admin-table-controls">
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', flex: 1 }}>
                  <div className="admin-search-input">
                    <Search size={16} style={{ color: 'var(--text-tertiary)' }} />
                    <input
                      type="text"
                      placeholder="Search name, username, email, MKC ID..."
                      value={userSearch}
                      onChange={(e) => setUserSearch(e.target.value)}
                    />
                  </div>

                  <select
                    className="admin-filter-select"
                    value={userRoleFilter}
                    onChange={(e) => setUserRoleFilter(e.target.value)}
                  >
                    <option value="">All Roles</option>
                    <option value="admin">Admins Only</option>
                    <option value="user">Standard Users</option>
                  </select>

                  <select
                    className="admin-filter-select"
                    value={userStatusFilter}
                    onChange={(e) => setUserStatusFilter(e.target.value)}
                  >
                    <option value="">All Statuses</option>
                    <option value="active">Active Only</option>
                    <option value="inactive">Inactive Only</option>
                  </select>

                  <button type="submit" className="feedback-btn" style={{ padding: '8px 16px' }}>
                    Filter Directory
                  </button>
                </div>

                <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Total Matching: <strong>{usersData.total}</strong> accounts
                </div>
              </form>

              <div className="admin-table-wrapper">
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>User / Identity</th>
                      <th>MKC ID</th>
                      <th>Role</th>
                      <th>Progression</th>
                      <th>Streak / Missions</th>
                      <th>Joined Date</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usersData.items.length === 0 ? (
                      <tr>
                        <td colSpan="7" style={{ textAlign: 'center', padding: '32px', color: 'var(--text-secondary)' }}>
                          No registered accounts matching search criteria.
                        </td>
                      </tr>
                    ) : (
                      usersData.items.map((u) => (
                        <tr key={u.id}>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                              <div style={{
                                width: 34,
                                height: 34,
                                borderRadius: '50%',
                                background: 'rgba(56, 189, 248, 0.15)',
                                border: '1px solid var(--cyan)',
                                color: 'var(--cyan)',
                                fontWeight: '700',
                                fontSize: '12px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                              }}>
                                {u.avatar_initials || 'U'}
                              </div>
                              <div>
                                <div style={{ fontWeight: '700', color: 'var(--text-primary)' }}>
                                  {u.full_name || 'Anonymous User'}
                                </div>
                                <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                                  @{u.username} • {u.email}
                                </div>
                              </div>
                            </div>
                          </td>

                          <td>
                            <code style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-chip)', color: 'var(--cyan)' }}>
                              {u.mkc_id || `MKC-USER-${u.id}`}
                            </code>
                          </td>

                          <td>
                            <span className={`role-badge ${u.role === 'admin' ? 'admin' : 'user'}`}>
                              {u.role === 'admin' ? <ShieldCheck size={12} /> : null}
                              {u.role}
                            </span>
                          </td>

                          <td>
                            <div>
                              <strong style={{ color: 'var(--text-primary)', fontSize: '13px' }}>
                                Level {u.level || 1}
                              </strong>
                              <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginLeft: '6px' }}>
                                ({u.total_xp || 0} XP • {u.rank || 'INITIATE'})
                              </span>
                            </div>
                          </td>

                          <td>
                            <div style={{ fontSize: '12px' }}>
                              <span>🔥 {u.streak_days || 0}d streak</span> • <span>🎯 {u.completed_missions || 0} missions</span>
                            </div>
                          </td>

                          <td>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                              {u.created_at ? new Date(u.created_at).toLocaleDateString() : 'N/A'}
                            </div>
                          </td>

                          <td>
                            <div style={{ display: 'flex', gap: '6px' }}>
                              <button
                                onClick={() => handleRoleToggle(u.id, u.role)}
                                className="feedback-btn"
                                style={{ padding: '4px 8px', fontSize: '11px' }}
                                title={u.role === 'admin' ? 'Demote to Standard User' : 'Promote to Admin'}
                              >
                                {u.role === 'admin' ? 'Demote' : 'Make Admin'}
                              </button>

                              <button
                                onClick={() => handleStatusToggle(u.id, u.is_active)}
                                className="feedback-btn"
                                style={{
                                  padding: '4px 8px',
                                  fontSize: '11px',
                                  color: u.is_active ? '#EF4444' : '#10B981',
                                  borderColor: u.is_active ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'
                                }}
                                title={u.is_active ? 'Deactivate Account' : 'Activate Account'}
                              >
                                {u.is_active ? 'Disable' : 'Enable'}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================ */}
          {/* TAB 3: FEEDBACK MODERATION QUEUE                            */}
          {/* ============================================================ */}
          {activeTab === 'feedback' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <button
                  onClick={() => handleFeedbackFilter('')}
                  className={`admin-tab-btn ${feedbackFilterStatus === '' ? 'active' : ''}`}
                >
                  All Tickets ({feedbackStats?.total ?? feedbackList.total})
                </button>
                <button
                  onClick={() => handleFeedbackFilter('new')}
                  className={`admin-tab-btn ${feedbackFilterStatus === 'new' ? 'active' : ''}`}
                >
                  🟡 New ({feedbackStats?.new ?? 0})
                </button>
                <button
                  onClick={() => handleFeedbackFilter('reviewing')}
                  className={`admin-tab-btn ${feedbackFilterStatus === 'reviewing' ? 'active' : ''}`}
                >
                  🔵 In Review ({feedbackStats?.reviewing ?? 0})
                </button>
                <button
                  onClick={() => handleFeedbackFilter('resolved')}
                  className={`admin-tab-btn ${feedbackFilterStatus === 'resolved' ? 'active' : ''}`}
                >
                  🟢 Resolved ({feedbackStats?.resolved ?? 0})
                </button>
              </div>

              <div className="feedback-list">
                {feedbackList.items.length === 0 ? (
                  <div className="admin-panel glass-panel" style={{ textAlign: 'center', padding: '48px' }}>
                    <CheckCircle2 size={36} style={{ color: '#10B981', margin: '0 auto 12px' }} />
                    <h3 style={{ fontSize: '16px', fontWeight: '700', margin: '0 0 4px', color: 'var(--text-primary)' }}>
                      No Feedback Tickets in this Queue
                    </h3>
                    <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
                      All user tickets in this status have been reviewed and resolved.
                    </p>
                  </div>
                ) : (
                  feedbackList.items.map((item) => (
                    <div key={item.id} className="feedback-card glass-panel">
                      <div className="feedback-header">
                        <div className="feedback-meta">
                          <span className="feedback-category-badge">{item.category}</span>
                          <span className={`feedback-status-badge ${item.status}`}>
                            {item.status}
                          </span>
                          <span>•</span>
                          <span>From: <strong>{item.user_email || item.username || `User #${item.user_id}`}</strong></span>
                          <span>•</span>
                          <span>{item.created_at ? new Date(item.created_at).toLocaleString() : 'Recently'}</span>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Status:</span>
                          <select
                            className="admin-filter-select"
                            style={{ padding: '4px 8px', fontSize: '12px' }}
                            value={item.status}
                            onChange={(e) => handleFeedbackStatusChange(item.id, e.target.value)}
                          >
                            <option value="new">New</option>
                            <option value="reviewing">Reviewing</option>
                            <option value="resolved">Resolved</option>
                            <option value="closed">Closed</option>
                          </select>
                        </div>
                      </div>

                      <p className="feedback-msg">{item.message}</p>

                      {item.page_url && (
                        <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
                          Submitted from: <code>{item.page_url}</code>
                        </div>
                      )}

                      {item.admin_notes && editingNotesId !== item.id && (
                        <div style={{
                          padding: '8px 12px',
                          borderRadius: '8px',
                          background: 'var(--bg-chip)',
                          borderLeft: '3px solid var(--cyan)',
                          fontSize: '12px',
                          color: 'var(--text-secondary)'
                        }}>
                          <strong>Admin Notes:</strong> {item.admin_notes}
                        </div>
                      )}

                      {editingNotesId === item.id ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '6px' }}>
                          <textarea
                            rows={2}
                            value={adminNotesText}
                            onChange={(e) => setAdminNotesText(e.target.value)}
                            placeholder="Add private administrator notes..."
                            style={{
                              padding: '8px 12px',
                              borderRadius: '8px',
                              background: 'var(--bg-input)',
                              border: '1px solid var(--border-subtle)',
                              color: 'var(--text-primary)',
                              fontSize: '12px',
                              outline: 'none',
                              resize: 'vertical'
                            }}
                          />
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button
                              onClick={() => handleSaveNotes(item.id)}
                              className="feedback-btn"
                              style={{ background: 'var(--cyan)', color: 'var(--text-on-accent)', borderColor: 'var(--cyan)' }}
                            >
                              Save Notes
                            </button>
                            <button
                              onClick={() => setEditingNotesId(null)}
                              className="feedback-btn"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="feedback-actions">
                          <button
                            onClick={() => {
                              setEditingNotesId(item.id);
                              setAdminNotesText(item.admin_notes || '');
                            }}
                            className="feedback-btn"
                            style={{ fontSize: '11px', padding: '4px 10px' }}
                          >
                            {item.admin_notes ? 'Edit Admin Notes' : '+ Add Admin Notes'}
                          </button>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
  );
};

export default AdminDashboard;
