import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, TriangleAlert, Check, X, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import MKCLogo from '../components/MKCLogo';
import './Login.css';
import './Register.css';

const Register = () => {
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Availability state
  const [availability, setAvailability] = useState(null); // { available: bool, reason: str }
  const [checkingUsername, setCheckingUsername] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [createdUser, setCreatedUser] = useState(null);

  const { register, checkUsernameAvailability } = useAuth();
  const navigate = useNavigate();

  // Debounced username availability check (300ms)
  useEffect(() => {
    const trimmed = username.trim();
    if (!trimmed) {
      const resetTimer = setTimeout(() => {
        setAvailability(null);
        setCheckingUsername(false);
      }, 0);
      return () => clearTimeout(resetTimer);
    }

    const timer = setTimeout(async () => {
      setCheckingUsername(true);
      try {
        const res = await checkUsernameAvailability(trimmed);
        setAvailability(res);
      } catch (err) {
        console.warn('Username check error:', err);
      } finally {
        setCheckingUsername(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [username, checkUsernameAvailability]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!fullName.trim() || !username.trim() || !email.trim() || !password) {
      setErrorMsg('Please fill in all required fields.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMsg('Passwords do not match.');
      return;
    }

    if (password.length < 8) {
      setErrorMsg('Password must contain at least 8 characters.');
      return;
    }

    if (availability && !availability.available) {
      setErrorMsg(availability.reason || `@${username.replace(/^@/, '')} is already taken.`);
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);

    try {
      const u = await register(fullName, username, email, password);
      setCreatedUser(u);
    } catch (err) {
      console.error('Registration error:', err);
      setErrorMsg(err.message || 'Registration failed. Please check your information.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEnterApp = () => {
    navigate('/dashboard');
  };

  return (
    <div className="auth-page-container">
      <div className="register-card">
        {createdUser ? (
          /* Onboarding Success Card */
          <div className="onboarding-card">
            <div className="onboarding-icon"><Sparkles size={28} /></div>
            <h1 className="onboarding-title font-serif">ACCOUNT CREATED</h1>
            <p className="onboarding-subtitle">
              Welcome to Mastery Key Coach, {createdUser.full_name}.
            </p>
            <div className="onboarding-identity-pill font-display">
              @{createdUser.username}
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Your identity, goals, and daily protocols are initialized.
            </p>
            <button onClick={handleEnterApp} className="btn-auth-primary" style={{ width: '100%' }}>
              [ ENTER MKC ]
            </button>
          </div>
        ) : (
          <>
            {/* Registration Form */}
            <div className="auth-header">
              <div className="auth-brand-logo" style={{ background: 'none', border: 'none', boxShadow: 'none' }}>
                <MKCLogo size={48} className="login-logo-svg" />
              </div>
              <h1 className="font-serif">Create your MKC account</h1>
              <p>Build your identity. Build your discipline. Build your future.</p>
            </div>

            {errorMsg && <div className="auth-error-banner"><TriangleAlert size={16} /> {errorMsg}</div>}

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="auth-field-group">
                <input
                  type="text"
                  placeholder="Full Name (e.g. Mohith K)"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="auth-input"
                  required
                />
              </div>

              <div className="auth-field-group">
                <input
                  type="text"
                  placeholder="MKC ID / Username (e.g. @mohith_ai)"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="auth-input"
                  required
                />
                {checkingUsername && (
                  <div className="username-feedback username-checking">Checking availability...</div>
                )}
                {!checkingUsername && availability && (
                  <div className={`username-feedback ${availability.available ? 'username-available' : 'username-taken'}`}>
                    {availability.available ? (
                      <><Check size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '4px' }} /> @{availability.username} is available</>
                    ) : (
                      <><X size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '4px' }} /> {availability.reason || `@${availability.username} is already taken`}</>
                    )}
                  </div>
                )}
              </div>

              <div className="auth-field-group">
                <input
                  type="email"
                  placeholder="Email address (user@example.com)"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="auth-input"
                  required
                />
              </div>

              <div className="auth-field-group">
                <div className="auth-password-wrapper">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Password (min. 8 characters)"
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

              <div className="auth-field-group">
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Confirm Password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="auth-input"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={submitting || (availability && !availability.available)}
                className="btn-auth-primary"
              >
                {submitting ? 'Creating Account...' : '[ CREATE ACCOUNT ]'}
              </button>
            </form>

            <div className="auth-footer-text">
              Already have an account?
              <Link to="/login" className="auth-link">
                Log in
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Register;
