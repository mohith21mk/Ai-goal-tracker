import './StatCard.css';

// Simple helper to draw a mini SVG sparkline path
const Sparkline = ({ color = '#38BDF8', data = [30, 45, 35, 60, 50, 75, 90] }) => {
  const width = 80;
  const height = 24;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data
    .map((val, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((val - min) / range) * (height - 4) - 2;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg width={width} height={height} className="stat-sparkline">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
};

const StatCard = ({
  title,
  value,
  unit,
  subtitle,
  change,
  trend = 'up',
  icon,
  sparklineData,
  accentColor = '#38BDF8'
}) => {
  return (
    <div className="stat-card glass-panel">
      <div className="stat-card-header">
        <span className="stat-title">{title}</span>
        {icon && <span className="stat-icon">{icon}</span>}
      </div>

      <div className="stat-card-body">
        <div className="stat-value-container">
          <span className="stat-value">{value}</span>
          {unit && <span className="stat-unit">{unit}</span>}
        </div>

        <div className="stat-sparkline-wrapper">
          <Sparkline color={accentColor} data={sparklineData || [40, 50, 45, 65, 60, 80, 92]} />
        </div>
      </div>

      <div className="stat-card-footer">
        <span className="stat-subtitle">{subtitle}</span>
        {change && (
          <span className={`stat-change ${trend === 'down' ? 'negative' : 'positive'}`}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : ''} {change}
          </span>
        )}
      </div>

      <div className="stat-card-border-glow" style={{ background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)` }} />
    </div>
  );
};

export default StatCard;
