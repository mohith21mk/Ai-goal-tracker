import { Target, Bot, CheckCircle2, TrendingUp, Trophy, ArrowDown } from 'lucide-react';
import "./MasteryLoop.css";

function MasteryLoop() {
  return (
    <section className="mastery-loop">

      <h2>The Mastery Loop</h2>

      <p className="loop-subtitle">
        Discipline isn't built overnight.
        It's created through small actions repeated every day.
      </p>

      <div className="loop-container">

        <div className="loop-card">
          <div className="loop-icon-box">
            <Target size={24} strokeWidth={1.8} style={{ color: '#38BDF8', filter: 'drop-shadow(0 0 6px rgba(56, 189, 248, 0.4))' }} aria-hidden="true" />
          </div>
          <h3>1. Set Your Goal</h3>
          <p>
            Define one meaningful goal you want to achieve.
          </p>
        </div>

        <div className="arrow"><ArrowDown size={20} strokeWidth={1.8} aria-hidden="true" /></div>

        <div className="loop-card">
          <div className="loop-icon-box">
            <Bot size={24} strokeWidth={1.8} style={{ color: '#A78BFA', filter: 'drop-shadow(0 0 6px rgba(167, 139, 250, 0.4))' }} aria-hidden="true" />
          </div>
          <h3>2. AI Creates Daily Missions</h3>
          <p>
            Your AI coach breaks the goal into simple daily tasks.
          </p>
        </div>

        <div className="arrow"><ArrowDown size={20} strokeWidth={1.8} aria-hidden="true" /></div>

        <div className="loop-card">
          <div className="loop-icon-box">
            <CheckCircle2 size={24} strokeWidth={1.8} style={{ color: '#10B981', filter: 'drop-shadow(0 0 6px rgba(16, 185, 129, 0.4))' }} aria-hidden="true" />
          </div>
          <h3>3. Complete Today's Mission</h3>
          <p>
            Small consistent actions build momentum.
          </p>
        </div>

        <div className="arrow"><ArrowDown size={20} strokeWidth={1.8} aria-hidden="true" /></div>

        <div className="loop-card">
          <div className="loop-icon-box">
            <TrendingUp size={24} strokeWidth={1.8} style={{ color: '#3B82F6', filter: 'drop-shadow(0 0 6px rgba(59, 130, 246, 0.4))' }} aria-hidden="true" />
          </div>
          <h3>4. Track Progress</h3>
          <p>
            Every completed mission increases your consistency score.
          </p>
        </div>

        <div className="arrow"><ArrowDown size={20} strokeWidth={1.8} aria-hidden="true" /></div>

        <div className="loop-card">
          <div className="loop-icon-box">
            <Trophy size={24} strokeWidth={1.8} style={{ color: '#FBBF24', filter: 'drop-shadow(0 0 6px rgba(251, 191, 36, 0.4))' }} aria-hidden="true" />
          </div>
          <h3>5. Build Discipline</h3>
          <p>
            Daily consistency becomes long-term discipline.
          </p>
        </div>

      </div>

    </section>
  );
}

export default MasteryLoop;