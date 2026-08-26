import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Flame, Brain, Zap, TrendingUp, CheckCircle2, DollarSign, Rocket, ArrowRight } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import HeroSection from '../components/HeroSection';
import StatCard from '../components/StatCard';
import ProgressCircle from '../components/ProgressCircle';
import AICoachCard from '../components/AICoachCard';
import MasteryPlanCard from '../components/MasteryPlanCard';
import MissionCard from '../components/MissionCard';
import MotivationBar from '../components/MotivationBar';
import { getMissions, toggleMission, getProgress, getTelemetry, getUser, getGoals, getDailyReflection, getProgression } from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
  const [missions, setMissions] = useState([]);
  const [progressData, setProgressData] = useState({ completed: 0, total: 0, percentage: 0 });
  const [progression, setProgression] = useState({ total_xp: 0, level: 1, rank: 'INITIATE', level_progress_percent: 0 });
  const [telemetry, setTelemetry] = useState({
    discipline_score: 0,
    mindset_strength: 0,
    consistency: 0,
    growth_index: 0,
    financial_goal: 0,
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
    }
  });
  const [user, setUser] = useState(null);
  const [goals, setGoals] = useState([]);
  const [reflectionData, setReflectionData] = useState({
    reflection: '"Small choices today create extraordinary tomorrows."',
    date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    highlight_metric: 'Daily Protocol',
    highlight_color: '#38BDF8'
  });
  const [loading, setLoading] = useState(true);
  const [backendConnected, setBackendConnected] = useState(false);

  const loadBackendData = useCallback(async () => {
    try {
      const [missionsData, telemetryRes, userRes, goalsRes, reflectionRes, progRes] = await Promise.all([
        getMissions().catch(() => null),
        getTelemetry().catch(() => null),
        getUser().catch(() => null),
        getGoals().catch(() => null),
        getDailyReflection().catch(() => null),
        getProgression().catch(() => null),
      ]);

      if (Array.isArray(missionsData) && missionsData.length > 0) {
        setMissions(missionsData);
      }

      if (telemetryRes) {
        setTelemetry(telemetryRes);
        if (telemetryRes.mission_completion) {
          setProgressData(telemetryRes.mission_completion);
        }
        if (telemetryRes.progression) {
          setProgression(telemetryRes.progression);
        }
      } else {
        const fallbackProg = await getProgress().catch(() => null);
        if (fallbackProg) setProgressData(fallbackProg);
      }

      if (progRes) setProgression(progRes);
      if (userRes) setUser(userRes);
      if (Array.isArray(goalsRes)) setGoals(goalsRes);
      if (reflectionRes) setReflectionData(reflectionRes);

      setBackendConnected(true);
    } catch (err) {
      console.warn('Backend API connection warning, operating with fallback local state:', err.message);
      setBackendConnected(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    async function init() {
      if (isMounted) {
        await loadBackendData();
      }
    }
    init();

    const handleGlobalProgressUpdate = () => {
      if (isMounted) {
        loadBackendData();
      }
    };
    window.addEventListener('mkc:progress-updated', handleGlobalProgressUpdate);

    return () => {
      isMounted = false;
      window.removeEventListener('mkc:progress-updated', handleGlobalProgressUpdate);
    };
  }, [loadBackendData]);

  const handleToggleMission = async (id) => {
    // Optimistic local UI toggle
    setMissions(prev => prev.map(m =>
      m.id === id ? { ...m, completed: !m.completed } : m
    ));

    if (backendConnected) {
      try {
        const updatedMission = await toggleMission(id);
        setMissions(prev => prev.map(m =>
          m.id === id ? { ...m, ...updatedMission } : m
        ));

        const [freshTelemetry, freshProgress, freshProgression] = await Promise.all([
          getTelemetry().catch(() => null),
          getProgress().catch(() => null),
          getProgression().catch(() => null),
        ]);

        if (freshTelemetry) setTelemetry(freshTelemetry);
        if (freshProgress) setProgressData(freshProgress);
        if (freshProgression) setProgression(freshProgression);

        // Dispatch global progress update event
        window.dispatchEvent(new CustomEvent('mkc:progress-updated'));
      } catch (err) {
        console.error('Error toggling mission on server:', err.message);
      }
    }
  };

  const completedCount = missions.filter(m => m.completed).length;
  const activeGoal = goals.find(g => g.status === 'active') || goals[0] || null;
  const activeGoalMissions = activeGoal ? missions.filter(m => Number(m.goal_id) === Number(activeGoal.id)) : missions;

  return (
    <div className="app-shell">
      {/* 1. Fixed Left Sidebar (~220px) */}
      <Sidebar />

      {/* 2. Main Scrollable Container */}
      <div className="main-viewport">
        {/* Sticky TopBar */}
        <TopBar user={user} />

        {/* Dashboard View Content */}
        <div className="dashboard-content-layout">
          {/* CENTER COLUMN (Flexible Width) */}
          <main className="center-content">
            {/* Cinematic Hero Section */}
            <HeroSection />

            {/* Performance Metrics Section (4-Column Grid) */}
            <section className="metrics-section" id="analytics">
              <div className="section-header">
                <h2 className="section-title font-display">Performance Metrics</h2>
                <span className="section-subtitle">Real-time telemetry</span>
              </div>

              <div className="metrics-grid-4col">
                {/* Row 1 */}
                <StatCard
                  title="Discipline Score"
                  value={String(telemetry.discipline_score || 0)}
                  unit="/100"
                  subtitle="Building daily discipline"
                  change={`${telemetry.discipline_score_change >= 0 ? '+' : ''}${telemetry.discipline_score_change || 0}`}
                  trend={telemetry.discipline_score_change >= 0 ? "up" : "down"}
                  icon={<Flame size={22} strokeWidth={1.8} />}
                  accentColor="#38BDF8"
                  sparklineData={telemetry.sparklines?.discipline_score || [0, 0, 0, 0, 0, 0, 0]}
                />
                <StatCard
                  title="Mindset Strength"
                  value={String(telemetry.mindset_strength || 0)}
                  unit="/100"
                  subtitle="Mental fortitude index"
                  change={`${telemetry.mindset_strength_change >= 0 ? '+' : ''}${telemetry.mindset_strength_change || 0}`}
                  trend={telemetry.mindset_strength_change >= 0 ? "up" : "down"}
                  icon={<Brain size={22} strokeWidth={1.8} />}
                  accentColor="#3B82F6"
                  sparklineData={telemetry.sparklines?.mindset_strength || [0, 0, 0, 0, 0, 0, 0]}
                />
                <StatCard
                  title="Consistency"
                  value={String(telemetry.consistency || 0)}
                  unit="/100"
                  subtitle="Closer to Freedom"
                  change={`${telemetry.consistency_change >= 0 ? '+' : ''}${telemetry.consistency_change || 0}`}
                  trend={telemetry.consistency_change >= 0 ? "up" : "down"}
                  icon={<Zap size={22} strokeWidth={1.8} />}
                  accentColor="#FBBF24"
                  sparklineData={telemetry.sparklines?.consistency || [0, 0, 0, 0, 0, 0, 0]}
                />
                <StatCard
                  title="Growth Index"
                  value={String(telemetry.growth_index || 0)}
                  unit="/100"
                  subtitle="Compound expansion"
                  change={`${telemetry.growth_index_change >= 0 ? '+' : ''}${telemetry.growth_index_change || 0}`}
                  trend={telemetry.growth_index_change >= 0 ? "up" : "down"}
                  icon={<TrendingUp size={22} strokeWidth={1.8} />}
                  accentColor="#10B981"
                  sparklineData={telemetry.sparklines?.growth_index || [0, 0, 0, 0, 0, 0, 0]}
                />

                {/* Row 2 */}
                <StatCard
                  title="Missions Completed"
                  value={String(telemetry.mission_completion?.completed !== undefined ? telemetry.mission_completion.completed : completedCount)}
                  subtitle="Discipline actions"
                  change={`${telemetry.missions_completed_change >= 0 ? '+' : ''}${telemetry.missions_completed_change || 0}`}
                  trend={telemetry.missions_completed_change >= 0 ? "up" : "down"}
                  icon={<CheckCircle2 size={22} strokeWidth={1.8} />}
                  accentColor="#38BDF8"
                  sparklineData={telemetry.sparklines?.missions_completed || [0, 0, 0, 0, 0, 0, 0]}
                />
                <StatCard
                  title="Financial Goal"
                  value={String(telemetry.financial_goal || 0) + "%"}
                  subtitle="Closer to Freedom"
                  change={`${telemetry.financial_goal_change >= 0 ? '+' : ''}${telemetry.financial_goal_change || 0}%`}
                  trend={telemetry.financial_goal_change >= 0 ? "up" : "down"}
                  icon={<DollarSign size={22} strokeWidth={1.8} />}
                  accentColor="#FBBF24"
                  sparklineData={telemetry.sparklines?.financial_goal || [0, 0, 0, 0, 0, 0, 0]}
                />
                <StatCard
                  title="Discipline Streak"
                  value={String(telemetry.streak_days || 0)}
                  unit="Days"
                  subtitle="Consistency compounding"
                  change={`${telemetry.streak_days_change >= 0 ? '+' : ''}${telemetry.streak_days_change || 0}`}
                  trend={telemetry.streak_days_change >= 0 ? "up" : "down"}
                  icon={<Zap size={22} strokeWidth={1.8} />}
                  accentColor="#FBBF24"
                  sparklineData={telemetry.sparklines?.streak_days || [0, 0, 0, 0, 0, 0, 0]}
                />
                <StatCard
                  title="Future You"
                  value={`Level ${progression.level || Math.floor((telemetry.xp_earned || 0) / 500) + 1}`}
                  subtitle={`${progression.total_xp ?? telemetry.xp_earned ?? 0} Total XP • ${progression.rank || 'INITIATE'}`}
                  change={`${telemetry.xp_earned_change >= 0 ? '+' : ''}${telemetry.xp_earned_change || 0} XP`}
                  trend={telemetry.xp_earned_change >= 0 ? "up" : "down"}
                  icon={<Rocket size={22} strokeWidth={1.8} />}
                  accentColor="#A78BFA"
                  sparklineData={telemetry.sparklines?.xp_earned || [0, 0, 0, 0, 0, 0, 0]}
                />
              </div>
            </section>

            {/* Daily Missions Section */}
            <section className="missions-section">
              <div className="section-header">
                <h2 className="section-title font-display">Daily Missions</h2>
                <span className="section-subtitle">
                  {completedCount}/{missions.length} Protocol Completed {loading && '(Syncing...)'}
                </span>
              </div>

              <div className="missions-list">
                {missions.map(mission => (
                  <MissionCard
                    key={mission.id}
                    title={mission.title}
                    category={mission.category || 'wellness'}
                    time={mission.time || '15 min'}
                    difficulty={mission.difficulty || 'easy'}
                    completed={Boolean(mission.completed)}
                    xpReward={mission.xp_reward || mission.xpReward || 10}
                    onComplete={() => handleToggleMission(mission.id)}
                  />
                ))}
              </div>
            </section>

            {/* Bottom Motivation Bar (Quote Cards) */}
            <MotivationBar />
          </main>

          {/* 3. RIGHT INFORMATION PANEL (~320px Fixed Width) */}
          <aside className="right-panel">
            {/* 1. Today's Progress */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
              <ProgressCircle
                percentage={progressData.percentage || (missions.length > 0 ? Math.round((completedCount / missions.length) * 100) : 0)}
                label={progressData.percentage > 0 || completedCount > 0 ? "On Track" : "Starting"}
                disciplineScore={telemetry.discipline_score || 0}
                mindsetScore={telemetry.mindset_strength || 0}
                executionScore={missions.length > 0 ? Math.round((completedCount / missions.length) * 100) : 0}
                consistencyScore={telemetry.consistency || 0}
              />
              
              {/* Dynamic Mission CTA */}
              {(() => {
                const pendingMission = missions.find(m => !m.completed);
                if (pendingMission) {
                  return (
                    <Link 
                      to="/missions"
                      style={{ width: '100%', background: 'var(--cyan)', color: '#000', border: 'none', borderRadius: '8px', padding: '14px', fontWeight: '700', fontSize: '14px', cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', textDecoration: 'none', transition: 'all 0.2s' }}
                      onMouseOver={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 4px 12px rgba(56,189,248,0.3)'; }}
                      onMouseOut={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = 'none'; }}
                    >
                      Begin Today's Mission <ArrowRight size={16} strokeWidth={2.5} />
                    </Link>
                  );
                } else if (missions.length > 0) {
                  return (
                    <Link to="/dashboard" style={{ width: '100%', background: 'rgba(56, 189, 248, 0.1)', border: '1px solid var(--cyan)', color: 'var(--cyan)', borderRadius: '8px', padding: '14px', fontWeight: '700', fontSize: '14px', cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', textDecoration: 'none', transition: 'all 0.2s' }}
                      onMouseOver={(e) => { e.currentTarget.style.background = 'rgba(56, 189, 248, 0.2)'; }}
                      onMouseOut={(e) => { e.currentTarget.style.background = 'rgba(56, 189, 248, 0.1)'; }}
                    >
                      Review Today's Progress <ArrowRight size={16} strokeWidth={2.5} />
                    </Link>
                  );
                } else {
                  return (
                    <Link to="/missions" style={{ width: '100%', background: 'var(--cyan)', color: '#000', border: 'none', borderRadius: '8px', padding: '14px', fontWeight: '700', fontSize: '14px', cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', textDecoration: 'none', transition: 'all 0.2s' }}
                      onMouseOver={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 4px 12px rgba(56,189,248,0.3)'; }}
                      onMouseOut={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = 'none'; }}
                    >
                      Create Today's Mission <ArrowRight size={16} strokeWidth={2.5} />
                    </Link>
                  );
                }
              })()}
            </div>

            {/* 2. AI Coach Card */}
            <AICoachCard
              message="You're not just dreaming— you're building. Every step today creates a stronger tomorrow."
              coachName="AI Coach"
              isOnline={true}
            />

            {/* 3. Mastery Plan */}
            <MasteryPlanCard activeGoal={activeGoal} linkedMissions={activeGoalMissions} telemetryBlueprint={telemetry.blueprint} />

            {/* 4. Today's Reflection */}
            <div className="reflection-card glass-panel">
              <div className="reflection-header">
                <span className="reflection-tag" style={{ color: reflectionData.highlight_color || 'var(--cyan)' }}>
                  DAILY REFLECTION • {reflectionData.highlight_metric || 'DISCIPLINE'}
                </span>
                <span className="reflection-date font-display">{reflectionData.date}</span>
              </div>
              <h3 className="reflection-title font-serif">
                "{reflectionData.reflection.replace(/^"|"$/g, '')}"
              </h3>
              <Link to="/journal" className="reflection-cta-btn" style={{ textDecoration: 'none' }}>
                <span>Write Reflection</span>
                <ArrowRight size={16} strokeWidth={1.8} style={{ marginLeft: '6px' }} />
              </Link>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
