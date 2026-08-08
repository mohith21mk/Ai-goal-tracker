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

      {/* Hero Anchor Visual Column (Pure SVG + CSS Cosmic Graphic) */}
      <div className="hero-anchor-visual">
        <div className="anchor-glow-bg" />
        <svg className="anchor-svg animate-float" viewBox="0 0 320 320" fill="none" xmlns="http://www.w3.org/2000/svg">
          {/* Outer Orbit Rings */}
          <circle cx="160" cy="160" r="140" stroke="rgba(56, 189, 248, 0.15)" strokeWidth="1" strokeDasharray="6 6" />
          <circle cx="160" cy="160" r="110" stroke="url(#orbitGrad)" strokeWidth="1.5" />
          <circle cx="160" cy="160" r="80" stroke="rgba(59, 130, 246, 0.2)" strokeWidth="1" />

          {/* Orbiting Energy Nodes */}
          <circle cx="160" cy="20" r="4" fill="#38BDF8" className="animate-pulse-glow" />
          <circle cx="270" cy="160" r="3" fill="#3B82F6" />
          <circle cx="50" cy="160" r="3" fill="#FBBF24" />

          {/* Cosmic Diamond Anchor Shape */}
          <g transform="translate(160, 160) scale(1.1)">
            {/* Upper Crown Pyramid */}
            <polygon points="0,-80 45,-30 0,-10 -45,-30" fill="url(#anchorFacet1)" stroke="#38BDF8" strokeWidth="1.5" />
            
            {/* Center Core Diamond */}
            <polygon points="0,-10 45,-30 55,20 0,60 -55,20 -45,-30" fill="url(#anchorFacet2)" stroke="#38BDF8" strokeWidth="1.5" />
            
            {/* Inner Glowing Core Lines */}
            <line x1="0" y1="-80" x2="0" y2="60" stroke="#38BDF8" strokeWidth="2" opacity="0.8" />
            <line x1="-55" y1="20" x2="55" y2="20" stroke="#38BDF8" strokeWidth="1.5" opacity="0.6" />

            {/* Gold Energy Point (Lower Center) */}
            <circle cx="0" cy="20" r="7" fill="#FBBF24" />
            <circle cx="0" cy="20" r="14" stroke="#FBBF24" strokeWidth="1.5" strokeOpacity="0.6" className="animate-pulse-glow" />

            {/* Cyan Luminous Edges */}
            <circle cx="0" cy="-80" r="5" fill="#38BDF8" />
            <circle cx="45" cy="-30" r="3" fill="#38BDF8" />
            <circle cx="-45" cy="-30" r="3" fill="#38BDF8" />
            <circle cx="0" cy="60" r="4" fill="#38BDF8" />
          </g>

          <defs>
            <linearGradient id="orbitGrad" x1="20" y1="160" x2="300" y2="160" gradientUnits="userSpaceOnUse">
              <stop stopColor="#38BDF8" stopOpacity="0.6" />
              <stop offset="0.5" stopColor="#3B82F6" stopOpacity="0.2" />
              <stop offset="1" stopColor="#FBBF24" stopOpacity="0.6" />
            </linearGradient>

            <linearGradient id="anchorFacet1" x1="0" y1="-80" x2="0" y2="-10" gradientUnits="userSpaceOnUse">
              <stop stopColor="#38BDF8" stopOpacity="0.4" />
              <stop offset="1" stopColor="#071426" stopOpacity="0.8" />
            </linearGradient>

            <linearGradient id="anchorFacet2" x1="0" y1="-30" x2="0" y2="60" gradientUnits="userSpaceOnUse">
              <stop stopColor="#071426" stopOpacity="0.9" />
              <stop offset="0.5" stopColor="#0c2548" stopOpacity="0.8" />
              <stop offset="1" stopColor="#38BDF8" stopOpacity="0.3" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    </section>
  );
};

export default HeroSection;
