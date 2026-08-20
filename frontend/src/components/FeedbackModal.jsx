import { useState, useEffect, useCallback } from 'react';
import { X, MessageSquare, Send, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { submitFeedback } from '../services/api';
import './FeedbackModal.css';

const CATEGORIES = [
  'Bug',
  'Feature Request',
  'UI/UX',
  'Performance',
  'Account/Login',
  'Community/Chat',
  'AI Coach',
  'Credential',
  'Other'
];

const SEVERITIES = [
  { label: 'Low (Cosmetic / Suggestion)', value: 'Low' },
  { label: 'Normal (Standard Feedback)', value: 'Normal' },
  { label: 'High (Impacts Workflow)', value: 'High' },
  { label: 'Critical (Broken / Blocker)', value: 'Critical' }
];

export default function FeedbackModal({ isOpen, onClose }) {
  const [category, setCategory] = useState('Bug');
  const [severity, setSeverity] = useState('Normal');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const handleClose = useCallback(() => {
    if (loading) return;
    setCategory('Bug');
    setSeverity('Normal');
    setMessage('');
    setError(null);
    setSuccess(false);
    onClose();
  }, [loading, onClose]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen && !loading) handleClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, loading, handleClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim() || message.trim().length < 3) {
      setError('Please provide a message with at least 3 characters.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await submitFeedback({
        category,
        severity,
        message: message.trim(),
        page_url: window.location.pathname + window.location.search
      });
      setSuccess(true);
      setTimeout(() => {
        handleClose();
      }, 2000);
    } catch (err) {
      setError(err.message || 'Failed to submit feedback. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="feedback-modal-backdrop" onClick={handleClose} role="dialog" aria-modal="true">
      <div className="feedback-modal-card glass-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="feedback-modal-header">
          <div className="feedback-header-title">
            <div className="feedback-icon-badge">
              <MessageSquare size={20} style={{ color: '#38BDF8' }} />
            </div>
            <div>
              <h3>Submit Feedback</h3>
              <p className="feedback-header-sub">Help us improve Mastery Key Coach. Your input is private to the team.</p>
            </div>
          </div>
          <button 
            className="feedback-close-btn" 
            onClick={handleClose} 
            disabled={loading}
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Success State */}
        {success ? (
          <div className="feedback-success-state">
            <CheckCircle2 size={48} className="feedback-success-icon" />
            <h4>Thank You!</h4>
            <p>Your feedback has been securely received by our team.</p>
          </div>
        ) : (
          /* Feedback Form */
          <form className="feedback-form" onSubmit={handleSubmit}>
            {error && (
              <div className="feedback-error-banner">
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <div className="feedback-field-group">
              <label htmlFor="fb-category">Category</label>
              <select
                id="fb-category"
                className="feedback-select"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                disabled={loading}
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            <div className="feedback-field-group">
              <label htmlFor="fb-severity">Severity / Priority</label>
              <select
                id="fb-severity"
                className="feedback-select"
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                disabled={loading}
              >
                {SEVERITIES.map((sev) => (
                  <option key={sev.value} value={sev.value}>
                    {sev.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="feedback-field-group">
              <label htmlFor="fb-message">
                Message <span className="char-count">({message.length}/5000)</span>
              </label>
              <textarea
                id="fb-message"
                className="feedback-textarea"
                rows={5}
                placeholder="Tell us what happened, report a bug, or suggest a new feature or improvement..."
                value={message}
                maxLength={5000}
                onChange={(e) => setMessage(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            <div className="feedback-modal-footer">
              <button
                type="button"
                className="feedback-cancel-btn"
                onClick={onClose}
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="feedback-submit-btn"
                disabled={loading || message.trim().length < 3}
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Submitting...</span>
                  </>
                ) : (
                  <>
                    <Send size={16} />
                    <span>Submit Feedback</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
