import { useState, useEffect } from 'react';
import { Zap, Laptop, HeartPulse, Dumbbell, BookOpen, Brain, CheckCircle2, Target, Flame, TriangleAlert, X } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import MissionCard from '../components/MissionCard';
import { getMissions, toggleMission, createMission, getTelemetry } from '../services/api';
import './Missions.css';

const CATEGORY_FILTERS = [
  { id: 'all', label: 'All Protocols', icon: <Zap size={14} style={{ color: '#FBBF24' }} /> },
  { id: 'productivity', label: 'Productivity', icon: <Laptop size={14} style={{ color: '#38BDF8' }} /> },
  { id: 'wellness', label: 'Wellness', icon: <HeartPulse size={14} style={{ color: '#EC4899' }} /> },
  { id: 'fitness', label: 'Fitness', icon: <Dumbbell size={14} style={{ color: '#10B981' }} /> },
  { id: 'learning', label: 'Learning', icon: <BookOpen size={14} style={{ color: '#3B82F6' }} /> },
  { id: 'mindset', label: 'Mindset', icon: <Brain size={14} style={{ color: '#A78BFA' }} /> },
];

const Missions = () => {
  const [missions, setMissions] = useState([]);
  const [telemetry, setTelemetry] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('productivity');
  const [time, setTime] = useState('15 min');
  const [difficulty, setDifficulty] = useState('easy');
  const [xpReward, setXpReward] = useState(15);

  const loadMissionsData = async () => {
    try {
      const [missionsData, telemetryRes] = await Promise.all([
        getMissions().catch(() => []),
        getTelemetry().catch(() => null)
      ]);

      if (Array.isArray(missionsData)) {
        setMissions(missionsData);
      }
      if (telemetryRes) {
        setTelemetry(telemetryRes);
      }
      setError(null);
    } catch (err) {
      console.error('Failed to load missions:', err);
      setError('Could not connect to missions service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    async function init() {
      try {
        const [missionsData, telemetryRes] = await Promise.all([
          getMissions().catch(() => []),
          getTelemetry().catch(() => null)
        ]);

        if (isMounted) {
          if (Array.isArray(missionsData)) setMissions(missionsData);
          if (telemetryRes) setTelemetry(telemetryRes);
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to load missions:', err);
          setError('Could not connect to missions service.');
          setLoading(false);
        }
      }
    }
    init();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleToggleMission = async (id) => {
    // Optimistic toggle
    setMissions(prev => prev.map(m =>
      m.id === id ? { ...m, completed: !m.completed } : m
    ));

    try {
      await toggleMission(id);
      await loadMissionsData();
    } catch (err) {
      console.error('Failed to toggle mission:', err);
      // Revert if error
      setMissions(prev => prev.map(m =>
        m.id === id ? { ...m, completed: !m.completed } : m
      ));
    }
  };

  const handleCreateMission = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;

    try {
      await createMission({
        title,
        description,
        category,
        time,
        difficulty,
        xp_reward: Number(xpReward)
      });

      setShowModal(false);
      setTitle('');
      setDescription('');
      await loadMissionsData();
    } catch (err) {
      alert(err.message || 'Failed to create custom mission.');
    }
  };

  const filteredMissions = selectedCategory === 'all'
    ? missions
    : missions.filter(m => (m.category || 'general').toLowerCase() === selectedCategory);

  const completedCount = missions.filter(m => m.completed).length;
  const totalCount = missions.length;
  const completionPct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-viewport">
        <TopBar />
        <div className="missions-container">
          {/* Header */}
          <div className="missions-header-section">
            <div className="missions-header-left">
              <h1 className="font-serif">Daily Missions Protocol</h1>
              <p>Execute daily discipline actions to compound long-term mastery.</p>
            </div>
            <button
              onClick={() => setShowModal(true)}
              className="btn-create-mission-primary"
            >
              <span>+</span>
              <span>Create Protocol</span>
            </button>
          </div>

          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 16px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '12px', color: '#EF4444', marginBottom: '24px' }}>
              <TriangleAlert size={16} strokeWidth={1.8} aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          {/* Telemetry Overview Cards */}
          <div className="missions-overview-grid">
            <div className="missions-stat-card glass-panel">
              <div className="missions-stat-header">
                <span className="missions-stat-title">Protocols Completed</span>
                <CheckCircle2 size={18} strokeWidth={1.8} style={{ color: '#10B981' }} aria-hidden="true" />
              </div>
              <div className="missions-stat-value">{completedCount} <span style={{ fontSize: '14px', color: 'var(--text-tertiary)' }}>/ {totalCount}</span></div>
              <div className="missions-stat-sub">Daily execution target</div>
            </div>

            <div className="missions-stat-card glass-panel">
              <div className="missions-stat-header">
                <span className="missions-stat-title">Completion Rate</span>
                <Target size={18} strokeWidth={1.8} style={{ color: '#38BDF8' }} aria-hidden="true" />
              </div>
              <div className="missions-stat-value">{completionPct}%</div>
              <div className="missions-stat-sub">Discipline efficiency</div>
            </div>

            <div className="missions-stat-card glass-panel">
              <div className="missions-stat-header">
                <span className="missions-stat-title">Total XP Earned</span>
                <Zap size={18} strokeWidth={1.8} style={{ color: '#FBBF24' }} aria-hidden="true" />
              </div>
              <div className="missions-stat-value">{telemetry?.xp_earned ?? 0} <span style={{ fontSize: '14px', color: 'var(--text-tertiary)' }}>XP</span></div>
              <div className="missions-stat-sub">Level progression points</div>
            </div>

            <div className="missions-stat-card glass-panel">
              <div className="missions-stat-header">
                <span className="missions-stat-title">Discipline Streak</span>
                <Flame size={18} strokeWidth={1.8} style={{ color: '#F97316' }} aria-hidden="true" />
              </div>
              <div className="missions-stat-value">{telemetry?.streak_days ?? 0} <span style={{ fontSize: '14px', color: 'var(--text-tertiary)' }}>Days</span></div>
              <div className="missions-stat-sub">Consecutive active days</div>
            </div>
          </div>

          {/* Category Filter Bar */}
          <div className="missions-filter-bar">
            {CATEGORY_FILTERS.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`category-filter-btn ${selectedCategory === cat.id ? 'active' : ''}`}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
              >
                {cat.icon}
                <span>{cat.label}</span>
              </button>
            ))}
          </div>

          {/* Missions List */}
          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-tertiary)' }}>Loading Daily Mission Protocols...</div>
          ) : filteredMissions.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', background: 'var(--card-bg)', borderRadius: '16px', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)' }}>
              No mission protocols found in this category. Click "Create Protocol" above to add your custom action!
            </div>
          ) : (
            <div className="missions-feed-list">
              {filteredMissions.map((m) => (
                <MissionCard
                  key={m.id}
                  title={m.title}
                  category={m.category || 'general'}
                  time={m.time || '15 min'}
                  difficulty={m.difficulty || 'easy'}
                  completed={Boolean(m.completed)}
                  xpReward={m.xp_reward || m.xpReward || 10}
                  onComplete={() => handleToggleMission(m.id)}
                />
              ))}
            </div>
          )}

          {/* Modal: Create Mission */}
          {showModal && (
            <div className="modal-overlay">
              <div className="modal-content-card">
                <div className="modal-header">
                  <h3>Create Daily Mission Protocol</h3>
                  <button onClick={() => setShowModal(false)} className="modal-close-btn"><X size={16} /></button>
                </div>

                <form onSubmit={handleCreateMission} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div className="modal-form-group">
                    <label>Protocol Title</label>
                    <input
                      type="text"
                      placeholder="e.g. 30-Min System Design & Architecture Review"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      className="modal-input"
                      required
                    />
                  </div>

                  <div className="modal-form-group">
                    <label>Description / Verification Criteria</label>
                    <input
                      type="text"
                      placeholder="e.g. Read whitepaper on distributed consensus"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="modal-input"
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div className="modal-form-group">
                      <label>Category</label>
                      <select
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        className="modal-select"
                      >
                        <option value="productivity">Productivity</option>
                        <option value="wellness">Wellness</option>
                        <option value="fitness">Fitness</option>
                        <option value="learning">Learning</option>
                        <option value="mindset">Mindset</option>
                      </select>
                    </div>

                    <div className="modal-form-group">
                      <label>Estimated Time</label>
                      <input
                        type="text"
                        placeholder="e.g. 20 min"
                        value={time}
                        onChange={(e) => setTime(e.target.value)}
                        className="modal-input"
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div className="modal-form-group">
                      <label>Difficulty</label>
                      <select
                        value={difficulty}
                        onChange={(e) => setDifficulty(e.target.value)}
                        className="modal-select"
                      >
                        <option value="easy">Easy</option>
                        <option value="medium">Medium</option>
                        <option value="hard">Hard</option>
                      </select>
                    </div>

                    <div className="modal-form-group">
                      <label>XP Reward</label>
                      <input
                        type="number"
                        min="5"
                        max="100"
                        value={xpReward}
                        onChange={(e) => setXpReward(e.target.value)}
                        className="modal-input"
                      />
                    </div>
                  </div>

                  <div className="modal-actions">
                    <button type="button" onClick={() => setShowModal(false)} className="btn-modal-cancel">Cancel</button>
                    <button type="submit" className="btn-modal-submit">Create Protocol</button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Missions;
