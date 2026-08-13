import { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import { Flame, Zap, Trophy, TrendingUp, TriangleAlert, Check, Trash2, X } from 'lucide-react';
import {
  getHabits,
  getHabitStats,
  createHabit,
  deleteHabit,
  toggleHabit
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);

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
      const [habitsList, statsData] = await Promise.all([
        getHabits(),
        getHabitStats()
      ]);
      setHabits(habitsList);
      setStats(statsData);
      setError(null);
    } catch (err) {
      console.error('Failed to refresh habits data:', err);
      setError('Failed to refresh habits data.');
    }
  };

  useEffect(() => {
    let isMounted = true;
    async function initHabits() {
      try {
        const [habitsList, statsData] = await Promise.all([
          getHabits(),
          getHabitStats()
        ]);
        if (isMounted) {
          setHabits(habitsList);
          setStats(statsData);
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to load habits data:', err);
          setError('Failed to load habits. Please verify backend connection.');
          setLoading(false);
        }
      }
    }
    initHabits();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleToggleDate = async (habitId, dateStr) => {
    try {
      await toggleHabit(habitId, dateStr);
      await refreshHabits();
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
    } catch (err) {
      alert(err.message || 'Failed to create habit.');
    }
  };

  const handleDeleteHabit = async (habitId, title) => {
    if (!window.confirm(`Are you sure you want to delete habit "${title}"?`)) return;

    try {
      await deleteHabit(habitId);
      await refreshHabits();
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
    <div className="app-shell">
      <Sidebar />
      <div className="main-viewport">
        <TopBar />
        <div className="habits-container">
          {/* Header */}
          <div className="habits-header-section">
            <div className="habits-header-left">
              <h1 className="font-serif">Habits & Streaks</h1>
              <p>Forge unbroken discipline through daily micro-consistency.</p>
            </div>
            <button
              onClick={() => setShowModal(true)}
              className="create-habit-btn"
            >
              <span>+ Create New Habit</span>
            </button>
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
                <span className="habit-stat-title">Active Habits</span>
                <span className="habit-stat-icon"><Flame size={18} strokeWidth={1.8} style={{ color: '#38BDF8' }} aria-hidden="true" /></span>
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
                  {/* Left Column: Info & Category */}
                  <div className="habit-info-col">
                    <div className="habit-meta-tags">
                      <span className={`category-tag ${habit.category}`}>
                        {habit.category}
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
                    <span className="matrix-header-text">Past 7 Days (Click to toggle)</span>
                    <div className="matrix-cells-row">
                      {habit.recent_7_days.map((dayItem) => (
                        <button
                          key={dayItem.date}
                          onClick={() => handleToggleDate(habit.id, dayItem.date)}
                          title={`${dayItem.date}: ${dayItem.completed ? 'Completed' : 'Pending'}`}
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
                      title="Delete habit"
                    >
                      <Trash2 size={16} strokeWidth={1.8} aria-hidden="true" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

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
    </div>
  );
};

export default Habits;
