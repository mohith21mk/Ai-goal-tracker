import { ShieldCheck, Award, Flame, Zap, Layers, Trophy, Sparkles } from 'lucide-react';
import './VictoryCredentialCard.css';

const TIER_META = {
  bronze: {
    label: 'BRONZE TIER',
    color: '#CD7F32',
    bg: 'rgba(205, 127, 50, 0.12)',
    border: 'rgba(205, 127, 50, 0.35)',
    glow: 'rgba(205, 127, 50, 0.2)'
  },
  silver: {
    label: 'SILVER TIER',
    color: '#E2E8F0',
    bg: 'rgba(226, 232, 240, 0.12)',
    border: 'rgba(226, 232, 240, 0.4)',
    glow: 'rgba(226, 232, 240, 0.2)'
  },
  gold: {
    label: 'GOLD TIER',
    color: '#FBBF24',
    bg: 'rgba(251, 191, 36, 0.12)',
    border: 'rgba(251, 191, 36, 0.45)',
    glow: 'rgba(251, 191, 36, 0.25)'
  },
  platinum: {
    label: 'PLATINUM TIER',
    color: '#38BDF8',
    bg: 'rgba(56, 189, 248, 0.14)',
    border: 'rgba(56, 189, 248, 0.5)',
    glow: 'rgba(56, 189, 248, 0.3)'
  },
  diamond: {
    label: 'DIAMOND TIER',
    color: '#A78BFA',
    bg: 'rgba(167, 139, 250, 0.16)',
    border: 'rgba(167, 139, 250, 0.55)',
    glow: 'rgba(167, 139, 250, 0.35)'
  }
};

export default function VictoryCredentialCard({
  credential,
  userName = 'Member',
  compact = false,
  interactive = true,
  selected = false,
  onClick
}) {
  if (!credential) return null;

  const tierKey = (credential.tier || 'bronze').toLowerCase();
  const tier = TIER_META[tierKey] || TIER_META.bronze;

  const getIcon = () => {
    const slug = credential.slug || '';
    const type = credential.credential_type || '';
    if (slug.includes('streak') || type.includes('streak')) return <Flame size={compact ? 14 : 20} strokeWidth={2} />;
    if (slug.includes('missions') || type.includes('mission')) return <Zap size={compact ? 14 : 20} strokeWidth={2} />;
    if (slug.includes('blueprint') || type.includes('blueprint')) return <Layers size={compact ? 14 : 20} strokeWidth={2} />;
    if (slug.includes('mastery') || type.includes('mastery')) return <Trophy size={compact ? 14 : 20} strokeWidth={2} />;
    return <Award size={compact ? 14 : 20} strokeWidth={2} />;
  };

  const formattedDate = credential.issued_at
    ? new Date(credential.issued_at).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    : 'Verified';

  if (compact) {
    return (
      <div
        className={`victory-chip tier-${tierKey} ${interactive ? 'interactive' : ''} ${selected ? 'selected' : ''}`}
        onClick={onClick}
        title={`${credential.title} (${tier.label}) — Click to view Certificate`}
        style={{
          '--tier-color': tier.color,
          '--tier-bg': tier.bg,
          '--tier-border': tier.border,
          '--tier-glow': tier.glow
        }}
      >
        <span className="chip-icon" style={{ color: tier.color }}>{getIcon()}</span>
        <span className="chip-title">{credential.title}</span>
        <span className="chip-tier-tag">{tierKey.toUpperCase()}</span>
      </div>
    );
  }

  return (
    <div
      className={`victory-card glass-panel tier-${tierKey} ${interactive ? 'interactive' : ''} ${selected ? 'selected' : ''}`}
      onClick={onClick}
      style={{
        '--tier-color': tier.color,
        '--tier-bg': tier.bg,
        '--tier-border': tier.border,
        '--tier-glow': tier.glow
      }}
    >
      <div className="victory-card-header">
        <div className="victory-badge-icon" style={{ color: tier.color }}>
          {getIcon()}
        </div>
        <div className="victory-verification-tag">
          <ShieldCheck size={13} strokeWidth={2.2} />
          <span>MKC VERIFIED</span>
        </div>
      </div>

      <div className="victory-card-body">
        <span className="victory-tier-label">{tier.label}</span>
        <h4 className="victory-title font-serif">{credential.title}</h4>
        <p className="victory-description">{credential.description}</p>
      </div>

      <div className="victory-card-footer">
        <div className="victory-xp-reward" style={{ color: tier.color }}>
          <Sparkles size={13} />
          <span>+{credential.xp_value || 50} XP</span>
        </div>
        <div className="victory-meta">
          <span className="victory-user font-display">{userName}</span>
          <span className="victory-date">{formattedDate}</span>
        </div>
      </div>
      <div className="victory-card-glow" />
    </div>
  );
}
