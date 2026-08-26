import { useState, useEffect, useRef } from 'react';
import { Bot, User, Trash2, TriangleAlert } from 'lucide-react';
import { sendCoachMessage, getCoachHistory, clearCoachHistory } from '../services/api';
import './AICoach.css';

const SUGGESTIONS = [
  'What should I focus on today?',
  'Analyze my current progress',
  'Give me a mindset reset',
  'How do I build consistency?',
  'Help me set a stretch goal',
];

const AICoach = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Load persisted conversation history on mount
  useEffect(() => {
    let isMounted = true;
    async function loadHistory() {
      try {
        const data = await getCoachHistory(50);
        if (isMounted && data && Array.isArray(data.messages) && data.messages.length > 0) {
          setMessages(data.messages.map((m) => ({
            sender: m.sender,
            text: m.content,
            time: m.created_at || null,
          })));
        }
      } catch (err) {
        if (isMounted) {
          console.warn('Could not load chat history:', err.message);
          setError('Historical chat sync unavailable. Live coach is ready.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadHistory();
    return () => { isMounted = false; };
  }, []);

  // Auto-scroll when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]);

  const handleSend = async (text) => {
    const userText = (text || input).trim();
    if (!userText || sending) return;

    setMessages((prev) => [...prev, { sender: 'user', text: userText, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }]);
    setInput('');
    setSending(true);
    setError(null);

    try {
      const data = await sendCoachMessage(userText);
      const reply = data.reply || "I'm having trouble connecting to my AI brain right now. Give me another try in a moment.";
      setMessages((prev) => [...prev, { sender: 'coach', text: reply, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }]);
    } catch (err) {
      console.error('AI Coach error:', err);
      setError('Failed to get a response. Please try again.');
      setMessages((prev) => [...prev, {
        sender: 'coach',
        text: "I'm having trouble connecting to my AI brain right now. Give me another try in a moment.",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSend();
  };

  const handleSuggestionClick = (suggestion) => {
    handleSend(suggestion);
  };

  const handleClearHistory = async () => {
    if (!window.confirm('Clear your entire coaching conversation history?')) return;
    try {
      await clearCoachHistory();
      setMessages([]);
      setError(null);
    } catch (err) {
      console.error('Clear history failed:', err);
      setError('Failed to clear chat history.');
    }
  };

  return (
    <div className="coach-page-container">
          {/* Header */}
          <div className="coach-page-header">
            <div className="coach-page-header-left">
              <h1 className="font-serif">AI Coach</h1>
              <p>Your elite personal growth mentor — ask anything, get disciplined guidance.</p>
            </div>
            <div className="coach-page-header-right">
              <div className="coach-page-status">
                <span className="coach-page-status-dot online" />
                <span className="coach-page-status-text">
                  {sending ? 'Analyzing...' : 'Online & Ready'}
                </span>
              </div>
              <span className="coach-page-model-badge">Neural v4.2</span>
              {messages.length > 0 && (
                <button onClick={handleClearHistory} className="coach-page-clear-btn" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Trash2 size={14} strokeWidth={1.8} aria-hidden="true" /> Clear History
                </button>
              )}
            </div>
          </div>

          {error && (
            <div className="coach-page-error" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <TriangleAlert size={16} strokeWidth={1.8} style={{ color: '#EF4444' }} aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          {/* Chat Messages Area */}
          <div className="coach-chat-area">
            {loading ? (
              <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
                Loading conversation history...
              </div>
            ) : messages.length === 0 ? (
              <div className="coach-empty-state">
                <div className="coach-empty-icon" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Bot size={40} strokeWidth={1.8} style={{ color: 'var(--cyan)', filter: 'drop-shadow(0 0 10px rgba(56, 189, 248, 0.4))' }} aria-hidden="true" />
                </div>
                <h3>Start Your Coaching Session</h3>
                <p>Ask your AI Coach anything — from daily focus priorities and goal strategy to mindset resets and progress analysis.</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`coach-msg from-${msg.sender}`}>
                  <div className="coach-msg-avatar">
                    {msg.sender === 'coach' ? (
                      <Bot size={20} strokeWidth={1.8} style={{ color: 'var(--cyan)' }} aria-hidden="true" />
                    ) : (
                      <User size={20} strokeWidth={1.8} style={{ color: 'var(--text-primary)' }} aria-hidden="true" />
                    )}
                  </div>
                  <div>
                    <div className="coach-msg-bubble">{msg.text}</div>
                    {msg.time && <div className="coach-msg-time">{msg.time}</div>}
                  </div>
                </div>
              ))
            )}

            {/* Typing indicator */}
            {sending && (
              <div className="coach-typing-indicator">
                <div className="coach-msg-avatar" style={{
                  width: 36, height: 36, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: 'linear-gradient(135deg, rgba(56,189,248,0.15), rgba(59,130,246,0.15))',
                  border: '1px solid rgba(56,189,248,0.3)', flexShrink: 0
                }}>
                  <Bot size={20} strokeWidth={1.8} style={{ color: 'var(--cyan)' }} aria-hidden="true" />
                </div>
                <div className="coach-typing-dots">
                  <span /><span /><span />
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Input Bar */}
          <form onSubmit={handleSubmit} className="coach-input-bar">
            <input
              ref={inputRef}
              type="text"
              placeholder="Ask your AI Coach anything..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={sending}
              className="coach-page-input"
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="coach-page-send-btn"
            >
              {sending ? 'Analyzing...' : 'Send →'}
            </button>
          </form>

          {/* Quick Suggestion Chips */}
          <div className="coach-suggestions-bar">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => handleSuggestionClick(s)}
                disabled={sending}
                className="coach-suggestion-chip"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
  );
};

export default AICoach;
