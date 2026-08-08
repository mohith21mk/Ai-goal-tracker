import { useState } from 'react';
import './AICoachCard.css';

const AICoachCard = ({
  message = "You're not just dreaming— you're building. Every step today creates a stronger tomorrow.",
  coachName = "AI Coach",
  isOnline = true
}) => {
  const [promptInput, setPromptInput] = useState('');
  const [chatLog, setChatLog] = useState([
    { sender: 'coach', text: message }
  ]);

  const handleSendPrompt = (e) => {
    e.preventDefault();
    if (!promptInput.trim()) return;

    const userText = promptInput;
    setChatLog((prev) => [...prev, { sender: 'user', text: userText }]);
    setPromptInput('');

    // Simulated instant AI coach response
    setTimeout(() => {
      setChatLog((prev) => [
        ...prev,
        {
          sender: 'coach',
          text: `Action locked in for "${userText}". Execute with total discipline today.`
        }
      ]);
    }, 600);
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
              <span className="status-text">{isOnline ? 'Online & Analyzing' : 'Offline'}</span>
            </div>
          </div>
        </div>

        <span className="neural-badge">Neural v4.2</span>
      </div>

      {/* Chat / Message Display */}
      <div className="coach-message-box">
        {chatLog.slice(-2).map((msg, index) => (
          <div key={index} className={`message-bubble ${msg.sender}`}>
            <p>{msg.text}</p>
          </div>
        ))}
      </div>

      {/* Quick Input Action */}
      <form onSubmit={handleSendPrompt} className="coach-input-form">
        <input
          type="text"
          placeholder="Ask AI Coach a question..."
          value={promptInput}
          onChange={(e) => setPromptInput(e.target.value)}
          className="coach-input"
        />
        <button type="submit" className="coach-send-btn">
          <span>Continue Conversation →</span>
        </button>
      </form>
    </div>
  );
};

export default AICoachCard;
