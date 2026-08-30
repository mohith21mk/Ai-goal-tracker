import { useState, useEffect, useCallback } from 'react';
import {
  Flame,
  Brain,
  Zap,
  TrendingUp,
  CheckCircle2,
  DollarSign,
  Rocket,
  Sparkles,
  Award,
  Calendar,
  Activity
} from 'lucide-react';
import StatCard from '../components/StatCard';
import MKCLogo from '../components/MKCLogo';
import { getTelemetry, getDailyProgress, getProgress, getProgression } from '../services/api';
import './Analytics.css';

const getStatusLabel = (score) => {
  if (score === undefined || score === null || score === 0) return 'Starting';
  if (score >= 80) return 'Optimal';
  if (score >= 60) return 'Strong';
  if (score >= 40) return 'Focused';
  if (score >= 20) return 'Building';
  return 'Starting';
};

const Analytics = () => {
  const [telemetry, setTelemetry] = useState({
    discipline_score: 0,
    mindset_strength: 0,
    consistency: 0,
    growth_index: 0,
    financial_goal: 0,
    active_days: 0,
    current_streak: 0,
    longest_streak: 0,
    streak_days: 0,
    xp_earned: 0,
    discipline_score_change: 0,
    mindset_strength_change: 0,
    consistency_change: 0,
    growth_index_change: 0,
    financial_goal_change: 0,
    sparklines: {
      discipline_score: [0, 0, 0, 0, 0, 0, 0],
      mindset_strength: [0, 0, 0, 0, 0, 0, 0],
      consistency: [0, 0, 0, 0, 0, 0, 0],
      growth_index: [0, 0, 0, 0, 0, 0, 0],
      financial_goal: [0, 0, 0, 0, 0, 0, 0],
      missions_completed: [0, 0, 0, 0, 0, 0, 0],
      streak_days: [0, 0, 0, 0, 0, 0, 0],
      xp_earned: [0, 0, 0, 0, 0, 0, 0],
    }
  });
  const [progression, setProgression] = useState({ total_xp: 0, level: 1, rank: 'INITIATE', level_progress_percent: 0 });
  const [dailyProgress, setDailyProgress] = useState({
    completed_actions: 0,
    total_actions: 0,
    completion_percentage: 0,
    missions_completed: 0,
    total_missions: 0,
    habits_completed: 0,
    total_habits: 0,
    xp_earned_today: 0,
  });
  const [loading, setLoading] = useState(true);

  const loadAnalyticsData = useCallback(async () => {
    try {
      const [telemetryRes, dailyRes, progRes] = await Promise.all([
        getTelemetry().catch(() => null),
        getDailyProgress().catch(() => null),
        getProgression().catch(() => null),
      ]);

      if (telemetryRes) {
        setTelemetry(telemetryRes);
        if (telemetryRes.progression) setProgression(telemetryRes.progression);
      }
      if (dailyRes) {
        setDailyProgress(dailyRes);
      } else {
        const fallbackProg = await getProgress().catch(() => null);
        if (fallbackProg?.daily) {
          setDailyProgress(fallbackProg.daily);
        } else if (fallbackProg) {
          setDailyProgress({
            completed_actions: fallbackProg.completed || 0,
            total_actions: fallbackProg.total || 0,
            completion_percentage: fallbackProg.percentage || 0,
            missions_completed: fallbackProg.completed || 0,
            total_missions: fallbackProg.total || 0,
            habits_completed: 0,
            total_habits: 0,
            xp_earned_today: 0,
          });
        }
      }
      if (progRes) setProgression(progRes);
    } catch (err) {
      console.warn('Failed to load real analytics telemetry:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    async function init() {
      if (isMounted) {
        await loadAnalyticsData();
      }
    }
    init();

    const handleGlobalProgressUpdate = () => {
      if (isMounted) {
        loadAnalyticsData();
      }
    };
    window.addEventListener('mkc:progress-updated', handleGlobalProgressUpdate);

    return () => {
      isMounted = false;
      window.removeEventListener('mkc:progress-updated', handleGlobalProgressUpdate);
    };
  }, [loadAnalyticsData]);

  const userLevel = progression.level || Math.floor((telemetry.xp_earned || 0) / 500) + 1;
  const hasActivity = (telemetry.discipline_score > 0) || ((progression.total_xp || telemetry.xp_earned || 0) > 0) || (dailyProgress.completed_actions > 0) || (telemetry.active_days > 0);

  return (
    <div className="analytics-page-layout">
      {/* Header Banner */}
      <div className="analytics-header glass-panel">
        <div className="analytics-header-content">
          <div className="analytics-title-group">
            <div className="analytics-icon-badge">
              <MKCLogo size={36} />
            </div>
            <div>
              <h1 className="analytics-title font-display">Performance Analytics</h1>
              <p className="analytics-subtitle">
                Normalized overall performance telemetry and daily protocol tracking derived strictly from your database records.
              </p>
            </div>
          </div>
          <div className="analytics-status-pill">
            <Activity size={16} strokeWidth={1.8} />
            <span>{hasActivity ? 'Live Telemetry Active' : 'Zero State • Ready to Begin'}</span>
          </div>
        </div>
      </div>

      {/* Core 4 Performance Pillars (System 1: Overall Performance) */}
      <section className="analytics-section">
        <div className="section-header">
          <h2 className="section-title font-display">Core Pillars</h2>
          <span className="section-subtitle">{loading ? 'Syncing...' : 'Normalized Journey Telemetry'}</span>
        </div>

        <div className="metrics-grid-4col">
          <StatCard
            title="Discipline Score"
            value={String(telemetry.discipline_score || 0)}
            unit="/100"
            subtitle={getStatusLabel(telemetry.discipline_score)}
            change={`${telemetry.discipline_score_change >= 0 ? '+' : ''}${telemetry.discipline_score_change || 0}`}
            trend={telemetry.discipline_score_change >= 0 ? 'up' : 'down'}
            icon={<Flame size={20} strokeWidth={1.8} />}
            accentColor="#10B981"
            sparklineData={telemetry.sparklines?.discipline_score || [0, 0, 0, 0, 0, 0, 0]}
          />
          <StatCard
            title="Mindset Strength"
            value={String(telemetry.mindset_strength || 0)}
            unit="/100"
            subtitle={getStatusLabel(telemetry.mindset_strength)}
            change={`${telemetry.mindset_strength_change >= 0 ? '+' : ''}${telemetry.mindset_strength_change || 0}`}
            trend={telemetry.mindset_strength_change >= 0 ? 'up' : 'down'}
            icon={<Brain size={20} strokeWidth={1.8} />}
            accentColor="#A78BFA"
            sparklineData={telemetry.sparklines?.mindset_strength || [0, 0, 0, 0, 0, 0, 0]}
          />
          <StatCard
            title="Execution Rate"
            value={`${telemetry.mission_completion?.percentage || 0}%`}
            subtitle={`${telemetry.mission_completion?.completed || 0} / ${telemetry.mission_completion?.total || 0} Lifetime Missions`}
            change={`${telemetry.missions_completed_change >= 0 ? '+' : ''}${telemetry.missions_completed_change || 0}`}
            trend={telemetry.missions_completed_change >= 0 ? 'up' : 'down'}
            icon={<CheckCircle2 size={20} strokeWidth={1.8} />}
            accentColor="#38BDF8"
            sparklineData={telemetry.sparklines?.missions_completed || [0, 0, 0, 0, 0, 0, 0]}
          />
          <StatCard
            title="Consistency"
            value={String(telemetry.consistency || 0)}
            unit="/100"
            subtitle={`${telemetry.active_days || 0} active days logged`}
            change={`${telemetry.consistency_change >= 0 ? '+' : ''}${telemetry.consistency_change || 0}`}
            trend={telemetry.consistency_change >= 0 ? 'up' : 'down'}
            icon={<Zap size={20} strokeWidth={1.8} />}
            accentColor="#3B82F6"
            sparklineData={telemetry.sparklines?.consistency || [0, 0, 0, 0, 0, 0, 0]}
          />
        </div>
      </section>

      {/* Growth & Compounding Section */}
      <section className="analytics-section">
        <div className="section-header">
          <h2 className="section-title font-display">Growth & Trajectory</h2>
          <span className="section-subtitle">Compounding XP & Financial Alignment</span>
        </div>

        <div className="metrics-grid-4col">
          <StatCard
            title="Growth Index"
            value={String(telemetry.growth_index || 0)}
            unit="/100"
            subtitle={getStatusLabel(telemetry.growth_index)}
            change={`${telemetry.growth_index_change >= 0 ? '+' : ''}${telemetry.growth_index_change || 0}`}
            trend={telemetry.growth_index_change >= 0 ? 'up' : 'down'}
            icon={<TrendingUp size={20} strokeWidth={1.8} />}
            accentColor="#F97316"
            sparklineData={telemetry.sparklines?.growth_index || [0, 0, 0, 0, 0, 0, 0]}
          />
          <StatCard
            title="Financial Goal"
            value={`${telemetry.financial_goal || 0}%`}
            subtitle="Financial Freedom Protocol"
            change={`${telemetry.financial_goal_change >= 0 ? '+' : ''}${telemetry.financial_goal_change || 0}%`}
            trend={telemetry.financial_goal_change >= 0 ? 'up' : 'down'}
            icon={<DollarSign size={20} strokeWidth={1.8} />}
            accentColor="#FBBF24"
            sparklineData={telemetry.sparklines?.financial_goal || [0, 0, 0, 0, 0, 0, 0]}
          />
          <StatCard
            title="Current Streak"
            value={String(telemetry.current_streak ?? telemetry.streak_days ?? 0)}
            unit="Days"
            subtitle={`Longest Streak: ${telemetry.longest_streak || telemetry.streak_days || 0}d`}
            change={`${telemetry.streak_days_change >= 0 ? '+' : ''}${telemetry.streak_days_change || 0}`}
            trend={telemetry.streak_days_change >= 0 ? 'up' : 'down'}
            icon={<Flame size={20} strokeWidth={1.8} />}
            accentColor="#F97316"
            sparklineData={telemetry.sparklines?.streak_days || [0, 0, 0, 0, 0, 0, 0]}
          />
          <StatCard
            title="Identity Level"
            value={`Level ${userLevel}`}
            subtitle={`${progression.total_xp ?? telemetry.xp_earned ?? 0} Total XP • ${progression.rank || 'INITIATE'}`}
            change={`${telemetry.xp_earned_change >= 0 ? '+' : ''}${telemetry.xp_earned_change || 0} XP`}
            trend={telemetry.xp_earned_change >= 0 ? 'up' : 'down'}
            icon={<Rocket size={20} strokeWidth={1.8} />}
            accentColor="#EC4899"
            sparklineData={telemetry.sparklines?.xp_earned || [0, 0, 0, 0, 0, 0, 0]}
          />
        </div>
      </section>

      {/* Breakdown Panels (2 Column) */}
      <div className="analytics-breakdown-grid">
        {/* System 2: Daily Protocol Summary */}
        <div className="analytics-card glass-panel">
          <div className="analytics-card-header">
            <Sparkles size={20} strokeWidth={1.8} className="icon-cyan" />
            <h3>Daily Protocol Summary</h3>
          </div>
          <div className="analytics-card-body">
            <div className="summary-row">
              <span className="summary-label">Actions Completed Today</span>
              <span className="summary-val font-display">{dailyProgress.completed_actions || 0} / {dailyProgress.total_actions || 0}</span>
            </div>
            <div className="summary-progress-bar">
              <div className="summary-progress-fill" style={{ width: `${Math.min(100, dailyProgress.completion_percentage || 0)}%` }} />
            </div>
            <div className="summary-row" style={{ marginTop: '12px' }}>
              <span className="summary-label">Missions Completed Today</span>
              <span className="summary-val font-display">{dailyProgress.missions_completed || 0}</span>
            </div>
            <div className="summary-row">
              <span className="summary-label">Habits Completed Today</span>
              <span className="summary-val font-display">{dailyProgress.habits_completed || 0}</span>
            </div>
            <div className="summary-row">
              <span className="summary-label">XP Earned Today</span>
              <span className="summary-val font-display" style={{ color: '#FBBF24' }}>
                +{dailyProgress.xp_earned_today || 0} XP
              </span>
            </div>
            <div className="summary-row">
              <span className="summary-label">Today's Protocol Status</span>
              <span className="summary-val font-display" style={{ color: 'var(--cyan)' }}>
                {dailyProgress.completion_percentage > 0 ? `${dailyProgress.completion_percentage}% Complete` : 'No activity recorded today'}
              </span>
            </div>
          </div>
        </div>

        {/* Lifetime Telemetry Milestones */}
        <div className="analytics-card glass-panel">
          <div className="analytics-card-header">
            <Award size={20} strokeWidth={1.8} className="icon-gold" />
            <h3>Journey Milestones</h3>
          </div>
          <div className="analytics-card-body">
            <div className="milestone-item">
              <div className="milestone-icon"><Calendar size={16} /></div>
              <div className="milestone-text">
                <div className="milestone-title">Streak Record</div>
                <div className="milestone-desc">
                  {(telemetry.longest_streak || telemetry.streak_days || 0) > 0
                    ? `${telemetry.longest_streak || telemetry.streak_days} consecutive days record (${telemetry.current_streak || telemetry.streak_days || 0}d active now)`
                    : 'No streak recorded yet'}
                </div>
              </div>
            </div>
            <div className="milestone-item">
              <div className="milestone-icon"><Award size={16} /></div>
              <div className="milestone-text">
                <div className="milestone-title">Total Lifetime XP</div>
                <div className="milestone-desc">
                  {(progression.total_xp || telemetry.xp_earned || 0) > 0
                    ? `${progression.total_xp || telemetry.xp_earned} XP accumulated across journey`
                    : '0 XP accumulated'}
                </div>
              </div>
            </div>
            <div className="milestone-item">
              <div className="milestone-icon"><Activity size={16} /></div>
              <div className="milestone-text">
                <div className="milestone-title">Active Days</div>
                <div className="milestone-desc">
                  {telemetry.active_days > 0
                    ? `${telemetry.active_days} distinct active days logged`
                    : 'Ready to log your first active day'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
