import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { TriangleAlert, CheckCircle2 } from 'lucide-react';
import MKCLogo from '../components/MKCLogo';
import { resetPassword } from '../services/api';
import './Login.css';
import './ForgotPassword.css';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [token, setToken] = useState(() => searchParams.get('token') || '');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const computeStrength = (pwd) => {
    if (!pwd) return { label: 'None', pct: 0, color: 'var(--text-muted)' };
    if (pwd.length < 8) return { label: 'Too Short', pct: 20, color: '#ef4444' };
    
    let score = 0;
    if (pwd.length >= 8) score += 30;
    if (pwd.length >= 12) score += 20;
    if (/[A-Z]/.test(pwd)) score += 15;
    if (/[0-9]/.test(pwd)) score += 15;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 20;

    if (score < 50) return { label: 'Weak', pct: 40, color: '#f59e0b' };
    if (score < 80) return { label: 'Medium', pct: 75, color: '#38bdf8' };
    return { label: 'Strong', pct: 100, color: '#10b981' };
  };

  const strength = computeStrength(newPassword);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!token.trim()) {
      setError('Password reset token is required.');
      return;
    }
    if (newPassword.length < 8) {
      setError('New password must contain at least 8 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match. Please verify your entry.');
      return;
    }

    setLoading(true);
    try {
      await resetPassword(token.trim(), newPassword);
      setSuccess(true);
    } catch (err) {
      setError(err.message || 'Failed to update password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container glass-panel">
        <div className="login-header">
          <div className="login-logo">
            <MKCLogo size={48} className="login-logo-svg" />
          </div>
          <h1 className="login-title font-display">Set New Password</h1>
          <p className="login-subtitle">
            Enter your new password to restore secure account access.
          </p>
        </div>

        {error && <div className="login-error-alert"><TriangleAlert size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />{error}</div>}

        {success ? (
          <div style={{ textAlign: 'center', padding: '16px 0' }}>
            <div className="login-success-alert" style={{ marginBottom: '24px' }}>
              <CheckCircle2 size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />
              Password updated successfully. All existing active sessions on other devices have been logged out for security.
            </div>
            <button
              className="login-submit-btn"
              onClick={() => navigate('/login')}
              type="button"
            >
              Sign In with New Password
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="login-form">
            {!searchParams.get('token') && (
              <div className="form-group">
                <label htmlFor="token">Reset Token</label>
                <input
                  id="token"
                  type="text"
                  placeholder="Paste your reset token here"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  disabled={loading}
                />
              </div>
            )}

            <div className="form-group">
              <label htmlFor="newPassword">New Password</label>
              <input
                id="newPassword"
                type="password"
                placeholder="At least 8 characters"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                disabled={loading}
                autoComplete="new-password"
              />
              {newPassword && (
                <div style={{ marginTop: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px', color: strength.color }}>
                    <span>Password Strength</span>
                    <span style={{ fontWeight: '700' }}>{strength.label}</span>
                  </div>
                  <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                    <div style={{ width: `${strength.pct}%`, height: '100%', background: strength.color, transition: 'all 0.3s ease' }} />
                  </div>
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm New Password</label>
              <input
                id="confirmPassword"
                type="password"
                placeholder="Re-enter new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={loading}
                autoComplete="new-password"
              />
            </div>

            <button type="submit" className="login-submit-btn" disabled={loading}>
              {loading ? 'Updating Password...' : 'Reset Password'}
            </button>
          </form>
        )}

        <div className="login-footer" style={{ marginTop: '24px' }}>
          <p>
            Back to <Link to="/login" className="login-link">Sign In</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
