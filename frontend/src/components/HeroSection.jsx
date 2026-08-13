import { Link } from 'react-router-dom';
import MKCLogo from './MKCLogo';
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
          <Link to="/blueprint" className="cta-primary" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            <span>Explore Blueprint</span>
          </Link>
        </div>
      </div>

      {/* Futuristic Anchor Symbol Visual Column */}
      <div className="hero-anchor-visual" aria-label="Mastery Key Coach Anchor Symbol of Stability and Growth">
        <div className="anchor-glow-bg" />
        <MKCLogo className="anchor-svg animate-float" style={{ width: '100%', maxWidth: '320px', height: 'auto' }} />
      </div>
    </section>
  );
};

export default HeroSection;
