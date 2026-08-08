import { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import HeroSection from '../components/HeroSection';
import StatCard from '../components/StatCard';
import ProgressCircle from '../components/ProgressCircle';
import AICoachCard from '../components/AICoachCard';
import MasteryPlanCard from '../components/MasteryPlanCard';
import MissionCard from '../components/MissionCard';
import MotivationBar from '../components/MotivationBar';
import { getMissions, toggleMission, getProgress } from '../services/api';
import './Dashboard.css';

const defaultFallbackMissions = [
  { id: 1, title: 'Morning Meditation Protocol', category: 'wellness', time: '10 min', difficulty: 'easy', completed: false, xpReward: 10 },
  { id: 2, title: 'Deep Work Block & Code Architecture', category: 'productivity', time: '2 hrs', difficulty: 'hard', completed: true, xpReward: 25 },
  { id: 3, title: 'High-Intensity Workout Session', category: 'fitness', time: '45 min', difficulty: 'hard', completed: false, xpReward: 20 },
  { id: 4, title: 'Mastery Reading & Knowledge Note', category: 'learning', time: '20 min', difficulty: 'easy', completed: true, xpReward: 10 },
  { id: 5, title: 'Gratitude & Vision Reflection', category: 'mindset', time: '5 min', difficulty: 'easy', completed: false, xpReward: 10 },
];

const Dashboard = () => {
  const [missions, setMissions] = useState(defaultFallbackMissions);
  const [progressData, setProgressData] = useState({ completed: 2, total: 5, percentage: 40 });
  const [loading, setLoading] = useState(true);
  const [backendConnected, setBackendConnected] = useState(false);

  useEffect(() => {
    async function loadBackendData() {
      try {
        const [missionsData, telemetry] = await Promise.all([
          getMissions(),
          getProgress()
        ]);
        if (Array.isArray(missionsData) && missionsData.length > 0) {
          setMissions(missionsData);
        }
        if (telemetry && typeof telemetry.percentage === 'number') {
          setProgressData(telemetry);
        }
        setBackendConnected(true);
      } catch (err) {
        console.warn('Backend API connection failed, operating with fallback local state:', err.message);
        setBackendConnected(false);
      } finally {
        setLoading(false);
      }
    }

    loadBackendData();
  }, []);

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
        const updatedTelemetry = await getProgress();
        setProgressData(updatedTelemetry);
      } catch (err) {
        console.error('Error toggling mission on server:', err.message);
      }
    }
  };

  const completedCount = missions.filter(m => m.completed).length;

  return (
    <div className="app-shell">
      {/* 1. Fixed Left Sidebar (~220px) */}
      <Sidebar />

      {/* 2. Main Scrollable Container */}
      <div className="main-viewport">
        {/* Sticky TopBar */}
        <TopBar />

        {/* Dashboard View Content */}
        <div className="dashboard-content-layout">
          {/* CENTER COLUMN (Flexible Width) */}
          <main className="center-content">
            {/* Cinematic Hero Section */}
            <HeroSection />

            {/* Performance Metrics Section (4-Column Grid) */}
            <section className="metrics-section">
              <div className="section-header">
                <h2 className="section-title font-display">Performance Metrics</h2>
                <span className="section-subtitle">Real-time telemetry</span>
              </div>

              <div className="metrics-grid-4col">
                {/* Row 1 */}
                <StatCard
                  title="Discipline Score"
                  value="92"
                  unit="/100"
                  subtitle="Building daily discipline"
                  change="+6"
                  trend="up"
                  icon="🔥"
                  accentColor="#38BDF8"
                  sparklineData={[45, 55, 60, 72, 80, 85, 92]}
                />
                <StatCard
                  title="Mindset Strength"
                  value="88"
                  unit="/100"
                  subtitle="Mental fortitude index"
                  change="+8"
                  trend="up"
                  icon="🧠"
                  accentColor="#3B82F6"
                  sparklineData={[30, 42, 50, 68, 75, 80, 88]}
                />
                <StatCard
                  title="Consistency"
                  value="76"
                  unit="/100"
                  subtitle="Closer to Freedom"
                  change="+5"
                  trend="up"
                  icon="⚡"
                  accentColor="#FBBF24"
                  sparklineData={[50, 52, 58, 62, 70, 72, 76]}
                />
                <StatCard
                  title="Growth Index"
                  value="74"
                  unit="/100"
                  subtitle="Compound expansion"
                  change="+7"
                  trend="up"
                  icon="📈"
                  accentColor="#10B981"
                  sparklineData={[40, 48, 55, 60, 65, 70, 74]}
                />

                {/* Row 2 */}
                <StatCard
                  title="Missions Completed"
                  value={String(completedCount)}
                  subtitle="Discipline actions"
                  change="+3"
                  trend="up"
                  icon="✅"
                  accentColor="#38BDF8"
                  sparklineData={[10, 15, 22, 28, 35, 39, completedCount * 8 || 10]}
                />
                <StatCard
                  title="Financial Goal"
                  value="68%"
                  subtitle="Closer to Freedom"
                  change="+2%"
                  trend="up"
                  icon="💰"
                  accentColor="#FBBF24"
                  sparklineData={[50, 54, 58, 60, 62, 65, 68]}
                />
                <StatCard
                  title="Discipline Streak"
                  value="28"
                  unit="Days"
                  subtitle="Consistency compounding"
                  change="🔥 Active"
                  trend="up"
                  icon="⚡"
                  accentColor="#FBBF24"
                  sparklineData={[7, 14, 21, 28, 28, 28, 28]}
                />
                <StatCard
                  title="Future You"
                  value="Level 9"
                  subtitle="Unlocking soon"
                  change="⚡ On Track"
                  trend="up"
                  icon="🚀"
                  accentColor="#A78BFA"
                  sparklineData={[6, 7, 7, 8, 8, 8, 9]}
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

            {/* Bottom Motivation Bar */}
            <MotivationBar />
          </main>

          {/* 3. RIGHT INFORMATION PANEL (~320px Fixed Width) */}
          <aside className="right-panel">
            {/* 1. Today's Progress */}
            <ProgressCircle
              percentage={progressData.percentage || Math.round((completedCount / (missions.length || 1)) * 100)}
              label="On Track"
            />

            {/* 2. AI Coach Card */}
            <AICoachCard
              message="You're not just dreaming— you're building. Every step today creates a stronger tomorrow."
              coachName="AI Coach"
              isOnline={true}
            />

            {/* 3. Mastery Plan */}
            <MasteryPlanCard />

            {/* 4. Today's Reflection */}
            <div className="reflection-card glass-panel">
              <div className="reflection-header">
                <span className="reflection-tag">DAILY REFLECTION</span>
                <span className="reflection-date font-display">May 28, 2024</span>
              </div>
              <h3 className="reflection-title font-serif">
                "Small choices today create extraordinary tomorrows."
              </h3>
              <button className="reflection-cta-btn">
                <span>Write Reflection →</span>
              </button>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
