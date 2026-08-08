import './HeroSection.css';

const HeroSection = () => {
  return (
    <section className="hero-container glass-panel">
      {/* Background Cosmic Particle Field */}
      <div className="cosmic-particles">
        <span className="particle p1" />
        <span className="particle p2" />
        <span className="particle p3" />
        <span className="particle p4" />
        <span className="particle p5" />
      </div>

      {/* Hero Content Column */}
      <div className="hero-content">
        <div className="hero-badge">
          <span className="hero-badge-dot" />
          <span className="hero-badge-text font-display">Daily Mastery Protocol</span>
        </div>
        <h1 className="hero-title font-serif">
          Unlock Your <br />
          <span className="gradient-text">Best Self</span>
        </h1>
        <p className="hero-subtitle">
          Your future isn't built by motivation. It is built by disciplined action repeated every day.
        </p>

        <div className="hero-actions">
          <button className="cta-primary">
            <span>Begin Today's Mission</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="5" y1="12" x2="19" y2="12"/>
              <polyline points="12 5 19 12 12 19"/>
            </svg>
          </button>
          <button className="cta-secondary">
            <span>Explore Blueprint</span>
          </button>
        </div>
      </div>

      {/* Futuristic Anchor Symbol Visual Column */}
      <div className="hero-anchor-visual" aria-label="Mastery Key Coach Anchor Symbol of Stability and Growth">
        <div className="anchor-glow-bg" />
        <svg className="anchor-svg animate-float" viewBox="0 0 320 320" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="anchorGlow" x1="160" y1="20" x2="160" y2="300" gradientUnits="userSpaceOnUse">
              <stop stopColor="#38BDF8" stopOpacity="0.9" />
              <stop offset="0.5" stopColor="#3B82F6" stopOpacity="0.8" />
              <stop offset="1" stopColor="#FBBF24" stopOpacity="0.9" />
            </linearGradient>
            <linearGradient id="anchorBodyGrad" x1="160" y1="40" x2="160" y2="280" gradientUnits="userSpaceOnUse">
              <stop stopColor="#071426" stopOpacity="0.9" />
              <stop offset="0.5" stopColor="#0C2548" stopOpacity="0.85" />
              <stop offset="1" stopColor="#050B16" stopOpacity="0.95" />
            </linearGradient>
            <linearGradient id="cyanStrokeGrad" x1="0" y1="0" x2="320" y2="320" gradientUnits="userSpaceOnUse">
              <stop stopColor="#38BDF8" />
              <stop offset="0.5" stopColor="#60A5FA" />
              <stop offset="1" stopColor="#FBBF24" />
            </linearGradient>
          </defs>

          {/* Ambient Orbital Rings */}
          <circle cx="160" cy="160" r="142" stroke="rgba(56, 189, 248, 0.12)" strokeWidth="1" strokeDasharray="6 6" />
          <circle cx="160" cy="160" r="115" stroke="rgba(59, 130, 246, 0.18)" strokeWidth="1.5" />
          <circle cx="160" cy="160" r="85" stroke="rgba(56, 189, 248, 0.1)" strokeWidth="1" />

          {/* Orbit Nodes */}
          <circle cx="160" cy="18" r="4" fill="#38BDF8" className="animate-pulse-glow" />
          <circle cx="275" cy="160" r="3.5" fill="#3B82F6" />
          <circle cx="45" cy="160" r="3.5" fill="#FBBF24" />
          <circle cx="160" cy="302" r="3" fill="#38BDF8" />

          {/* FUTURISTIC ANCHOR SYMBOL */}
          <g transform="translate(0, 5)">
            {/* Top Ring / Shackle of Hope */}
            <circle cx="160" cy="55" r="22" stroke="url(#cyanStrokeGrad)" strokeWidth="3.5" fill="rgba(7, 20, 38, 0.8)" />
            <circle cx="160" cy="55" r="12" stroke="rgba(56, 189, 248, 0.4)" strokeWidth="1.5" />
            <circle cx="160" cy="55" r="4" fill="#FBBF24" className="animate-pulse-glow" />

            {/* Horizontal Stock / Crossbar */}
            <path d="M 90 105 H 230" stroke="url(#cyanStrokeGrad)" strokeWidth="4" strokeLinecap="round" />
            <polygon points="82,105 92,98 92,112" fill="#38BDF8" />
            <polygon points="238,105 228,98 228,112" fill="#38BDF8" />

            {/* Main Vertical Spine of Discipline */}
            <rect x="153" y="77" width="14" height="155" rx="4" fill="url(#anchorBodyGrad)" stroke="url(#cyanStrokeGrad)" strokeWidth="2" />
            <line x1="160" y1="80" x2="160" y2="230" stroke="#38BDF8" strokeWidth="2" opacity="0.8" />

            {/* Core Energy Nodes */}
            <circle cx="160" cy="105" r="5" fill="#FBBF24" />
            <circle cx="160" cy="165" r="4" fill="#38BDF8" />

            {/* Curved Fluke Arms of Stability */}
            <path d="M 75 195 C 85 260, 235 260, 245 195" fill="none" stroke="url(#cyanStrokeGrad)" strokeWidth="5" strokeLinecap="round" />
            <path d="M 85 198 C 95 248, 225 248, 235 198" fill="none" stroke="rgba(7, 20, 38, 0.9)" strokeWidth="3" />

            {/* Left Fluke Arrow */}
            <path d="M 75 195 L 60 170 L 88 180 Z" fill="url(#anchorBodyGrad)" stroke="#38BDF8" strokeWidth="2" />
            <circle cx="68" cy="178" r="3" fill="#FBBF24" />

            {/* Right Fluke Arrow */}
            <path d="M 245 195 L 260 170 L 232 180 Z" fill="url(#anchorBodyGrad)" stroke="#38BDF8" strokeWidth="2" />
            <circle cx="252" cy="178" r="3" fill="#FBBF24" />

            {/* Bottom Crown Base Point */}
            <polygon points="160,262 148,238 172,238" fill="url(#anchorBodyGrad)" stroke="#38BDF8" strokeWidth="2" />
            <circle cx="160" cy="250" r="4" fill="#38BDF8" />
          </g>
        </svg>
      </div>
    </section>
  );
};

export default HeroSection;
