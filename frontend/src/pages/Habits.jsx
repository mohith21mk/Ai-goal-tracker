import { useState, useEffect, useRef } from 'react';
import { 
  Zap, 
  Trophy, 
  TrendingUp, 
  TriangleAlert, 
  Check, 
  Trash2, 
  X, 
  Sparkles, 
  Shield, 
  Crown,
  PartyPopper
} from 'lucide-react';
import {
  getHabits,
  getHabitStats,
  createHabit,
  deleteHabit,
  toggleHabit,
  getProgression
} from '../services/api';
import './Habits.css';

const Habits = () => {
  const [habits, setHabits] = useState([]);
  const [stats, setStats] = useState({
    total_active_habits: 0,
    avg_current_streak: 0,
    max_longest_streak: 0,
    overall_7day_completion_pct: 0,
    habits_completed_today: 0
  });
  const [progression, setProgression] = useState({
    level: 1,
    rank: 'INITIATE',
    total_xp: 0,
    current_level_xp: 0,
    next_level_xp: 500,
    progress_pct: 0,
    level_progress_percent: 0,
    xp_to_next_level: 500,
    xp_to_next: 500
  });
  const [levelUpEvent, setLevelUpEvent] = useState(null); // { oldLevel, newLevel, oldRank, newRank }
  const [floatingXp, setFloatingXp] = useState([]); // [{ id, habitId, text }]
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const prevProgressionRef = useRef(null);
  const animCounterRef = useRef(1);
  const animTimersRef = useRef(new Set());
  const isMountedRef = useRef(true);

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'wellness',
    frequency: 'daily',
    target_days_per_week: 7
  });

  const refreshHabits = async () => {
    try {
      const [habitsList, statsData, progData] = await Promise.all([
        getHabits(),
        getHabitStats(),
        getProgression().catch(() => null)
      ]);
      if (!isMountedRef.current) return;
      setHabits(habitsList);
      setStats(statsData);

      if (progData) {
        if (prevProgressionRef.current) {
          const oldLvl = prevProgressionRef.current.level;
          const newLvl = progData.level;
          const oldRnk = prevProgressionRef.current.rank;
          const newRnk = progData.rank;

          if (newLvl > oldLvl || (oldRnk && newRnk && oldRnk !== newRnk)) {
            setLevelUpEvent({
              oldLevel: oldLvl,
              newLevel: newLvl,
              oldRank: oldRnk,
              newRank: newRnk,
              isRankUp: oldRnk !== newRnk
            });
          }
        }
        prevProgressionRef.current = progData;
        setProgression(progData);
      }

      setError(null);
    } catch (err) {
      if (!isMountedRef.current) return;
      console.error('Failed to refresh habits data:', err);
      setError('Failed to refresh habits data.');
    }
  };

  useEffect(() => {
    isMountedRef.current = true;
    async function initHabits() {
      try {
        const [habitsList, statsData, progData] = await Promise.all([
          getHabits(),
          getHabitStats(),
          getProgression().catch(() => null)
        ]);
        if (isMountedRef.current) {
          setHabits(habitsList);
          setStats(statsData);
          if (progData) {
            prevProgressionRef.current = progData;
            setProgression(progData);
          }
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        if (isMountedRef.current) {
          console.error('Failed to load habits data:', err);
          setError('Failed to load habits. Please verify backend connection.');
          setLoading(false);
        }
      }
    }
    const currentTimers = animTimersRef.current;
    initHabits();

    const handleGlobalProgressUpdate = () => {
      refreshHabits();
    };
    window.addEventListener('mkc:progress-updated', handleGlobalProgressUpdate);

    return () => {
      isMountedRef.current = false;
      window.removeEventListener('mkc:progress-updated', handleGlobalProgressUpdate);
      currentTimers.forEach(t => clearTimeout(t));
      currentTimers.clear();
    };
  }, []);

  const triggerXpAnimation = (habitId, xpText = '+15 XP') => {
    animCounterRef.current += 1;
    const animId = animCounterRef.current;
    if (!isMountedRef.current) return;
    setFloatingXp(prev => [...prev, { id: animId, habitId, text: xpText }]);
    const timerId = setTimeout(() => {
      animTimersRef.current.delete(timerId);
      if (isMountedRef.current) {
        setFloatingXp(prev => prev.filter(item => item.id !== animId));
      }
    }, 1200);
    animTimersRef.current.add(timerId);
  };

  const handleToggleDate = async (habitId, dateStr) => {
    try {
      const res = await toggleHabit(habitId, dateStr);
      if (res && (res.completed || res.status === 'completed' || !res.removed)) {
        triggerXpAnimation(habitId, '+15 XP');
      }
      await refreshHabits();
      window.dispatchEvent(new CustomEvent('mkc:progress-updated'));
    } catch (err) {
      alert(err.message || 'Could not toggle habit completion.');
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title.trim()) return;

    try {
      await createHabit(formData);
      setShowModal(false);
      setFormData({
        title: '',
        description: '',
        category: 'wellness',
        frequency: 'daily',
        target_days_per_week: 7
      });
      await refreshHabits();
      window.dispatchEvent(new CustomEvent('mkc:progress-updated'));
    } catch (err) {
      alert(err.message || 'Failed to create habit.');
    }
  };

  const handleDeleteHabit = async (habitId, title) => {
    if (!window.confirm(`Are you sure you want to delete habit "${title}"?`)) return;

    try {
      await deleteHabit(habitId);
      await refreshHabits();
      window.dispatchEvent(new CustomEvent('mkc:progress-updated'));
    } catch (err) {
      alert(err.message || 'Failed to delete habit.');
    }
  };

  // Helper to format YYYY-MM-DD into short day label (e.g. "Mon")
  const formatDayLabel = (dateStr) => {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { weekday: 'short' });
  };

  return (
    <>
      <div className="habits-container">
          {/* 1. SOUL-LEVELING CHARACTER PROGRESSION HUD */}
          <div className="habits-hud-card glass-panel">
            <div className="hud-top-row">
              <div className="hud-identity">
                <div className="hud-level-badge font-display">
                  <span className="lvl-prefix">LVL</span>
                  <span className="lvl-number">{progression.level || 1}</span>
                </div>
                <div className="hud-title-col">
                  <div className="hud-rank-row">
                    <Crown size={15} style={{ color: 'var(--cyan)' }} />
                    <span className="hud-rank-title font-display">{progression.rank || 'Initiate'}</span>
                  </div>
                  <h1 className="hud-main-title font-serif">Discipline Protocols & Quests</h1>
                </div>
              </div>

              <div className="hud-actions-right">
                <button
                  onClick={() => setShowModal(true)}
                  className="create-habit-btn"
                >
                  <span>+ Add Protocol Quest</span>
                </button>
              </div>
            </div>

            {/* Soul-Leveling XP Progress Bar */}
            <div className="hud-xp-section">
              <div className="hud-xp-meta">
                <div className="xp-current-info font-display">
                  <Sparkles size={14} style={{ color: 'var(--cyan)' }} />
                  <span>XP {progression.current_level_xp !== undefined ? progression.current_level_xp : ((progression.total_xp || 0) % 500)} / {progression.next_level_xp || 500}</span>
                </div>
                <div className="xp-next-target font-display">
                  +{progression.xp_to_next_level !== undefined ? progression.xp_to_next_level : (progression.xp_to_next !== undefined ? progression.xp_to_next : Math.max(0, 500 - ((progression.total_xp || 0) % 500)))} XP TO LEVEL {(progression.level || 1) + 1}
                </div>
              </div>
              <div className="hud-xp-bar-track">
                <div 
                  className="hud-xp-bar-fill" 
                  style={{ width: `${Math.max(4, Math.min(100, progression.level_progress_percent !== undefined ? progression.level_progress_percent : (progression.progress_pct || 0)))}%` }}
                >
                  <div className="xp-bar-glow" />
                </div>
              </div>
            </div>
          </div>

          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 16px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '12px', color: '#EF4444', marginBottom: '24px' }}>
              <TriangleAlert size={16} strokeWidth={1.8} aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          {/* Habits Telemetry Overview */}
          <div className="habits-overview-grid">
            <div className="habit-stat-card glass-panel">
              <div className="habit-stat-header">
                <span className="habit-stat-title">Active Protocols</span>
                <span className="habit-stat-icon"><Shield size={18} strokeWidth={1.8} style={{ color: '#38BDF8' }} aria-hidden="true" /></span>
              </div>
              <div className="habit-stat-value">{stats.total_active_habits}</div>
              <div className="habit-stat-sub">{stats.habits_completed_today} completed today</div>
            </div>

            <div className="habit-stat-card glass-panel">
              <div className="habit-stat-header">
                <span className="habit-stat-title">Avg Current Streak</span>
                <span className="habit-stat-icon"><Zap size={18} strokeWidth={1.8} style={{ color: '#FBBF24' }} aria-hidden="true" /></span>
              </div>
              <div className="habit-stat-value">{stats.avg_current_streak} <span style={{ fontSize: '14px', color: 'var(--text-tertiary)' }}>Days</span></div>
              <div className="habit-stat-sub">Consecutive execution</div>
            </div>

            <div className="habit-stat-card glass-panel">
              <div className="habit-stat-header">
                <span className="habit-stat-title">Longest Record</span>
                <span className="habit-stat-icon"><Trophy size={18} strokeWidth={1.8} style={{ color: '#FBBF24' }} aria-hidden="true" /></span>
              </div>
              <div className="habit-stat-value">{stats.max_longest_streak} <span style={{ fontSize: '14px', color: 'var(--text-tertiary)' }}>Days</span></div>
              <div className="habit-stat-sub">All-time record</div>
            </div>

            <div className="habit-stat-card glass-panel">
              <div className="habit-stat-header">
                <span className="habit-stat-title">7-Day Consistency</span>
                <span className="habit-stat-icon"><TrendingUp size={18} strokeWidth={1.8} style={{ color: '#10B981' }} aria-hidden="true" /></span>
              </div>
              <div className="habit-stat-value">{stats.overall_7day_completion_pct}%</div>
              <div className="habit-stat-sub">Weekly protocol average</div>
            </div>
          </div>

          {/* Habits List */}
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-tertiary)' }}>
              Loading habits & streak telemetry...
            </div>
          ) : habits.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', background: 'var(--card-bg)', borderRadius: '20px', border: '1px solid var(--border-subtle)' }}>
              <h3 style={{ fontSize: '18px', color: 'var(--text-primary)', marginBottom: '8px' }}>No Habits Configured Yet</h3>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>Create your first habit protocol to start tracking your daily streak.</p>
              <button onClick={() => setShowModal(true)} className="create-habit-btn" style={{ margin: '0 auto' }}>
                + Create Your First Habit
              </button>
            </div>
          ) : (
            <div className="habits-list-section">
              {habits.map((habit) => (
                <div key={habit.id} className="habit-card glass-panel">
                  {/* Floating XP bubble animation */}
                  {floatingXp.filter(fx => fx.habitId === habit.id).map(fx => (
                    <div key={fx.id} className="floating-xp-bubble font-display">
                      <Sparkles size={13} /> {fx.text}
                    </div>
                  ))}

                  {/* Left Column: Info & Category */}
                  <div className="habit-info-col">
                    <div className="habit-meta-tags">
                      <span className={`category-tag ${habit.category}`}>
                        {habit.category}
                      </span>
                      <span className="quest-xp-reward font-display">
                        <Sparkles size={11} /> +15 XP
                      </span>
                      <span className="streak-badge" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <Zap size={12} strokeWidth={1.8} aria-hidden="true" /> {habit.current_streak} Day Streak (Best: {habit.longest_streak})
                      </span>
                    </div>
                    <h3 className="habit-title">{habit.title}</h3>
                    <p className="habit-description">{habit.description || 'No description provided.'}</p>
                  </div>

                  {/* Center Column: 7-Day Matrix */}
                  <div className="habit-matrix-col">
                    <span className="matrix-header-text">Past 7 Days Protocol Execution</span>
                    <div className="matrix-cells-row">
                      {habit.recent_7_days.map((dayItem) => (
                        <button
                          key={dayItem.date}
                          onClick={() => handleToggleDate(habit.id, dayItem.date)}
                          title={`${dayItem.date}: ${dayItem.completed ? 'Completed' : 'Click to complete protocol (+15 XP)'}`}
                          className={`matrix-cell ${dayItem.completed ? 'completed' : ''}`}
                        >
                          <span className="matrix-cell-day">{formatDayLabel(dayItem.date)}</span>
                          <span className="matrix-cell-dot" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            {dayItem.completed && <Check size={12} strokeWidth={2.5} aria-hidden="true" />}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Right Column: Actions */}
                  <div className="habit-actions-col">
                    <button
                      onClick={() => handleDeleteHabit(habit.id, habit.title)}
                      className="action-icon-btn"
                      title="Delete habit protocol"
                    >
                      <Trash2 size={16} strokeWidth={1.8} aria-hidden="true" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      {/* Level Up & Rank Up Celebration Modal */}
      {levelUpEvent && (
        <div className="level-up-modal-backdrop" onClick={() => setLevelUpEvent(null)}>
          <div className="level-up-modal-card glass-panel" onClick={e => e.stopPropagation()}>
            <div className="level-up-glow" />
            <div className="level-up-icon-wrap">
              <PartyPopper size={36} style={{ color: 'var(--cyan)' }} />
            </div>
            <span className="level-up-tag font-display">
              {levelUpEvent.isRankUp ? '★ RANK ADVANCEMENT ★' : '★ LEVEL UP ACHIEVED ★'}
            </span>
            <h2 className="level-up-title font-serif">
              {levelUpEvent.isRankUp
                ? `${levelUpEvent.oldRank} → ${levelUpEvent.newRank}`
                : `Level ${levelUpEvent.oldLevel} → Level ${levelUpEvent.newLevel}`}
            </h2>
            <div className="level-up-stats-box">
              <div className="level-up-stat">
                <span className="lvl-stat-lbl">ADVANCED RANK</span>
                <span className="lvl-stat-val font-display">{levelUpEvent.newRank}</span>
              </div>
              <div className="level-up-stat">
                <span className="lvl-stat-lbl">CURRENT LEVEL</span>
                <span className="lvl-stat-val font-display">LVL {levelUpEvent.newLevel}</span>
              </div>
              <div className="level-up-stat">
                <span className="lvl-stat-lbl">PROTOCOL REWARD</span>
                <span className="lvl-stat-val font-display" style={{ color: 'var(--cyan)' }}>+15 XP</span>
              </div>
            </div>
            <p className="level-up-sub">Your character progression accelerates through persistent protocol execution.</p>
            <button onClick={() => setLevelUpEvent(null)} className="btn-level-up-claim font-display">
              Claim Advancement →
            </button>
          </div>
        </div>
      )}

      {/* Create Habit Modal */}
      {showModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3>Create Habit Protocol</h3>
              <button onClick={() => setShowModal(false)} className="close-btn"><X size={16} /></button>
            </div>
            <form onSubmit={handleCreateSubmit}>
              <div className="form-group">
                <label>Habit Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., 60-Min AI Deep Work"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  rows="2"
                  placeholder="Describe your protocol routine..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="form-textarea"
                />
              </div>

              <div className="form-group">
                <label>Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="form-select"
                >
                  <option value="wellness">Wellness</option>
                  <option value="fitness">Fitness</option>
                  <option value="productivity">Productivity</option>
                  <option value="learning">Learning</option>
                  <option value="mindset">Mindset</option>
                  <option value="general">General</option>
                </select>
              </div>

              <div className="form-group">
                <label>Target Days / Week</label>
                <input
                  type="number"
                  min="1"
                  max="7"
                  value={formData.target_days_per_week}
                  onChange={(e) => setFormData({ ...formData, target_days_per_week: parseInt(e.target.value) || 7 })}
                  className="form-input"
                />
              </div>

              <div className="modal-actions">
                <button type="button" onClick={() => setShowModal(false)} className="btn-cancel">
                  Cancel
                </button>
                <button type="submit" className="btn-save">
                  Save Habit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default Habits;
