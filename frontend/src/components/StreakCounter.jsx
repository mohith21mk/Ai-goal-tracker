import { Flame, Zap } from 'lucide-react';
import './StreakCounter.css';

const StreakCounter = ({ days = 28, label = 'Days Strong' }) => {
  return (
    <div className="streak-counter glass-card">
      <div className="streak-icon"><Flame size={28} strokeWidth={1.8} /></div>
      
      <div className="streak-content">
        <div className="streak-days">{days}</div>
        <div className="streak-label">{label}</div>
      </div>

      <div className="streak-progress-bar">
        <div 
          className="streak-progress-fill"
          style={{ width: `${Math.min((days / 365) * 100, 100)}%` }}
        ></div>
      </div>

      <p className="streak-message">
        Keep the momentum going! <Zap size={16} strokeWidth={1.8} style={{ display: 'inline-block', verticalAlign: 'middle' }} />
      </p>
    </div>
  );
};

export default StreakCounter;
