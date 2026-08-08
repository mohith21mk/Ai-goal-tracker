import './ProgressCircle.css';

const ProgressCircle = ({ percentage = 84, label = 'On Track' }) => {
  const radius = 68;
  const strokeWidth = 10;
  const normalizedRadius = radius - strokeWidth * 0.5;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="progress-card-container glass-panel">
      <div className="progress-card-header">
        <h3 className="progress-card-title">Today's Progress</h3>
        <span className="progress-badge">● Active Protocol</span>
      </div>

      <div className="progress-ring-wrapper">
        <svg height={radius * 2} width={radius * 2} className="progress-ring-svg">
          <defs>
            <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#38BDF8" />
              <stop offset="50%" stopColor="#3B82F6" />
              <stop offset="100%" stopColor="#FBBF24" />
            </linearGradient>
            <filter id="cyanGlowFilter" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Background Track Circle */}
          <circle
            stroke="rgba(148, 163, 184, 0.12)"
            fill="transparent"
            strokeWidth={strokeWidth}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />

          {/* Animated Progress Circle */}
          <circle
            stroke="url(#ringGradient)"
            fill="transparent"
            strokeWidth={strokeWidth}
            strokeDasharray={`${circumference} ${circumference}`}
            style={{ strokeDashoffset }}
            strokeLinecap="round"
            filter="url(#cyanGlowFilter)"
            r={normalizedRadius}
            cx={radius}
            cy={radius}
            className="progress-ring-circle"
          />
        </svg>

        <div className="progress-center-text">
          <span className="progress-number font-display">{percentage}%</span>
          <span className="progress-label">{label}</span>
        </div>
      </div>

      <div className="progress-stats-grid">
        <div className="progress-stat-item">
          <span className="stat-name">Discipline</span>
          <span className="stat-val highlight-cyan">Strong</span>
        </div>
        <div className="progress-stat-item">
          <span className="stat-name">Mindset</span>
          <span className="stat-val highlight-blue">Focused</span>
        </div>
        <div className="progress-stat-item">
          <span className="stat-name">Execution</span>
          <span className="stat-val highlight-gold">Excellent</span>
        </div>
        <div className="progress-stat-item">
          <span className="stat-name">Consistency</span>
          <span className="stat-val highlight-green">Building</span>
        </div>
      </div>
    </div>
  );
};

export default ProgressCircle;
