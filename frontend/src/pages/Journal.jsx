import { useState, useEffect } from 'react';
import { Zap, Target, Scale, Shield, BatteryCharging, Calendar, Flame, BookOpen, Bot, RefreshCw, TriangleAlert, Trash2 } from 'lucide-react';
import {
  getTodayJournal,
  saveJournalEntry,
  getJournalHistory,
  getJournalStats,
  analyzeJournalEntry,
  deleteJournalEntry
} from '../services/api';
import './Journal.css';

const MOOD_OPTIONS = [
  { id: 'energized', label: 'Energized', icon: <Zap size={16} style={{ color: '#FBBF24' }} /> },
  { id: 'focused', label: 'Focused', icon: <Target size={16} style={{ color: '#38BDF8' }} /> },
  { id: 'neutral', label: 'Neutral', icon: <Scale size={16} style={{ color: '#A78BFA' }} /> },
  { id: 'challenged', label: 'Challenged', icon: <Shield size={16} style={{ color: '#F97316' }} /> },
  { id: 'exhausted', label: 'Exhausted', icon: <BatteryCharging size={16} style={{ color: '#EF4444' }} /> }
];

const Journal = () => {
  const [todayEntry, setTodayEntry] = useState(null);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState({
    total_entries: 0,
    journal_streak: 0,
    longest_journal_streak: 0,
    avg_energy_7d: 0.0,
    latest_mood: null,
    mood_distribution: {}
  });
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  // Form state
  const [mood, setMood] = useState('focused');
  const [energyLevel, setEnergyLevel] = useState(7);
  const [winsText, setWinsText] = useState('');
  const [challengesText, setChallengesText] = useState('');
  const [learningsText, setLearningsText] = useState('');
  const [growthNextText, setGrowthNextText] = useState('');

  // Helper for today's local YYYY-MM-DD
  const getTodayLocalDate = () => {
    const d = new Date();
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const refreshJournalData = async () => {
    try {
      const [todayRes, historyRes, statsRes] = await Promise.all([
        getTodayJournal(),
        getJournalHistory(30),
        getJournalStats()
      ]);

      if (todayRes && todayRes.entry) {
        const e = todayRes.entry;
        setTodayEntry(e);
        setMood(e.mood || 'focused');
        setEnergyLevel(e.energy_level || 7);
        setWinsText(e.wins_text || '');
        setChallengesText(e.challenges_text || '');
        setLearningsText(e.learnings_text || '');
        setGrowthNextText(e.growth_next_text || '');
      }

      if (historyRes && Array.isArray(historyRes.entries)) {
        setHistory(historyRes.entries);
      }

      if (statsRes) {
        setStats(statsRes);
      }

      setError(null);
    } catch (err) {
      console.error('Failed to refresh journal data:', err);
      setError('Could not connect to journal server.');
    }
  };

  useEffect(() => {
    let isMounted = true;
    async function initJournal() {
      try {
        const [todayRes, historyRes, statsRes] = await Promise.all([
          getTodayJournal(),
          getJournalHistory(30),
          getJournalStats()
        ]);

        if (isMounted) {
          if (todayRes && todayRes.entry) {
            const e = todayRes.entry;
            setTodayEntry(e);
            setMood(e.mood || 'focused');
            setEnergyLevel(e.energy_level || 7);
            setWinsText(e.wins_text || '');
            setChallengesText(e.challenges_text || '');
            setLearningsText(e.learnings_text || '');
            setGrowthNextText(e.growth_next_text || '');
          }

          if (historyRes && Array.isArray(historyRes.entries)) {
            setHistory(historyRes.entries);
          }

          if (statsRes) {
            setStats(statsRes);
          }

          setError(null);
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to load journal data:', err);
          setError('Could not connect to journal server.');
          setLoading(false);
        }
      }
    }
    initJournal();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSave = async (shouldAnalyze = false) => {
    setIsSubmitting(true);
    if (shouldAnalyze) setIsAnalyzing(true);
    setError(null);

    const payload = {
      entry_date: getTodayLocalDate(),
      mood,
      energy_level: energyLevel,
      wins_text: winsText,
      challenges_text: challengesText,
      learnings_text: learningsText,
      growth_next_text: growthNextText,
      analyze: shouldAnalyze
    };

    try {
      const res = await saveJournalEntry(payload);
      if (res && res.entry) {
        setTodayEntry(res.entry);
      }
      await refreshJournalData();
    } catch (err) {
      console.error('Failed to save reflection:', err);
      setError(err.message || 'Failed to save reflection entry.');
    } finally {
      setIsSubmitting(false);
      setIsAnalyzing(false);
    }
  };

  const handleReAnalyze = async () => {
    if (!todayEntry || !todayEntry.id) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const res = await analyzeJournalEntry(todayEntry.id);
      if (res && res.entry) {
        setTodayEntry(res.entry);
      }
      await refreshJournalData();
    } catch (err) {
      console.error('Failed to analyze entry:', err);
      setError(err.message || 'AI reflection analysis failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleDeleteEntry = async (id, dateStr) => {
    if (!window.confirm(`Delete reflection for ${dateStr}?`)) return;
    try {
      await deleteJournalEntry(id);
      if (todayEntry && todayEntry.id === id) {
        setTodayEntry(null);
        setWinsText('');
        setChallengesText('');
        setLearningsText('');
        setGrowthNextText('');
      }
      await refreshJournalData();
    } catch (err) {
      alert(err.message || 'Failed to delete entry.');
    }
  };

  return (
    <div className="journal-container">
          {/* Header */}
          <div className="journal-header-section">
            <div className="journal-header-left">
              <h1 className="font-serif">Mindset Journal</h1>
              <p>Reflect. Reframe. Return stronger.</p>
            </div>
            <div className="today-date-badge" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Calendar size={14} strokeWidth={1.8} aria-hidden="true" />
              <span>{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' })}</span>
            </div>
          </div>

          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 16px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '12px', color: '#EF4444', marginBottom: '24px' }}>
              <TriangleAlert size={16} strokeWidth={1.8} aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          {/* Journal Telemetry Overview */}
          <div className="journal-overview-grid">
            <div className="journal-stat-card glass-panel">
              <div className="journal-stat-header">
                <span className="journal-stat-title">Reflection Streak</span>
                <span className="journal-stat-icon"><Flame size={18} strokeWidth={1.8} style={{ color: '#38BDF8' }} aria-hidden="true" /></span>
              </div>
              <div className="journal-stat-value">{stats.journal_streak} <span style={{ fontSize: '14px', color: 'var(--text-tertiary)' }}>Days</span></div>
              <div className="journal-stat-sub">Best: {stats.longest_journal_streak} Days</div>
            </div>

            <div className="journal-stat-card glass-panel">
              <div className="journal-stat-header">
                <span className="journal-stat-title">7-Day Avg Energy</span>
                <span className="journal-stat-icon"><Zap size={18} strokeWidth={1.8} style={{ color: '#FBBF24' }} aria-hidden="true" /></span>
              </div>
              <div className="journal-stat-value">{stats.avg_energy_7d} <span style={{ fontSize: '14px', color: 'var(--text-tertiary)' }}>/10</span></div>
              <div className="journal-stat-sub">Weekly vital energy</div>
            </div>

            <div className="journal-stat-card glass-panel">
              <div className="journal-stat-header">
                <span className="journal-stat-title">Total Reflections</span>
                <span className="journal-stat-icon"><BookOpen size={18} strokeWidth={1.8} style={{ color: '#3B82F6' }} aria-hidden="true" /></span>
              </div>
              <div className="journal-stat-value">{stats.total_entries}</div>
              <div className="journal-stat-sub">Logged reflections</div>
            </div>

            <div className="journal-stat-card glass-panel">
              <div className="journal-stat-header">
                <span className="journal-stat-title">Latest Mood</span>
                <span className="journal-stat-icon"><Target size={18} strokeWidth={1.8} style={{ color: '#A78BFA' }} aria-hidden="true" /></span>
              </div>
              <div className="journal-stat-value">{stats.latest_mood || 'None'}</div>
              <div className="journal-stat-sub">Self-reported mood</div>
            </div>
          </div>

          {/* Main Two-Column Layout: Form & AI Card */}
          <div className="journal-main-grid">
            {/* Left: Reflection Form */}
            <div className="journal-form-card glass-panel">
              <h3 className="form-section-title">Today's Reflection Protocol</h3>

              {/* Mood Selector */}
              <div>
                <label className="prompt-label" style={{ display: 'block', marginBottom: '8px' }}>1. Select Your Current Mindset Mood</label>
                <div className="mood-selector-row">
                  {MOOD_OPTIONS.map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => setMood(m.id)}
                      className={`mood-pill-btn ${mood === m.id ? 'active' : ''}`}
                    >
                      <span>{m.icon}</span>
                      <span>{m.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Energy Level Slider */}
              <div className="energy-slider-container">
                <div className="energy-header">
                  <span className="prompt-label">2. Energy Level (1-10)</span>
                  <span className="energy-num-badge">{energyLevel} / 10</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={energyLevel}
                  onChange={(e) => setEnergyLevel(parseInt(e.target.value))}
                  className="energy-slider"
                />
              </div>

              {/* Prompts */}
              <div className="reflection-prompt-group">
                <label className="prompt-label">What went well today?</label>
                <textarea
                  rows="2"
                  placeholder="Record your wins, breakthroughs, or completed tasks..."
                  value={winsText}
                  onChange={(e) => setWinsText(e.target.value)}
                  className="prompt-textarea"
                />
              </div>

              <div className="reflection-prompt-group">
                <label className="prompt-label">What challenged me today?</label>
                <textarea
                  rows="2"
                  placeholder="Identify friction points, distractions, or difficulty..."
                  value={challengesText}
                  onChange={(e) => setChallengesText(e.target.value)}
                  className="prompt-textarea"
                />
              </div>

              <div className="reflection-prompt-group">
                <label className="prompt-label">What did I learn today?</label>
                <textarea
                  rows="2"
                  placeholder="Core mental model or key engineering realization..."
                  value={learningsText}
                  onChange={(e) => setLearningsText(e.target.value)}
                  className="prompt-textarea"
                />
              </div>

              <div className="reflection-prompt-group">
                <label className="prompt-label">What will I improve tomorrow?</label>
                <textarea
                  rows="2"
                  placeholder="Single high-leverage focus action for tomorrow..."
                  value={growthNextText}
                  onChange={(e) => setGrowthNextText(e.target.value)}
                  className="prompt-textarea"
                />
              </div>

              {/* Form Actions */}
              <div className="journal-form-actions">
                <button
                  type="button"
                  disabled={isSubmitting || isAnalyzing}
                  onClick={() => handleSave(false)}
                  className="btn-save-journal"
                >
                  {isSubmitting && !isAnalyzing ? 'Saving...' : 'Save Reflection'}
                </button>

                <button
                  type="button"
                  disabled={isSubmitting || isAnalyzing}
                  onClick={() => handleSave(true)}
                  className="btn-analyze-journal"
                >
                  {isAnalyzing ? 'Analyzing Reflection...' : 'Save & Analyze with AI'}
                </button>
              </div>
            </div>

            {/* Right: AI Reflection Analysis Card */}
            <div className="ai-analysis-card glass-panel">
              <div className="ai-card-header">
                <Bot size={20} strokeWidth={1.8} style={{ color: 'var(--cyan)' }} aria-hidden="true" />
                <h3>AI Mindset Coach Reflection</h3>
              </div>

              {isAnalyzing ? (
                <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--cyan)' }}>
                  <p style={{ fontWeight: '700', marginBottom: '8px' }}>Synthesizing Mindset Reflection...</p>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Evaluating goals, energy level, and daily protocol metrics.</p>
                </div>
              ) : todayEntry && todayEntry.ai_analysis ? (
                <div>
                  <div className="ai-analysis-body">
                    {todayEntry.ai_analysis}
                  </div>
                  <div style={{ marginTop: '20px', textAlign: 'right' }}>
                    <button
                      onClick={handleReAnalyze}
                      disabled={isAnalyzing}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'transparent', border: '1px solid var(--border-subtle)', borderRadius: '8px', color: 'var(--text-secondary)', padding: '6px 12px', cursor: 'pointer', fontSize: '11px' }}
                    >
                      <RefreshCw size={12} strokeWidth={1.8} aria-hidden="true" /> Re-Analyze Reflection
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '50px 20px', color: 'var(--text-tertiary)' }}>
                  <p style={{ fontSize: '14px', marginBottom: '8px' }}>No AI Analysis Generated Yet</p>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                    Complete your daily prompts and click <strong>"Save & Analyze with AI"</strong> to receive personalized coaching insights.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Bottom Section: Reflection History */}
          <div className="history-section">
            <div className="history-section-header">
              <h2>Reflection History</h2>
              <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>{history.length} logged entries</span>
            </div>

            {loading ? (
              <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-tertiary)' }}>Loading reflection logs...</div>
            ) : history.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', background: 'var(--card-bg)', borderRadius: '16px', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)' }}>
                No past reflections found. Fill out today's reflection form to start your mindset journal streak!
              </div>
            ) : (
              history.map((item) => (
                <div key={item.id} className="history-card-item glass-panel">
                  <div className="history-item-left">
                    <div className="history-item-meta">
                      <span className="history-item-date" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <Calendar size={12} strokeWidth={1.8} aria-hidden="true" /> {item.entry_date}
                      </span>
                      <span className="history-item-mood">{item.mood}</span>
                      <span className="history-item-energy" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <Zap size={12} strokeWidth={1.8} style={{ color: '#FBBF24' }} aria-hidden="true" /> Energy: {item.energy_level}/10
                      </span>
                      {item.ai_analysis && <span style={{ fontSize: '10px', padding: '2px 6px', background: 'rgba(56, 189, 248, 0.15)', color: 'var(--cyan)', borderRadius: '4px' }}>AI Analyzed</span>}
                    </div>

                    {item.wins_text && (
                      <p className="history-preview-text">
                        <strong>Win:</strong> {item.wins_text}
                      </p>
                    )}
                    {item.challenges_text && (
                      <p className="history-preview-text">
                        <strong>Challenge:</strong> {item.challenges_text}
                      </p>
                    )}
                  </div>

                  <button
                    onClick={() => handleDeleteEntry(item.id, item.entry_date)}
                    style={{ background: 'transparent', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', fontSize: '14px', padding: '4px' }}
                    title="Delete reflection"
                  >
                    <Trash2 size={14} strokeWidth={1.8} aria-hidden="true" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
  );
};

export default Journal;
