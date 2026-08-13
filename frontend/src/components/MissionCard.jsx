import { Clock } from 'lucide-react';
import './MissionCard.css';

const MissionCard = ({
  title,
  category = 'general',
  time = '15 min',
  difficulty = 'easy',
  completed = false,
  xpReward = 10,
  onComplete
}) => {
  return (
    <div
      className={`mission-card glass-panel ${completed ? 'completed' : ''}`}
      onClick={onComplete}
    >
      <div className="mission-checkbox-wrapper">
        <div className={`mission-checkbox ${completed ? 'checked' : ''}`}>
          {completed && (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#050B16" strokeWidth="3.5">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          )}
        </div>
      </div>

      <div className="mission-content">
        <div className="mission-header-tags">
          <span className={`category-tag tag-${category}`}>{category}</span>
          <span className={`difficulty-tag difficulty-${difficulty}`}>{difficulty}</span>
          <span className="time-tag"><Clock size={12} strokeWidth={1.8} style={{ marginRight: '4px' }} /> {time}</span>
        </div>
        <h4 className={`mission-title ${completed ? 'strikethrough' : ''}`}>{title}</h4>
      </div>

      <div className="mission-xp-badge">
        <span className="xp-text">+{xpReward} XP</span>
      </div>
    </div>
  );
};

export default MissionCard;
