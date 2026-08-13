import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { TriangleAlert, CheckCircle2 } from 'lucide-react';
import MKCLogo from '../components/MKCLogo';
import { verifyEmail } from '../services/api';
import './Login.css';
import './ForgotPassword.css';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [token, setToken] = useState(() => searchParams.get('token') || '');
  const [loading, setLoading] = useState(() => Boolean(searchParams.get('token')));
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;
    const queryToken = searchParams.get('token');
    if (queryToken) {
      verifyEmail(queryToken)
        .then(() => {
          if (isMounted) setSuccess(true);
        })
        .catch((err) => {
          if (isMounted) setError(err.message || 'Email verification link is invalid or has expired.');
        })
        .finally(() => {
          if (isMounted) setLoading(false);
        });
    }
    return () => {
      isMounted = false;
    };
  }, [searchParams]);

  const handleManualSubmit = (e) => {
    e.preventDefault();
    if (!token.trim()) {
      setError('Please enter a verification token.');
      return;
    }
    setLoading(true);
    setError('');
    verifyEmail(token.trim())
      .then(() => setSuccess(true))
      .catch((err) => setError(err.message || 'Email verification link is invalid or has expired.'))
      .finally(() => setLoading(false));
  };

  return (
    <div className="login-page">
      <div className="login-container glass-panel">
        <div className="login-header">
          <div className="login-logo">
            <MKCLogo size={48} className="login-logo-svg" />
          </div>
          <h1 className="login-title font-display">Email Verification</h1>
          <p className="login-subtitle">
            Verify your email address to confirm your Mastery Key Coach identity.
          </p>
        </div>

        {error && <div className="login-error-alert"><TriangleAlert size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />{error}</div>}

        {success ? (
          <div style={{ textAlign: 'center', padding: '16px 0' }}>
            <div className="login-success-alert" style={{ marginBottom: '24px' }}>
              <CheckCircle2 size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />
              Your email address has been verified successfully!
            </div>
            <button
              className="login-submit-btn"
              onClick={() => navigate('/dashboard')}
              type="button"
            >
              Go to Dashboard
            </button>
          </div>
        ) : (
          <form onSubmit={handleManualSubmit} className="login-form">
            {!searchParams.get('token') && (
              <div className="form-group">
                <label htmlFor="verifToken">Verification Token</label>
                <input
                  id="verifToken"
                  type="text"
                  placeholder="Paste verification token here"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  disabled={loading}
                />
              </div>
            )}

            <button type="submit" className="login-submit-btn" disabled={loading}>
              {loading ? 'Verifying Email...' : 'Verify Email Address'}
            </button>
          </form>
        )}

        <div className="login-footer" style={{ marginTop: '24px' }}>
          <p>
            Back to <Link to="/dashboard" className="login-link">Dashboard</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
