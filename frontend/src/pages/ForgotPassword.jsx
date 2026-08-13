import { useState } from 'react';
import { Link } from 'react-router-dom';
import { TriangleAlert, CheckCircle2 } from 'lucide-react';
import MKCLogo from '../components/MKCLogo';
import { forgotPassword } from '../services/api';
import './Login.css';
import './ForgotPassword.css';

export default function ForgotPassword() {
  const [identifier, setIdentifier] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [devToken, setDevToken] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setDevToken(null);

    if (!identifier.trim()) {
      setError('Please enter your email or @username.');
      return;
    }

    setLoading(true);
    try {
      const res = await forgotPassword(identifier.trim());
      setMessage(res.message || "If an account exists for this address, you'll receive password reset instructions.");
      if (res.dev_reset_token) {
        setDevToken(res.dev_reset_token);
      }
    } catch (err) {
      setError(err.message || 'Failed to request password reset.');
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
          <h1 className="login-title font-display">Reset Password</h1>
          <p className="login-subtitle">
            Enter your registered email address or @username to receive password recovery instructions.
          </p>
        </div>

        {error && <div className="login-error-alert"><TriangleAlert size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />{error}</div>}
        {message && <div className="login-success-alert"><CheckCircle2 size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />{message}</div>}

        {devToken && (
          <div className="dev-token-notice">
            <span className="dev-badge">Development Delivery</span>
            <p style={{ margin: '6px 0', fontSize: '12px', color: 'var(--text-secondary)' }}>
              Password reset link generated:
            </p>
            <Link
              to={`/reset-password?token=${devToken}`}
              className="dev-token-link"
              style={{ color: 'var(--cyan)', wordBreak: 'break-all', fontSize: '13px', fontWeight: '600' }}
            >
              /reset-password?token={devToken}
            </Link>
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="identifier">Email Address or @username</label>
            <input
              id="identifier"
              type="text"
              placeholder="e.g. alex@example.com or @alex_dev"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              disabled={loading}
              autoComplete="username"
            />
          </div>

          <button type="submit" className="login-submit-btn" disabled={loading}>
            {loading ? 'Processing...' : 'Send Reset Instructions'}
          </button>
        </form>

        <div className="login-footer" style={{ marginTop: '24px' }}>
          <p>
            Remembered your password? <Link to="/login" className="login-link">Sign In</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
