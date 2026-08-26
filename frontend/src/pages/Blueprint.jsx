import { useState, useEffect } from 'react';
import { Sparkles, TriangleAlert, Rocket, Target, Trash2, Calendar, Check, X } from 'lucide-react';
import {
  getActiveBlueprint,
  createBlueprint,
  createBlueprintPhase,
  createBlueprintMilestone,
  toggleBlueprintMilestone,
  deleteBlueprintMilestone,
  deleteBlueprintPhase
} from '../services/api';
import './Blueprint.css';

const Blueprint = () => {
  const [activeBlueprint, setActiveBlueprint] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals state
  const [showBpModal, setShowBpModal] = useState(false);
  const [showPhaseModal, setShowPhaseModal] = useState(false);
  const [showMilestoneModal, setShowMilestoneModal] = useState(false);
  const [selectedPhaseId, setSelectedPhaseId] = useState(null);

  // Form states
  const [bpTitle, setBpTitle] = useState('');
  const [bpVision, setBpVision] = useState('');
  const [bpTargetDate, setBpTargetDate] = useState('2028-06-30');

  const [phaseTitle, setPhaseTitle] = useState('');
  const [phaseDesc, setPhaseDesc] = useState('');

  const [msTitle, setMsTitle] = useState('');
  const [msDesc, setMsDesc] = useState('');
  const [msTargetDate, setMsTargetDate] = useState('');

  const loadBlueprintData = async () => {
    try {
      const res = await getActiveBlueprint();
      if (res && res.blueprint) {
        setActiveBlueprint(res.blueprint);
      } else {
        setActiveBlueprint(null);
      }
      setError(null);
    } catch (err) {
      console.error('Failed to load active blueprint:', err);
      setError('Could not connect to blueprint service.');
    }
  };

  useEffect(() => {
    let isMounted = true;
    async function init() {
      try {
        const res = await getActiveBlueprint();
        if (isMounted) {
          if (res && res.blueprint) {
            setActiveBlueprint(res.blueprint);
          } else {
            setActiveBlueprint(null);
          }
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to load blueprint:', err);
          setError('Could not connect to blueprint service.');
          setLoading(false);
        }
      }
    }
    init();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleCreateBlueprint = async (e) => {
    e.preventDefault();
    if (!bpTitle.trim()) return;
    try {
      await createBlueprint({
        title: bpTitle,
        vision: bpVision,
        target_date: bpTargetDate,
        set_active: true
      });
      setShowBpModal(false);
      setBpTitle('');
      setBpVision('');
      await loadBlueprintData();
    } catch (err) {
      alert(err.message || 'Failed to create blueprint.');
    }
  };

  const handleCreatePhase = async (e) => {
    e.preventDefault();
    if (!activeBlueprint || !phaseTitle.trim()) return;
    try {
      await createBlueprintPhase(activeBlueprint.id, {
        title: phaseTitle,
        description: phaseDesc
      });
      setShowPhaseModal(false);
      setPhaseTitle('');
      setPhaseDesc('');
      await loadBlueprintData();
    } catch (err) {
      alert(err.message || 'Failed to create phase.');
    }
  };

  const handleCreateMilestone = async (e) => {
    e.preventDefault();
    if (!selectedPhaseId || !msTitle.trim()) return;
    try {
      await createBlueprintMilestone(selectedPhaseId, {
        title: msTitle,
        description: msDesc,
        target_date: msTargetDate
      });
      setShowMilestoneModal(false);
      setMsTitle('');
      setMsDesc('');
      setMsTargetDate('');
      await loadBlueprintData();
    } catch (err) {
      alert(err.message || 'Failed to create milestone.');
    }
  };

  const handleToggleMilestone = async (milestoneId) => {
    try {
      await toggleBlueprintMilestone(milestoneId);
      await loadBlueprintData();
    } catch (err) {
      console.error('Error toggling milestone:', err);
    }
  };

  const handleDeleteMilestone = async (milestoneId) => {
    if (!window.confirm('Delete this milestone?')) return;
    try {
      await deleteBlueprintMilestone(milestoneId);
      await loadBlueprintData();
    } catch (err) {
      alert(err.message || 'Failed to delete milestone.');
    }
  };

  const handleDeletePhase = async (phaseId) => {
    if (!window.confirm('Delete this phase and its milestones?')) return;
    try {
      await deleteBlueprintPhase(phaseId);
      await loadBlueprintData();
    } catch (err) {
      alert(err.message || 'Failed to delete phase.');
    }
  };

  const openMilestoneModal = (phaseId) => {
    setSelectedPhaseId(phaseId);
    setShowMilestoneModal(true);
  };

  // Helper for Days Remaining calculation
  const getDaysRemaining = (targetDateStr) => {
    if (!targetDateStr) return null;
    const target = new Date(targetDateStr);
    const today = new Date();
    const diffTime = target - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 0;
  };

  return (
    <div className="blueprint-container">
          {/* Header */}
          <div className="blueprint-header-section">
            <div className="blueprint-header-left">
              <h1 className="font-serif">Life Blueprint</h1>
              <p>Architect your long-term vision into milestone protocols.</p>
            </div>
            <button
              onClick={() => setShowBpModal(true)}
              className="btn-create-blueprint-primary"
            >
              <Sparkles size={16} strokeWidth={1.8} aria-hidden="true" />
              <span>{activeBlueprint ? 'New Blueprint' : 'Build Blueprint'}</span>
            </button>
          </div>

          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 16px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '12px', color: '#EF4444', marginBottom: '24px' }}>
              <TriangleAlert size={16} strokeWidth={1.8} aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-tertiary)' }}>Loading Life Blueprint architecture...</div>
          ) : !activeBlueprint ? (
            <div className="blueprint-empty-card glass-panel">
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px' }}>
                <Rocket size={44} strokeWidth={1.8} style={{ color: 'var(--cyan)', filter: 'drop-shadow(0 0 10px rgba(56, 189, 248, 0.4))' }} aria-hidden="true" />
              </div>
              <h3 className="font-display">Build Your Life Blueprint</h3>
              <p>Define your long-term vision, group focus into Life Areas, and organize execution into structured Phases and Milestones.</p>
              <button
                onClick={() => setShowBpModal(true)}
                className="btn-create-blueprint-primary"
                style={{ marginTop: '16px' }}
              >
                <span>Create Active Blueprint</span>
              </button>
            </div>
          ) : (
            <>
              {/* Blueprint Hero Card */}
              <div className="blueprint-hero-card glass-panel">
                <div className="blueprint-hero-top">
                  <div>
                    <div className="blueprint-title-row">
                      <h2>{activeBlueprint.title}</h2>
                      <span className="active-status-badge">ACTIVE BLUEPRINT</span>
                    </div>
                    {activeBlueprint.vision && (
                      <p className="blueprint-vision-quote">"{activeBlueprint.vision}"</p>
                    )}
                  </div>
                  {activeBlueprint.target_date && (
                    <div className="blueprint-target-tag" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Target size={16} strokeWidth={1.8} style={{ color: 'var(--cyan)' }} aria-hidden="true" />
                      <span>Target: <strong>{activeBlueprint.target_date}</strong> ({getDaysRemaining(activeBlueprint.target_date)} days remaining)</span>
                    </div>
                  )}
                </div>

                <div className="blueprint-progress-section">
                  <div className="blueprint-progress-header">
                    <span>Overall Blueprint Progress</span>
                    <span>{activeBlueprint.completed_milestones} / {activeBlueprint.total_milestones} Milestones ({activeBlueprint.progress_percentage}%)</span>
                  </div>
                  <div className="blueprint-progress-bar-bg">
                    <div
                      className="blueprint-progress-bar-fill"
                      style={{ width: `${activeBlueprint.progress_percentage}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Life Areas Showcase */}
              {activeBlueprint.areas && activeBlueprint.areas.length > 0 && (
                <div className="life-areas-section">
                  <h3 className="section-section-title">Life Areas</h3>
                  <div className="areas-grid">
                    {activeBlueprint.areas.map((area) => (
                      <div key={area.id} className="area-card glass-panel">
                        <div className="area-icon-box">{area.icon || <Target size={16} strokeWidth={1.8} style={{ color: 'var(--cyan)' }} aria-hidden="true" />}</div>
                        <div className="area-details">
                          <h4>{area.name}</h4>
                          <p>{area.description || 'Core focus vector'}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Phase Timeline & Accordion */}
              <div className="phases-timeline-container">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 className="section-section-title" style={{ margin: 0 }}>Strategic Phases & Milestone Protocols</h3>
                  <button
                    onClick={() => setShowPhaseModal(true)}
                    className="btn-add-milestone"
                  >
                    + Add Phase
                  </button>
                </div>

                {activeBlueprint.phases && activeBlueprint.phases.map((phase) => (
                  <div
                    key={phase.id}
                    className={`phase-card-item glass-panel ${phase.status === 'active' ? 'active-phase' : ''}`}
                  >
                    <div className="phase-header-row">
                      <div className="phase-title-group">
                        <span className="phase-num-badge">Phase {phase.phase_number}</span>
                        <span className="phase-title-text">{phase.title}</span>
                        <span style={{ fontSize: '11px', textTransform: 'uppercase', color: phase.status === 'completed' ? 'var(--cyan)' : phase.status === 'active' ? 'var(--accent-gold)' : 'var(--text-tertiary)' }}>
                          • {phase.status}
                        </span>
                      </div>

                      <div className="phase-actions-right">
                        <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                          {phase.completed_milestones}/{phase.total_milestones} ({phase.progress_percentage}%)
                        </span>
                        <button
                          onClick={() => openMilestoneModal(phase.id)}
                          className="btn-add-milestone"
                        >
                          + Milestone
                        </button>
                        <button
                          onClick={() => handleDeletePhase(phase.id)}
                          style={{ background: 'transparent', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                          title="Delete Phase"
                        >
                          <Trash2 size={16} strokeWidth={1.8} aria-hidden="true" />
                        </button>
                      </div>
                    </div>

                    {phase.description && (
                      <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{phase.description}</p>
                    )}

                    {/* Phase Progress Bar */}
                    <div className="blueprint-progress-bar-bg" style={{ height: '6px' }}>
                      <div
                        className="blueprint-progress-bar-fill"
                        style={{ width: `${phase.progress_percentage}%` }}
                      />
                    </div>

                    {/* Milestones Checklist */}
                    {phase.milestones && phase.milestones.length > 0 && (
                      <div className="milestones-list">
                        {phase.milestones.map((ms) => (
                          <div
                            key={ms.id}
                            className={`milestone-item ${ms.completed ? 'completed' : ''}`}
                          >
                            <div className="milestone-left">
                              <button
                                onClick={() => handleToggleMilestone(ms.id)}
                                className={`milestone-check-btn ${ms.completed ? 'checked' : ''}`}
                              >
                                {ms.completed && <Check size={12} strokeWidth={2.5} aria-hidden="true" />}
                              </button>
                              <div className="milestone-info-text">
                                <h5>{ms.title}</h5>
                                {ms.description && <p>{ms.description}</p>}
                              </div>
                            </div>

                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                              {ms.target_date && (
                                <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                  <Calendar size={12} strokeWidth={1.8} aria-hidden="true" /> {ms.target_date}
                                </span>
                              )}
                              <button
                                onClick={() => handleDeleteMilestone(ms.id)}
                                className="milestone-delete-btn"
                                title="Delete Milestone"
                              >
                                <Trash2 size={14} strokeWidth={1.8} aria-hidden="true" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Modal: Create Blueprint */}
          {showBpModal && (
            <div className="modal-overlay">
              <div className="modal-content-card">
                <div className="modal-header">
                  <h3>Build New Life Blueprint</h3>
                  <button onClick={() => setShowBpModal(false)} className="modal-close-btn"><X size={16} /></button>
                </div>
                <form onSubmit={handleCreateBlueprint} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div className="modal-form-group">
                    <label>Blueprint Title</label>
                    <input
                      type="text"
                      placeholder="e.g. Become an AI Engineer by 2028"
                      value={bpTitle}
                      onChange={(e) => setBpTitle(e.target.value)}
                      className="modal-input"
                      required
                    />
                  </div>
                  <div className="modal-form-group">
                    <label>Long-Term Vision Statement</label>
                    <input
                      type="text"
                      placeholder="e.g. Building production-grade intelligent AI systems."
                      value={bpVision}
                      onChange={(e) => setBpVision(e.target.value)}
                      className="modal-input"
                    />
                  </div>
                  <div className="modal-form-group">
                    <label>Target Completion Date</label>
                    <input
                      type="date"
                      value={bpTargetDate}
                      onChange={(e) => setBpTargetDate(e.target.value)}
                      className="modal-input"
                    />
                  </div>
                  <div className="modal-actions">
                    <button type="button" onClick={() => setShowBpModal(false)} className="btn-modal-cancel">Cancel</button>
                    <button type="submit" className="btn-modal-submit">Create Blueprint</button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Modal: Add Phase */}
          {showPhaseModal && (
            <div className="modal-overlay">
              <div className="modal-content-card">
                <div className="modal-header">
                  <h3>Add Strategic Phase</h3>
                  <button onClick={() => setShowPhaseModal(false)} className="modal-close-btn"><X size={16} /></button>
                </div>
                <form onSubmit={handleCreatePhase} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div className="modal-form-group">
                    <label>Phase Title</label>
                    <input
                      type="text"
                      placeholder="e.g. Phase 4: Placement & Career Mastery"
                      value={phaseTitle}
                      onChange={(e) => setPhaseTitle(e.target.value)}
                      className="modal-input"
                      required
                    />
                  </div>
                  <div className="modal-form-group">
                    <label>Phase Description</label>
                    <input
                      type="text"
                      placeholder="e.g. Resume, mock interviews, and DSA preparation"
                      value={phaseDesc}
                      onChange={(e) => setPhaseDesc(e.target.value)}
                      className="modal-input"
                    />
                  </div>
                  <div className="modal-actions">
                    <button type="button" onClick={() => setShowPhaseModal(false)} className="btn-modal-cancel">Cancel</button>
                    <button type="submit" className="btn-modal-submit">Add Phase</button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Modal: Add Milestone */}
          {showMilestoneModal && (
            <div className="modal-overlay">
              <div className="modal-content-card">
                <div className="modal-header">
                  <h3>Add Milestone Protocol</h3>
                  <button onClick={() => setShowMilestoneModal(false)} className="modal-close-btn"><X size={16} /></button>
                </div>
                <form onSubmit={handleCreateMilestone} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div className="modal-form-group">
                    <label>Milestone Title</label>
                    <input
                      type="text"
                      placeholder="e.g. Complete 50 LeetCode Hard Problems"
                      value={msTitle}
                      onChange={(e) => setMsTitle(e.target.value)}
                      className="modal-input"
                      required
                    />
                  </div>
                  <div className="modal-form-group">
                    <label>Description / Verification Criteria</label>
                    <input
                      type="text"
                      placeholder="e.g. Focus on Graphs, DP, and Trees"
                      value={msDesc}
                      onChange={(e) => setMsDesc(e.target.value)}
                      className="modal-input"
                    />
                  </div>
                  <div className="modal-form-group">
                    <label>Target Date</label>
                    <input
                      type="date"
                      value={msTargetDate}
                      onChange={(e) => setMsTargetDate(e.target.value)}
                      className="modal-input"
                    />
                  </div>
                  <div className="modal-actions">
                    <button type="button" onClick={() => setShowMilestoneModal(false)} className="btn-modal-cancel">Cancel</button>
                    <button type="submit" className="btn-modal-submit">Add Milestone</button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
  );
};

export default Blueprint;
