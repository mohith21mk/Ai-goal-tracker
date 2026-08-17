import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import './StatCard.css';

// Data-driven mini SVG sparkline path helper
const Sparkline = ({ color = '#38BDF8', data = [0, 0, 0, 0, 0, 0, 0] }) => {
  const width = 80;
  const height = 24;
  const padding = 3;

  const pts = Array.isArray(data) && data.length > 0 ? data.map(n => (isNaN(Number(n)) ? 0 : Number(n))) : [0, 0, 0, 0, 0, 0, 0];

  const min = Math.min(...pts);
  const max = Math.max(...pts);
  const diff = max - min;

  const points = pts
    .map((val, i) => {
      const x = (i / (pts.length - 1)) * width;
      let y;
      if (diff === 0) {
        y = max === 0 ? height - padding : height / 2;
      } else {
        y = height - padding - ((val - min) / diff) * (height - 2 * padding);
      }
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  return (
    <svg width={width} height={height} className="stat-sparkline" viewBox={`0 0 ${width} ${height}`}>
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
  // Determine trend direction and clean label if numeric or string number
  let effectiveTrend = trend;
  let displayChange = change;

  if (change !== undefined && change !== null) {
    const rawStr = String(change).replace(/^[+]/, '');
    const parsedNum = Number(rawStr);
    if (!isNaN(parsedNum)) {
      if (parsedNum > 0) {
        effectiveTrend = 'up';
        displayChange = `+${parsedNum}`;
      } else if (parsedNum < 0) {
        effectiveTrend = 'down';
        displayChange = `${parsedNum}`;
      } else {
        effectiveTrend = 'neutral';
        displayChange = `0`;
      }
    }
  }

  return (
    <div className="stat-card glass-panel">
      <div className="stat-card-header">
        <span className="stat-title">{title}</span>
        {icon && (
          <div
            className="stat-icon"
            style={{
              color: accentColor,
              backgroundColor: `${accentColor}18`,
              borderColor: `${accentColor}40`,
              boxShadow: `0 0 16px ${accentColor}28, inset 0 1px 0 ${accentColor}25`
            }}
          >
            {icon}
          </div>
        )}
      </div>

      <div className="stat-card-body">
        <div className="stat-value-container">
          <span className="stat-value">{value}</span>
          {unit && <span className="stat-unit">{unit}</span>}
        </div>

        <div className="stat-sparkline-wrapper">
          <Sparkline color={accentColor} data={sparklineData || [0, 0, 0, 0, 0, 0, 0]} />
        </div>
      </div>

      <div className="stat-card-footer">
        <span className="stat-subtitle">{subtitle}</span>
        {change !== undefined && change !== null && (
          <span className={`stat-change ${effectiveTrend}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '2px' }}>
            {effectiveTrend === 'up' && <ArrowUp size={12} strokeWidth={2.5} aria-hidden="true" />}
            {effectiveTrend === 'down' && <ArrowDown size={12} strokeWidth={2.5} aria-hidden="true" />}
            {effectiveTrend === 'neutral' && <Minus size={12} strokeWidth={2.5} aria-hidden="true" />}
            {displayChange}
          </span>
        )}
      </div>

      <div className="stat-card-border-glow" style={{ background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)` }} />
    </div>
  );
};

export default StatCard;
