import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { TriangleAlert, CheckCircle2, Pencil, Flame, Zap, Target, Shield, Globe, X, Award, Sparkles } from 'lucide-react';
import VictoryCredentialCard from '../components/VictoryCredentialCard';
import CertificateModal from '../components/CertificateModal';
import { getUser, updateUser, getProgression, getCredentials, getVerifiedCredential } from '../services/api';
import './Profile.css';

const Profile = () => {
  const [searchParams] = useSearchParams();
  const [user, setUser] = useState(null);
  const [progression, setProgression] = useState({ level: 1, rank: 'Initiate', total_xp: 0, next_level_xp: 100, progress_pct: 0 });
  const [credentials, setCredentials] = useState([]);
  const [selectedCert, setSelectedCert] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // Form edit states
  const [fullName, setFullName] = useState('');
  const [avatarInitials, setAvatarInitials] = useState('');
  const [bio, setBio] = useState('');

  const [saving, setSaving] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function loadProfileData() {
      try {
        const [u, prog, creds] = await Promise.all([
          getUser().catch(() => null),
          getProgression().catch(() => ({ level: 1, rank: 'Initiate', total_xp: 0, next_level_xp: 100, progress_pct: 0 })),
          getCredentials().catch(() => [])
        ]);

        if (isMounted) {
          if (u) {
            setUser(u);
            setFullName(u.full_name || '');
            setAvatarInitials(u.avatar_initials || 'MK');
            setBio(u.bio || '');
          }
          if (prog) setProgression(prog);
          const safeCreds = Array.isArray(creds) ? creds : [];
          setCredentials(safeCreds);

          const credParam = searchParams.get('cred');
          if (credParam) {
            const matching = safeCreds.find(c => String(c.id) === String(credParam) || c.slug === credParam);
            if (matching) {
              setSelectedCert(matching);
            } else {
              getVerifiedCredential(credParam).then(verified => {
                if (isMounted && verified) setSelectedCert(verified);
              }).catch((err) => {
                console.warn('Could not fetch verified credential by param:', err);
              });
            }
          }
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to load user profile:', err);
          setFeedbackMessage({ type: 'error', text: 'Could not load account profile.' });
          setLoading(false);
        }
      }
    }
    loadProfileData();

    const handleGlobalProgressUpdate = () => {
      loadProfileData();
    };
    window.addEventListener('mkc:progress-updated', handleGlobalProgressUpdate);

    return () => {
      isMounted = false;
      window.removeEventListener('mkc:progress-updated', handleGlobalProgressUpdate);
    };
  }, [searchParams]);

  const handleOpenEditModal = () => {
    if (user) {
      setFullName(user.full_name || '');
      setAvatarInitials(user.avatar_initials || 'MK');
      setBio(user.bio || '');
    }
    setFeedbackMessage(null);
    setIsEditModalOpen(true);
  };

  const handleSaveProfile = async (e) => {
    if (e) e.preventDefault();
    setSaving(true);
    setFeedbackMessage(null);

    try {
      const updated = await updateUser({
        full_name: fullName,
        avatar_initials: avatarInitials,
        bio
      });

      if (updated) {
        setUser(updated);
        setFullName(updated.full_name);
        setAvatarInitials(updated.avatar_initials);
        setBio(updated.bio);
      }

      setFeedbackMessage({ type: 'success', text: 'Profile identity updated successfully!' });
      setIsEditModalOpen(false);
    } catch (err) {
      console.error('Failed to update profile:', err);
      setFeedbackMessage({ type: 'error', text: err.message || 'Failed to update profile.' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="profile-container">
          {/* Header & Feedback */}
          {feedbackMessage && (
            <div style={{
              padding: '12px 16px',
              background: feedbackMessage.type === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(56, 189, 248, 0.1)',
              border: `1px solid ${feedbackMessage.type === 'error' ? '#EF4444' : 'var(--cyan)'}`,
              borderRadius: '12px',
              color: feedbackMessage.type === 'error' ? '#EF4444' : 'var(--cyan)',
              fontSize: '13px'
            }}>
              {feedbackMessage.type === 'error' ? (
                <TriangleAlert size={16} strokeWidth={1.8} style={{ color: '#EF4444' }} aria-hidden="true" />
              ) : (
                <CheckCircle2 size={16} strokeWidth={1.8} style={{ color: 'var(--cyan)' }} aria-hidden="true" />
              )} {feedbackMessage.text}
            </div>
          )}

          {loading ? (
            <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
              Loading Identity & Account Profile...
            </div>
          ) : (
            <>
              {/* 1. Identity Hero Section */}
              <div className="profile-hero-card glass-panel">
                <div className="profile-hero-left">
                  <div className="profile-avatar-circle font-display">
                    {user?.avatar_initials || 'MK'}
                  </div>
                </div>
                <div className="profile-hero-info">
                  <div className="profile-name-row">
                    <h1 className="font-serif">{user?.full_name || 'Mohith'}</h1>
                    <span className="profile-mkc-badge font-display">
                      @{user?.username || 'mohith_ai'}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
                      ({user?.mkc_id || 'MKC-2026-8F4A2C'})
                    </span>
                  </div>
                  <div className="profile-member-since">
                    Member Since {user?.member_since || 'August 2026'} • Level {progression.level || 1} {progression.rank || 'Initiate'}
                  </div>
                  <div className="profile-bio">
                    {user?.bio || 'AI Engineering & Full-Stack Systems Mastery'}
                  </div>
                </div>
                <button onClick={handleOpenEditModal} className="btn-edit-profile" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                  <Pencil size={14} strokeWidth={1.8} aria-hidden="true" /> Edit Profile
                </button>
              </div>

              {/* 2. Performance Telemetry Grid */}
              <div className="profile-stats-grid">
                <div className="profile-stat-card glass-panel">
                  <div className="profile-stat-header">
                    <span className="profile-stat-label">Discipline Streak</span>
                    <span className="profile-stat-icon"><Flame size={18} strokeWidth={1.8} style={{ color: '#F97316' }} aria-hidden="true" /></span>
                  </div>
                  <div className="profile-stat-val">{user?.streak_days || 0} Days</div>
                  <div className="profile-stat-sub">Consecutive protocol execution</div>
                </div>

                <div className="profile-stat-card glass-panel">
                  <div className="profile-stat-header">
                    <span className="profile-stat-label">Total Mastery XP</span>
                    <span className="profile-stat-icon"><Zap size={18} strokeWidth={1.8} style={{ color: '#FBBF24' }} aria-hidden="true" /></span>
                  </div>
                  <div className="profile-stat-val">{progression.total_xp ?? user?.xp_earned ?? 0} XP</div>
                  <div className="profile-stat-sub">Level {progression.level || 1} ({progression.progress_pct || 0}% progress)</div>
                </div>

                <div className="profile-stat-card glass-panel">
                  <div className="profile-stat-header">
                    <span className="profile-stat-label">Missions Completed</span>
                    <span className="profile-stat-icon"><CheckCircle2 size={18} strokeWidth={1.8} style={{ color: '#10B981' }} aria-hidden="true" /></span>
                  </div>
                  <div className="profile-stat-val">{user?.completed_missions || 0}</div>
                  <div className="profile-stat-sub">Daily protocols executed</div>
                </div>

                <div className="profile-stat-card glass-panel">
                  <div className="profile-stat-header">
                    <span className="profile-stat-label">Active Goals</span>
                    <span className="profile-stat-icon"><Target size={18} strokeWidth={1.8} style={{ color: '#38BDF8' }} aria-hidden="true" /></span>
                  </div>
                  <div className="profile-stat-val">{user?.active_goals || 0}</div>
                  <div className="profile-stat-sub">High-leverage targets</div>
                </div>
              </div>

              {/* 3. Mastery Credentials & Achievements Showcase */}
              <div className="profile-credentials-section glass-panel">
                <div className="profile-credentials-header">
                  <div className="credentials-header-left">
                    <div className="credentials-title-row">
                      <Award size={22} strokeWidth={2} style={{ color: 'var(--cyan)' }} />
                      <h2 className="font-serif">Mastery Credentials & Verified Achievements</h2>
                    </div>
                    <p className="credentials-subtitle">
                      Server-verified cryptographic credentials proving discipline, streak velocity, and protocol mastery.
                    </p>
                  </div>
                  <span className="credentials-count-pill font-display">
                    {credentials.length} Earned
                  </span>
                </div>

                {credentials.length === 0 ? (
                  <div className="credentials-empty-state">
                    <Sparkles size={32} style={{ opacity: 0.4, color: 'var(--cyan)', marginBottom: '8px' }} />
                    <h4>No Credentials Earned Yet</h4>
                    <p>Complete daily protocols, maintain streaks, and execute blueprints to earn verified achievements.</p>
                  </div>
                ) : (
                  <div className="credentials-gallery-grid">
                    {credentials.map(cred => (
                      <VictoryCredentialCard
                        key={cred.id || cred.slug}
                        credential={cred}
                        userName={user?.full_name || user?.username || 'Mastery Practitioner'}
                        onClick={() => setSelectedCert(cred)}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* 4. Profile Privacy Status Banner */}
              <div className="profile-privacy-banner glass-panel">
                <div className="profile-privacy-left">
                  <span className="profile-privacy-icon">
                    {user?.profile_visibility === 'private' ? (
                      <Shield size={20} strokeWidth={1.8} style={{ color: '#A78BFA' }} aria-hidden="true" />
                    ) : (
                      <Globe size={20} strokeWidth={1.8} style={{ color: 'var(--cyan)' }} aria-hidden="true" />
                    )}
                  </span>
                  <div>
                    <div className="profile-privacy-title">
                      Profile Privacy: {user?.profile_visibility === 'private' ? 'Private (Anonymous Member)' : 'Public (Community Visible)'}
                    </div>
                    <div className="profile-privacy-desc">
                      {user?.profile_visibility === 'private'
                        ? 'Your post & comment attributions display as "Anonymous Member" in the Community feed.'
                        : 'Your full name and identity are visible on public community posts and leaderboards.'}
                    </div>
                  </div>
                </div>
                <Link to="/settings" className="profile-privacy-btn">
                  Manage in Settings →
                </Link>
              </div>

              {/* Certificate Modal */}
              {selectedCert && (
                <CertificateModal
                  credential={selectedCert}
                  user={user}
                  onClose={() => setSelectedCert(null)}
                />
              )}

              {/* 4. Edit Profile Modal */}
              {isEditModalOpen && (
                <div className="modal-backdrop">
                  <div className="modal-card">
                    <div className="modal-header">
                      <h2>Edit Account Profile</h2>
                      <button onClick={() => setIsEditModalOpen(false)} className="modal-close-btn">
                        <X size={16} />
                      </button>
                    </div>

                    <form onSubmit={handleSaveProfile} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      <div className="modal-field">
                        <label className="modal-label">MKC Unique Identifier (Permanent)</label>
                        <input
                          type="text"
                          value={user?.mkc_id || 'MKC-2026-8F4A2C'}
                          disabled
                          className="modal-input"
                          style={{ opacity: 0.6, cursor: 'not-allowed', color: 'var(--cyan)' }}
                        />
                      </div>

                      <div className="modal-field">
                        <label className="modal-label">Display Name</label>
                        <input
                          type="text"
                          value={fullName}
                          onChange={(e) => setFullName(e.target.value)}
                          placeholder="e.g. Mohith K"
                          className="modal-input"
                          required
                        />
                      </div>

                      <div className="modal-field">
                        <label className="modal-label">Avatar Initials (Max 4 chars)</label>
                        <input
                          type="text"
                          value={avatarInitials}
                          onChange={(e) => setAvatarInitials(e.target.value.toUpperCase())}
                          placeholder="e.g. MK"
                          maxLength={4}
                          className="modal-input"
                          required
                        />
                      </div>

                      <div className="modal-field">
                        <label className="modal-label">Bio / Focus Statement</label>
                        <textarea
                          value={bio}
                          onChange={(e) => setBio(e.target.value)}
                          placeholder="Short summary of your engineering or growth focus..."
                          className="modal-textarea"
                          maxLength={500}
                        />
                      </div>

                      <div className="modal-footer">
                        <button
                          type="button"
                          onClick={() => setIsEditModalOpen(false)}
                          className="btn-modal-cancel"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={saving}
                          className="btn-modal-save"
                        >
                          {saving ? 'Saving...' : 'Save Profile'}
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
  );
};

export default Profile;
