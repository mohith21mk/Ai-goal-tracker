import { Flame, Bot, Trophy, TrendingUp } from 'lucide-react';

function Features() {
  return (
    <section className="features">
      <h2>Why Mastery Key Coach?</h2>

      <div className="feature-grid">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Flame size={18} strokeWidth={1.8} style={{ color: '#38BDF8', filter: 'drop-shadow(0 0 5px rgba(56, 189, 248, 0.4))' }} aria-hidden="true" />
          <span>Daily Missions</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Bot size={18} strokeWidth={1.8} style={{ color: '#A78BFA', filter: 'drop-shadow(0 0 5px rgba(167, 139, 250, 0.4))' }} aria-hidden="true" />
          <span>AI Coach</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Trophy size={18} strokeWidth={1.8} style={{ color: '#FBBF24', filter: 'drop-shadow(0 0 5px rgba(251, 191, 36, 0.4))' }} aria-hidden="true" />
          <span>Achievements</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <TrendingUp size={18} strokeWidth={1.8} style={{ color: '#10B981', filter: 'drop-shadow(0 0 5px rgba(16, 185, 129, 0.4))' }} aria-hidden="true" />
          <span>Progress Analytics</span>
        </div>
      </div>
    </section>
  );
}

export default Features;