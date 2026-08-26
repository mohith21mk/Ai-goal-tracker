import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  X, 
  UserPlus, 
  UserCheck,
  Check, 
  MessageCircle, 
  Flame, 
  Zap, 
  CheckCircle2, 
  ShieldAlert, 
  Clock, 
  CheckCheck,
  TriangleAlert,
  Award
} from 'lucide-react';
import { 
  getPublicUserProfile,
  getPublicCredentials,
  getFollowStats,
  followUser,
  unfollowUser,
  requestConnection, 
  acceptConnection, 
  rejectConnection 
} from '../services/api';
import VictoryCredentialCard from './VictoryCredentialCard';
import './UserProfilePanel.css';

export default function UserProfilePanel({ 
  userId, 
  onClose, 
  onStartConversation, 
  onConnectionUpdated 
}) {
  const [profile, setProfile] = useState(null);
  const [credentials, setCredentials] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('none');
  const [followStats, setFollowStats] = useState({ followers_count: 0, following_count: 0, is_following: false });
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const toastTimerRef = useRef(null);
  const isMountedRef = useRef(true);

  const showToast = (type, text) => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    if (isMountedRef.current) {
      setToast({ type, text });
    }
    toastTimerRef.current = setTimeout(() => {
      if (isMountedRef.current) {
        setToast(null);
      }
    }, 4000);
  };

  const refreshProfile = useCallback(async () => {
    if (!userId) return;
    try {
      const [data, creds, fStats] = await Promise.all([
        getPublicUserProfile(userId),
        getPublicCredentials(userId).catch(() => []),
        getFollowStats(userId).catch(() => ({ followers_count: 0, following_count: 0, is_following: false }))
      ]);
      if (isMountedRef.current) {
        setProfile(data);
        setCredentials(Array.isArray(creds) ? creds : []);
        setConnectionStatus(data.connection_status || 'none');
        setFollowStats(fStats);
      }
    } catch (err) {
      console.error('Failed to refresh user profile:', err);
    }
  }, [userId]);

  useEffect(() => {
    isMountedRef.current = true;
    async function loadData() {
      setLoading(true);
      try {
        const [data, creds, fStats] = await Promise.all([
          getPublicUserProfile(userId),
          getPublicCredentials(userId).catch(() => []),
          getFollowStats(userId).catch(() => ({ followers_count: 0, following_count: 0, is_following: false }))
        ]);
        if (isMountedRef.current) {
          setProfile(data);
          setCredentials(Array.isArray(creds) ? creds : []);
          setConnectionStatus(data.connection_status || 'none');
          setFollowStats(fStats);
          setLoading(false);
        }
      } catch (err) {
        if (isMountedRef.current) {
          console.error('Failed to load user profile modal:', err);
          setLoading(false);
        }
      }
    }

    if (userId) {
      loadData();
    }

    return () => {
      isMountedRef.current = false;
      if (toastTimerRef.current) {
        clearTimeout(toastTimerRef.current);
      }
    };
  }, [userId]);

  const handleToggleFollow = async () => {
    if (!userId || followLoading) return;
    setFollowLoading(true);
    try {
      if (followStats.is_following) {
        await unfollowUser(userId);
        setFollowStats(prev => ({
          ...prev,
          is_following: false,
          followers_count: Math.max(0, prev.followers_count - 1)
        }));
        showToast('success', `Unfollowed @${profile?.username || 'user'}`);
      } else {
        await followUser(userId);
        setFollowStats(prev => ({
          ...prev,
          is_following: true,
          followers_count: prev.followers_count + 1
        }));
        showToast('success', `Now following @${profile?.username || 'user'}`);
      }
    } catch (err) {
      showToast('error', err.message || 'Failed to update follow status.');
    } finally {
      setFollowLoading(false);
    }
  };

  const handleConnect = async () => {
    setActionLoading(true);
    try {
      await requestConnection(userId);
      setConnectionStatus('sent');
      showToast('success', 'Connection request sent successfully.');
      refreshProfile();
      if (onConnectionUpdated) onConnectionUpdated();
    } catch (err) {
      showToast('error', err.message || 'Failed to send connection request.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAccept = async () => {
    setActionLoading(true);
    try {
      await acceptConnection(userId);
      setConnectionStatus('accepted');
      showToast('success', 'Connection accepted.');
      refreshProfile();
      if (onConnectionUpdated) onConnectionUpdated();
    } catch (err) {
      showToast('error', err.message || 'Failed to accept connection.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    setActionLoading(true);
    try {
      await rejectConnection(userId);
      setConnectionStatus('none');
      showToast('success', 'Connection request declined.');
      refreshProfile();
      if (onConnectionUpdated) onConnectionUpdated();
    } catch (err) {
      showToast('error', err.message || 'Failed to decline connection.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleMessage = () => {
    if (connectionStatus !== 'accepted') {
      showToast('error', 'You must be connected to message this user.');
      return;
    }
    if (onStartConversation) {
      onStartConversation(userId);
    }
  };

  const renderActionButton = () => {
    if (actionLoading) {
      return (
        <button className="user-profile-btn disabled" disabled>
          Processing...
        </button>
      );
    }

    switch (connectionStatus) {
      case 'none':
        return (
          <button 
            onClick={handleConnect} 
            className="user-profile-btn btn-primary"
          >
            <UserPlus size={16} strokeWidth={2} /> Send Connection Request
          </button>
        );

      case 'sent':
        return (
          <button className="user-profile-btn btn-secondary disabled" disabled>
            <Clock size={16} strokeWidth={2} /> Request Pending
          </button>
        );

      case 'received':
        return (
          <div className="user-profile-btn-group">
            <button 
              onClick={handleAccept} 
              className="user-profile-btn btn-success"
            >
              <Check size={16} strokeWidth={2} /> Accept Request
            </button>
            <button 
              onClick={handleReject} 
              className="user-profile-btn btn-danger"
            >
              <X size={16} strokeWidth={2} /> Decline
            </button>
          </div>
        );

      case 'accepted':
        return (
          <button 
            onClick={handleMessage} 
            className="user-profile-btn btn-primary"
          >
            <MessageCircle size={16} strokeWidth={2} /> Open Message Conversation
          </button>
        );

      case 'blocked':
        return (
          <button className="user-profile-btn btn-danger disabled" disabled>
            <ShieldAlert size={16} strokeWidth={2} /> User Blocked
          </button>
        );

      case 'self':
        return (
          <div className="user-profile-status-pill self">
            <span>Your Account Profile</span>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="user-profile-modal-backdrop" onClick={onClose}>
      <div 
        className="user-profile-modal-card glass-panel" 
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {/* Close Button */}
        <button 
          onClick={onClose} 
          className="user-profile-close-btn"
          aria-label="Close profile"
        >
          <X size={18} strokeWidth={2} />
        </button>

        {/* Toast Alert */}
        {toast && (
          <div className={`user-profile-toast toast-${toast.type}`}>
            {toast.type === 'error' ? (
              <TriangleAlert size={14} />
            ) : (
              <CheckCheck size={14} />
            )}
            <span>{toast.text}</span>
          </div>
        )}

        {loading ? (
          <div className="user-profile-loading">
            Syncing Profile Identity...
          </div>
        ) : !profile ? (
          <div className="user-profile-empty">
            User profile could not be loaded.
          </div>
        ) : (
          <div className="user-profile-body">
            {/* Top Identity Section */}
            <div className="user-profile-header">
              <div className="user-profile-avatar font-display">
                {profile.avatar_initials || (profile.username ? profile.username.substring(0, 2).toUpperCase() : 'MK')}
              </div>
              <div className="user-profile-info">
                <h3 className="user-profile-fullname font-serif">
                  {profile.full_name || profile.username}
                </h3>
                <div className="user-profile-tags">
                  <span className="user-profile-username font-display">
                    @{profile.username}
                  </span>
                  <span className="user-profile-mkcid">
                    {profile.mkc_id || `MKC-${profile.id}`}
                  </span>
                </div>
                
                {/* Followers / Following Stats Row */}
                <div className="user-profile-social-row">
                  <span><strong>{followStats.followers_count}</strong> Followers</span>
                  <span className="dot">•</span>
                  <span><strong>{followStats.following_count}</strong> Following</span>
                </div>

                {profile.member_since && (
                  <div className="user-profile-since">
                    Member Since {profile.member_since}
                  </div>
                )}
              </div>
            </div>

            {/* Bio Section */}
            {profile.bio && (
              <div className="user-profile-bio">
                <p>{profile.bio}</p>
              </div>
            )}

            {/* Performance Telemetry Grid */}
            <div className="user-profile-telemetry-grid">
              <div className="telemetry-pill">
                <Flame size={16} strokeWidth={1.8} className="icon-orange" />
                <div className="telemetry-data">
                  <span className="telemetry-val">{profile.streak_days || 0}d</span>
                  <span className="telemetry-lbl">Streak</span>
                </div>
              </div>

              <div className="telemetry-pill">
                <Zap size={16} strokeWidth={1.8} className="icon-gold" />
                <div className="telemetry-data">
                  <span className="telemetry-val">{profile.xp_earned || 0}</span>
                  <span className="telemetry-lbl">XP</span>
                </div>
              </div>

              <div className="telemetry-pill">
                <CheckCircle2 size={16} strokeWidth={1.8} className="icon-green" />
                <div className="telemetry-data">
                  <span className="telemetry-val">{profile.completed_missions || 0}</span>
                  <span className="telemetry-lbl">Protocols</span>
                </div>
              </div>
            </div>

            {/* Verified Credentials Chips Section */}
            {credentials.length > 0 && (
              <div className="user-profile-credentials-box">
                <div className="user-profile-credentials-header">
                  <Award size={13} style={{ color: 'var(--cyan)' }} />
                  <span>Verified Achievements ({credentials.length})</span>
                </div>
                <div className="user-profile-credentials-chips">
                  {credentials.slice(0, 5).map(cred => (
                    <VictoryCredentialCard
                      key={cred.id || cred.slug}
                      credential={cred}
                      compact={true}
                      interactive={false}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Connection Status & Action Section */}
            <div className="user-profile-actions-wrapper">
              <div className="connection-status-row">
                <span className="status-label">Network Status:</span>
                <span className={`status-indicator status-${connectionStatus}`}>
                  ● {connectionStatus === 'none' ? 'Not Connected' :
                     connectionStatus === 'sent' ? 'Request Sent' :
                     connectionStatus === 'received' ? 'Incoming Request' :
                     connectionStatus === 'accepted' ? 'Connected' :
                     connectionStatus === 'blocked' ? 'Blocked' : 'Active'}
                </span>
              </div>

              <div className="action-button-container">
                {/* Social Follow Toggle Button (if not viewing self) */}
                {connectionStatus !== 'self' && (
                  <button 
                    type="button" 
                    className={`user-profile-btn ${followStats.is_following ? 'btn-following' : 'btn-follow'}`}
                    onClick={handleToggleFollow}
                    disabled={followLoading}
                    style={{ marginBottom: '8px' }}
                  >
                    {followStats.is_following ? (
                      <><UserCheck size={16} strokeWidth={2} /> Following</>
                    ) : (
                      <><UserPlus size={16} strokeWidth={2} /> Follow @{profile.username}</>
                    )}
                  </button>
                )}

                {renderActionButton()}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
