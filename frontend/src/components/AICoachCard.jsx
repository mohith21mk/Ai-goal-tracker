import { useState, useEffect, useRef } from 'react';
import { sendCoachMessage, getCoachHistory, clearCoachHistory } from '../services/api';
import { Trash2, AlertTriangle, ArrowRight } from 'lucide-react';
import './AICoachCard.css';

const AICoachCard = ({
  message = "What's on your mind today? Let's take your next big goal step by step.",
  coachName = "AI Coach",
  isOnline = true
}) => {
  const [promptInput, setPromptInput] = useState('');
  const [chatLog, setChatLog] = useState([
    { sender: 'coach', text: message }
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const messageBoxRef = useRef(null);
  const userScrolledUpRef = useRef(false);

  const handleScroll = () => {
    if (!messageBoxRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = messageBoxRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 40;
    userScrolledUpRef.current = !isAtBottom;
  };

  useEffect(() => {
    if (messageBoxRef.current && !userScrolledUpRef.current) {
      messageBoxRef.current.scrollTop = messageBoxRef.current.scrollHeight;
    }
  }, [chatLog, isSubmitting]);

  // Load persisted conversation history on mount
  useEffect(() => {
    let isMounted = true;
    async function loadHistory() {
      try {
        const historyData = await getCoachHistory(50);
        if (isMounted) {
          if (historyData && Array.isArray(historyData.messages) && historyData.messages.length > 0) {
            const loadedLog = historyData.messages.map((m) => ({
              sender: m.sender,
              text: m.content
            }));
            setChatLog(loadedLog);
          }
          setErrorMessage(null);
        }
      } catch (err) {
        if (isMounted) {
          console.warn('Could not load chat history from database:', err.message);
          setErrorMessage('Historical chat sync unavailable. Live coach ready.');
        }
      }
    }
    loadHistory();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSendPrompt = async (e) => {
    e.preventDefault();
    const userText = promptInput.trim();
    if (!userText || isSubmitting) return;

    userScrolledUpRef.current = false;
    setChatLog((prev) => [...prev, { sender: 'user', text: userText }]);
    setPromptInput('');
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const responseData = await sendCoachMessage(userText);
      const coachReply = responseData.reply || "I'm having trouble connecting to my AI brain right now. Give me another try in a moment.";

      setChatLog((prev) => [
        ...prev,
        { sender: 'coach', text: coachReply }
      ]);
    } catch (err) {
      console.warn('AI Coach server API call failed:', err.message);
      setErrorMessage('Chat response failed to persist. Please try again.');
      setChatLog((prev) => [
        ...prev,
        {
          sender: 'coach',
          text: "I'm having trouble connecting to my AI brain right now. Give me another try in a moment."
        }
      ]);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await clearCoachHistory();
      setChatLog([{ sender: 'coach', text: message }]);
      setErrorMessage(null);
    } catch (err) {
      console.warn('Clear history failed:', err.message);
      setErrorMessage('Failed to clear chat history.');
    }
  };

  return (
    <div className="ai-coach-card glass-panel">
      {/* Card Header with Cyberpunk SVG Avatar & Pulsing Dot */}
      <div className="coach-card-header">
        <div className="avatar-section">
          <div className="ai-avatar-graphic">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="40" height="40" rx="12" fill="#071426" stroke="#38BDF8" strokeWidth="1.5" />
              {/* Cybernetic Helmet Mask */}
              <path d="M12 16C12 12.6863 14.6863 10 18 10H22C25.3137 10 28 12.6863 28 16V22C28 25.3137 25.3137 28 22 28H18C14.6863 28 12 25.3137 12 22V16Z" fill="url(#aiAvatarGrad)" />
              {/* Luminous Visor Line */}
              <rect x="15" y="16" width="10" height="3" rx="1.5" fill="#38BDF8" className="animate-pulse-glow" />
              <circle cx="20" cy="23" r="1.5" fill="#FBBF24" />
              <defs>
                <linearGradient id="aiAvatarGrad" x1="12" y1="10" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#3B82F6" stopOpacity="0.8" />
                  <stop offset="1" stopColor="#050B16" stopOpacity="0.9" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div className="coach-identity">
            <span className="coach-name font-display">{coachName}</span>
            <div className="coach-status">
              <span className={`status-dot ${isOnline ? 'online' : ''}`} />
              <span className="status-text">{isSubmitting ? 'Thinking...' : isOnline ? 'Online & Active' : 'Offline'}</span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {chatLog.length > 1 && (
            <button
              onClick={handleClearHistory}
              title="Clear chat history"
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-tertiary)',
                cursor: 'pointer',
                fontSize: '12px',
                padding: '2px 4px',
                transition: 'color 0.2s'
              }}
              onMouseOver={(e) => (e.target.style.color = '#FBBF24')}
              onMouseOut={(e) => (e.target.style.color = 'var(--text-tertiary)')}
            >
              <Trash2 size={14} strokeWidth={1.8} />
            </button>
          )}
          <span className="neural-badge">Neural v4.2</span>
        </div>
      </div>

      {errorMessage && (
        <div style={{ fontSize: '11px', color: '#FBBF24', padding: '4px 12px', background: 'rgba(251, 191, 36, 0.1)', borderRadius: '6px', margin: '4px 12px 0' }}>
          <AlertTriangle size={14} strokeWidth={1.8} style={{ display: 'inline-block', verticalAlign: 'middle', marginRight: '4px' }} /> {errorMessage}
        </div>
      )}

      {/* Chat / Message Display */}
      <div className="coach-message-box" ref={messageBoxRef} onScroll={handleScroll}>
        {chatLog.map((msg, index) => (
          <div key={index} className={`message-bubble ${msg.sender}`}>
            <p>{msg.text}</p>
          </div>
        ))}
        {isSubmitting && (
          <div className="message-bubble coach">
            <p style={{ fontStyle: 'italic', opacity: 0.8 }}>Formulating personalized advice...</p>
          </div>
        )}
      </div>

      {/* Quick Input Action */}
      <form onSubmit={handleSendPrompt} className="coach-input-form">
        <input
          type="text"
          placeholder="Ask AI Coach a question..."
          value={promptInput}
          onChange={(e) => setPromptInput(e.target.value)}
          disabled={isSubmitting}
          className="coach-input"
        />
        <button type="submit" disabled={isSubmitting || !promptInput.trim()} className="coach-send-btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
          <span>{isSubmitting ? 'Thinking...' : 'Continue Conversation'}</span>
          {!isSubmitting && <ArrowRight size={14} strokeWidth={2} aria-hidden="true" />}
        </button>
      </form>
    </div>
  );
};

export default AICoachCard;
