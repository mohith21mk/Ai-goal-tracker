import './MasteryPlanCard.css';

const MasteryPlanCard = ({ activeGoal, linkedMissions = [], telemetryBlueprint = null }) => {
  const goalTitle = telemetryBlueprint?.current_phase || activeGoal?.title || 'Phase 2: AI & Machine Learning';
  const goalCategory = telemetryBlueprint?.title ? 'ACTIVE BLUEPRINT' : activeGoal?.category ? activeGoal.category.toUpperCase() : 'ACTIVE BLUEPRINT';
  
  const completedMestones = telemetryBlueprint?.completed_milestones ?? linkedMissions.filter(m => m.completed).length;
  const totalMestones = telemetryBlueprint?.total_milestones ?? linkedMissions.length;

  const progressPercent = telemetryBlueprint?.progress_percentage ?? (totalMestones > 0
    ? Math.round((completedMestones / totalMestones) * 100)
    : 38);

  const nextStepText = telemetryBlueprint?.next_milestone || activeGoal?.description || 'Build AI Project Portfolio';

  return (
    <div className="mastery-plan-card glass-panel">
      {/* Header Banner Graphic */}
      <div className="plan-header-banner">
        <svg className="cosmic-mountain-svg" viewBox="0 0 300 80" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0 80L80 30L150 60L230 15L300 80H0Z" fill="url(#mountainGrad1)" />
          <path d="M40 80L120 40L200 65L300 35V80H40Z" fill="url(#mountainGrad2)" />
          <circle cx="230" cy="15" r="4" fill="#FBBF24" className="animate-pulse-glow" />
          <line x1="0" y1="79" x2="300" y2="79" stroke="#38BDF8" strokeWidth="1" strokeOpacity="0.4" />
          <defs>
            <linearGradient id="mountainGrad1" x1="150" y1="15" x2="150" y2="80" gradientUnits="userSpaceOnUse">
              <stop stopColor="#38BDF8" stopOpacity="0.25" />
              <stop offset="1" stopColor="#071426" stopOpacity="0.8" />
            </linearGradient>
            <linearGradient id="mountainGrad2" x1="170" y1="35" x2="170" y2="80" gradientUnits="userSpaceOnUse">
              <stop stopColor="#3B82F6" stopOpacity="0.3" />
              <stop offset="1" stopColor="#050B16" stopOpacity="0.9" />
            </linearGradient>
          </defs>
        </svg>

        <div className="plan-banner-overlay">
          <span className="plan-tag">{goalCategory}</span>
          <h3 className="plan-main-title font-display">The Mastery Plan</h3>
        </div>
      </div>

      {/* Content */}
      <div className="plan-body">
        <div className="milestone-info">
          <span className="milestone-phase font-display">{goalTitle}</span>
          <span className="steps-count">
            {totalMestones > 0 ? `${completedMestones}/${totalMestones} Milestones` : '3/8 Milestones'}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="plan-progress-track">
          <div className="plan-progress-fill" style={{ width: `${progressPercent}%` }} />
        </div>

        {/* Next Milestone Step Badge */}
        <div className="next-step-badge">
          <div className="next-step-icon">🎯</div>
          <div className="next-step-details">
            <span className="next-step-label">NEXT MILESTONE</span>
            <span className="next-step-name">{nextStepText}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MasteryPlanCard;
