import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, TriangleAlert } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import MKCLogo from '../components/MKCLogo';
import './Login.css';

const Login = () => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!identifier.trim() || !password) return;

    setSubmitting(true);
    setErrorMsg(null);

    try {
      await login(identifier, password);
      navigate('/dashboard');
    } catch (err) {
      console.error('Login error:', err);
      setErrorMsg(err.message || 'Invalid username/email or password.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page-container">
      <div className="auth-card">
        {/* Header */}
        <div className="auth-header">
          <div className="auth-brand-logo" style={{ background: 'none', border: 'none', boxShadow: 'none' }}>
            <MKCLogo size={48} className="login-logo-svg" />
          </div>
          <h1 className="font-serif">Welcome back</h1>
          <p>Your next level of discipline is waiting.</p>
        </div>

        {errorMsg && <div className="auth-error-banner"><TriangleAlert size={16} /> {errorMsg}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field-group">
            <input
              type="text"
              placeholder="Username or email (@mohith_ai)"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              className="auth-input"
              required
              autoFocus
            />
          </div>

          <div className="auth-field-group">
            <div className="auth-password-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="auth-input"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="auth-password-toggle"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting || !identifier.trim() || !password}
            className="btn-auth-primary"
          >
            {submitting ? 'Logging in...' : 'Log In'}
          </button>
        </form>

        <div className="auth-divider">OR</div>

        <div className="auth-footer-text">
          Don't have an MKC account?
          <Link to="/register" className="auth-link">
            Create account
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Login;
