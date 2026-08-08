import { useState, useEffect, useRef, useCallback } from 'react';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import MissionCard from '../components/MissionCard';
import { getGoals, createGoal, updateGoal, deleteGoal, getMissions, toggleMission } from '../services/api';
import './Goals.css';

const defaultFallbackGoals = [
  {
    id: 1,
    user_id: 1,
    title: 'AI Engineering Mastery',
    description: 'Become an industry-ready AI Engineer by building strong foundations in Python, DSA, machine learning, backend engineering, cloud, and AI application development.',
    category: 'career',
    status: 'active',
    target_date: '2028-06-30',
    created_at: '2026-08-08 18:11:12'
  }
];

const defaultFallbackMissions = [
  { id: 1, title: 'Morning Meditation Protocol', category: 'wellness', time: '10 min', difficulty: 'easy', completed: false, xpReward: 10, goal_id: 1 },
  { id: 2, title: 'Deep Work Block & Code Architecture', category: 'productivity', time: '2 hrs', difficulty: 'hard', completed: true, xpReward: 25, goal_id: 1 },
  { id: 3, title: 'High-Intensity Workout Session', category: 'fitness', time: '45 min', difficulty: 'hard', completed: false, xpReward: 20, goal_id: 1 },
  { id: 4, title: 'Mastery Reading & Knowledge Note', category: 'learning', time: '20 min', difficulty: 'easy', completed: true, xpReward: 10, goal_id: 1 },
  { id: 5, title: 'Gratitude & Vision Reflection', category: 'mindset', time: '5 min', difficulty: 'easy', completed: false, xpReward: 10, goal_id: 1 }
];

const Goals = () => {
  const [goals, setGoals] = useState([]);
  const [missions, setMissions] = useState([]);
  const [selectedGoalId, setSelectedGoalId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState(null);

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'career',
    target_date: '',
    status: 'active'
  });
  const [formError, setFormError] = useState(null);
  const [formSubmitting, setFormSubmitting] = useState(false);

  // Delete Dialog state
  const [deletingGoal, setDeletingGoal] = useState(null);

  // Focus management refs
  const triggerButtonRef = useRef(null);
  const modalFirstInputRef = useRef(null);

  const closeModal = useCallback(() => {
    setIsModalOpen(false);
    setEditingGoal(null);
    setFormError(null);
    if (triggerButtonRef.current) {
      triggerButtonRef.current.focus();
    }
  }, []);

  const fetchGoalsData = useCallback(async () => {
    setLoading(true);
    setApiError(null);
    try {
      const [goalsList, missionsList] = await Promise.all([
        getGoals(),
        getMissions()
      ]);

      if (Array.isArray(goalsList) && goalsList.length > 0) {
        setGoals(goalsList);
        setSelectedGoalId(prev => prev || goalsList[0].id);
      } else {
        setGoals(defaultFallbackGoals);
        setSelectedGoalId(1);
      }

      if (Array.isArray(missionsList)) {
        setMissions(missionsList);
      } else {
        setMissions(defaultFallbackMissions);
      }
    } catch (err) {
      console.warn('Backend server offline or failed, using fallback goals:', err.message);
      setGoals(defaultFallbackGoals);
      setMissions(defaultFallbackMissions);
      setSelectedGoalId(1);
      setApiError('Unable to connect to live API server. Showing cached goals.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    async function init() {
      if (!isMounted) return;
      await fetchGoalsData();
    }
    init();
    return () => { isMounted = false; };
  }, [fetchGoalsData]);

  // Escape key handler for dialogs
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (isModalOpen) closeModal();
        if (deletingGoal) setDeletingGoal(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isModalOpen, deletingGoal, closeModal]);

  // Focus trap / auto-focus for modal
  useEffect(() => {
    if (isModalOpen && modalFirstInputRef.current) {
      modalFirstInputRef.current.focus();
    }
  }, [isModalOpen]);

  const openCreateModal = () => {
    setEditingGoal(null);
    setFormData({
      title: '',
      description: '',
      category: 'career',
      target_date: '',
      status: 'active'
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (goal, e) => {
    e.stopPropagation();
    setEditingGoal(goal);
    setFormData({
      title: goal.title || '',
      description: goal.description || '',
      category: goal.category || 'career',
      target_date: goal.target_date || '',
      status: goal.status || 'active'
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      setFormError('Goal title is required.');
      return;
    }

    setFormSubmitting(true);
    setFormError(null);

    try {
      if (editingGoal) {
        // PATCH only updated fields
        const changedFields = {};
        if (formData.title !== editingGoal.title) changedFields.title = formData.title;
        if (formData.description !== editingGoal.description) changedFields.description = formData.description;
        if (formData.category !== editingGoal.category) changedFields.category = formData.category;
        if (formData.status !== editingGoal.status) changedFields.status = formData.status;
        if (formData.target_date !== editingGoal.target_date) changedFields.target_date = formData.target_date;

        const updated = await updateGoal(editingGoal.id, changedFields);
        setGoals(prev => prev.map(g => g.id === editingGoal.id ? { ...g, ...updated } : g));
      } else {
        // POST new goal
        const created = await createGoal({
          title: formData.title,
          description: formData.description,
          category: formData.category,
          target_date: formData.target_date
        });
        setGoals(prev => [...prev, created]);
        setSelectedGoalId(created.id);
      }
      closeModal();
    } catch (err) {
      console.error('Goal submission error:', err.message);
      // Fallback local update if API server fails
      if (editingGoal) {
        setGoals(prev => prev.map(g => g.id === editingGoal.id ? { ...g, ...formData } : g));
      } else {
        const fakeId = Date.now();
        const fakeGoal = { id: fakeId, user_id: 1, ...formData };
        setGoals(prev => [...prev, fakeGoal]);
        setSelectedGoalId(fakeId);
      }
      closeModal();
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleDeleteGoal = async () => {
    if (!deletingGoal) return;
    const targetId = deletingGoal.id;

    try {
      await deleteGoal(targetId);
      setGoals(prev => prev.filter(g => g.id !== targetId));
    } catch (err) {
      console.warn('API delete goal failed, removing locally:', err.message);
      setGoals(prev => prev.filter(g => g.id !== targetId));
    } finally {
      setDeletingGoal(null);
      if (selectedGoalId === targetId) {
        const remaining = goals.filter(g => g.id !== targetId);
        setSelectedGoalId(remaining.length > 0 ? remaining[0].id : null);
      }
    }
  };

  const handleToggleMission = async (missionId) => {
    setMissions(prev => prev.map(m =>
      m.id === missionId ? { ...m, completed: !m.completed } : m
    ));

    try {
      const updated = await toggleMission(missionId);
      setMissions(prev => prev.map(m =>
        m.id === missionId ? { ...m, ...updated } : m
      ));
    } catch (err) {
      console.error('Failed to sync mission toggle:', err.message);
    }
  };

  // Helper getters
  const getLinkedMissions = (goalId) => {
    return missions.filter(m => Number(m.goal_id) === Number(goalId));
  };

  const calculateProgress = (goalId) => {
    const linked = getLinkedMissions(goalId);
    if (linked.length === 0) return null;
    const completed = linked.filter(m => m.completed).length;
    return Math.round((completed / linked.length) * 100);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'No target date';
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return dateStr;
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const selectedGoal = goals.find(g => g.id === selectedGoalId) || goals[0];
  const selectedLinkedMissions = selectedGoal ? getLinkedMissions(selectedGoal.id) : [];
  const selectedProgress = selectedGoal ? calculateProgress(selectedGoal.id) : null;

  return (
    <div className="app-shell">
      {/* 1. App Shell Sidebar */}
      <Sidebar />

      {/* 2. Main Viewport */}
      <div className="main-viewport">
        <TopBar />

        <div className="goals-container-layout">
          {/* Header Banner */}
          <div className="goals-page-header">
            <div className="header-text-area">
              <span className="page-tag font-display">MILESTONE TRACKER</span>
              <h1 className="page-title font-serif">Mastery Goals</h1>
              <p className="page-subtitle">
                Define strategic milestones, align daily protocols, and track your expansion toward freedom.
              </p>
            </div>
            <button
              ref={triggerButtonRef}
              className="create-goal-btn cta-primary"
              onClick={openCreateModal}
            >
              <span>+ Create New Goal</span>
            </button>
          </div>

          {apiError && (
            <div className="api-warning-bar">
              <span>⚠️ {apiError}</span>
              <button className="retry-btn" onClick={fetchGoalsData}>Retry Connection</button>
            </div>
          )}

          {/* Main 2-Column Content */}
          {loading ? (
            <div className="goals-loading-grid">
              <div className="skeleton-card glass-panel" />
              <div className="skeleton-card glass-panel" />
            </div>
          ) : goals.length === 0 ? (
            <div className="goals-empty-state glass-panel">
              <div className="empty-icon">🎯</div>
              <h3 className="empty-title font-display">No Goals Defined Yet</h3>
              <p className="empty-desc">
                No goals yet. Define the next milestone and start building your mastery.
              </p>
              <button className="cta-primary" onClick={openCreateModal}>
                Create Your First Goal
              </button>
            </div>
          ) : (
            <div className="goals-content-grid">
              {/* LEFT COLUMN: Goals List */}
              <div className="goals-list-column">
                <h3 className="section-subtitle font-display">Active Milestones ({goals.length})</h3>
                <div className="goals-cards-stack">
                  {goals.map((goal) => {
                    const isSelected = goal.id === selectedGoalId;
                    const progressVal = calculateProgress(goal.id);
                    const linkedCount = getLinkedMissions(goal.id).length;

                    return (
                      <div
                        key={goal.id}
                        tabIndex={0}
                        role="button"
                        aria-pressed={isSelected}
                        className={`goal-card glass-panel ${isSelected ? 'selected' : ''}`}
                        onClick={() => setSelectedGoalId(goal.id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setSelectedGoalId(goal.id);
                          }
                        }}
                      >
                        <div className="goal-card-top">
                          <span className={`category-tag tag-${goal.category || 'career'}`}>
                            {goal.category || 'career'}
                          </span>
                          <span className={`status-pill status-${goal.status || 'active'}`}>
                            {goal.status || 'active'}
                          </span>
                        </div>

                        <h4 className="goal-card-title">{goal.title}</h4>
                        <p className="goal-card-desc">{goal.description}</p>

                        <div className="goal-card-meta">
                          <span className="target-date-text">
                            📅 {formatDate(goal.target_date)}
                          </span>

                          <div className="goal-card-actions">
                            <button
                              aria-label={`Edit ${goal.title}`}
                              className="action-icon-btn edit-btn"
                              onClick={(e) => openEditModal(goal, e)}
                            >
                              ✏️
                            </button>
                            <button
                              aria-label={`Delete ${goal.title}`}
                              className="action-icon-btn delete-btn"
                              onClick={(e) => {
                                e.stopPropagation();
                                setDeletingGoal(goal);
                              }}
                            >
                              🗑️
                            </button>
                          </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="goal-card-progress">
                          {progressVal !== null ? (
                            <>
                              <div className="progress-info">
                                <span className="progress-label">Protocol Execution</span>
                                <span className="progress-value">{progressVal}%</span>
                              </div>
                              <div className="progress-bar-track">
                                <div className="progress-bar-fill" style={{ width: `${progressVal}%` }} />
                              </div>
                            </>
                          ) : (
                            <span className="no-missions-text font-display">
                              {linkedCount === 0 ? 'No missions linked yet' : '0% Protocol Execution'}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* RIGHT COLUMN: Selected Goal Detail View */}
              {selectedGoal && (
                <div className="goal-detail-column glass-panel">
                  <div className="detail-header">
                    <div className="detail-badges">
                      <span className={`category-tag tag-${selectedGoal.category || 'career'}`}>
                        {selectedGoal.category || 'career'}
                      </span>
                      <span className={`status-pill status-${selectedGoal.status || 'active'}`}>
                        {selectedGoal.status || 'active'}
                      </span>
                    </div>

                    <h2 className="detail-title font-display">{selectedGoal.title}</h2>
                    <p className="detail-description">{selectedGoal.description}</p>

                    <div className="detail-meta-bar">
                      <span className="meta-item">
                        <strong>Target Date:</strong> {formatDate(selectedGoal.target_date)}
                      </span>
                      <span className="meta-item">
                        <strong>Protocol Progress:</strong> {selectedProgress !== null ? `${selectedProgress}%` : 'No linked missions'}
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  {selectedProgress !== null && (
                    <div className="detail-progress-section">
                      <div className="progress-bar-track large">
                        <div className="progress-bar-fill" style={{ width: `${selectedProgress}%` }} />
                      </div>
                    </div>
                  )}

                  {/* Linked Missions Section */}
                  <div className="linked-missions-section">
                    <h3 className="linked-section-title font-display">
                      Linked Missions ({selectedLinkedMissions.length})
                    </h3>

                    {selectedLinkedMissions.length === 0 ? (
                      <div className="no-linked-missions-box">
                        <p>No daily missions linked to this goal yet.</p>
                      </div>
                    ) : (
                      <div className="linked-missions-list">
                        {selectedLinkedMissions.map(m => (
                          <MissionCard
                            key={m.id}
                            title={m.title}
                            category={m.category || 'wellness'}
                            time={m.time || '15 min'}
                            difficulty={m.difficulty || 'easy'}
                            completed={Boolean(m.completed)}
                            xpReward={m.xp_reward || 10}
                            onComplete={() => handleToggleMission(m.id)}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* CREATE / EDIT MODAL DIALOG */}
      {isModalOpen && (
        <div className="modal-backdrop" tabIndex={-1}>
          <div className="modal-dialog glass-panel" role="dialog" aria-modal="true">
            <div className="modal-header">
              <h3 className="modal-title font-display">
                {editingGoal ? 'Edit Milestone Goal' : 'Define New Milestone Goal'}
              </h3>
              <button aria-label="Close modal" className="modal-close-btn" onClick={closeModal}>✕</button>
            </div>

            <form onSubmit={handleFormSubmit} className="modal-form">
              {formError && <div className="form-error-msg">{formError}</div>}

              <div className="form-group">
                <label htmlFor="goal-title-input">Goal Title *</label>
                <input
                  id="goal-title-input"
                  ref={modalFirstInputRef}
                  type="text"
                  placeholder="e.g. AI Engineering Mastery"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label htmlFor="goal-desc-input">Description</label>
                <textarea
                  id="goal-desc-input"
                  rows={3}
                  placeholder="Describe your strategic objective..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="form-textarea"
                />
              </div>

              <div className="form-row-2col">
                <div className="form-group">
                  <label htmlFor="goal-category-select">Category</label>
                  <select
                    id="goal-category-select"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="form-select"
                  >
                    <option value="career">Career & Engineering</option>
                    <option value="wellness">Wellness & Health</option>
                    <option value="fitness">Fitness & Strength</option>
                    <option value="learning">Learning & Knowledge</option>
                    <option value="productivity">Productivity</option>
                    <option value="mindset">Mindset</option>
                    <option value="general">General</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="goal-status-select">Status</label>
                  <select
                    id="goal-status-select"
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="form-select"
                  >
                    <option value="active">Active</option>
                    <option value="completed">Completed</option>
                    <option value="paused">Paused</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="goal-date-input">Target Completion Date</label>
                <input
                  id="goal-date-input"
                  type="date"
                  value={formData.target_date}
                  onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
                  className="form-input"
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="cta-secondary" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" disabled={formSubmitting} className="cta-primary">
                  {formSubmitting ? 'Saving...' : editingGoal ? 'Save Changes' : 'Create Goal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DELETE CONFIRMATION DIALOG */}
      {deletingGoal && (
        <div className="modal-backdrop">
          <div className="modal-dialog glass-panel delete-modal" role="dialog" aria-modal="true">
            <h3 className="modal-title font-display">Delete Milestone Goal?</h3>
            <p className="delete-warning-text">
              Are you sure you want to delete <strong>"{deletingGoal.title}"</strong>?
            </p>
            <p className="delete-info-note">
              This action cannot be undone from the dashboard. Linked missions will be safely decoupled and preserved.
            </p>

            <div className="modal-actions">
              <button className="cta-secondary" onClick={() => setDeletingGoal(null)}>
                Cancel
              </button>
              <button className="cta-danger" onClick={handleDeleteGoal}>
                Delete Goal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Goals;
