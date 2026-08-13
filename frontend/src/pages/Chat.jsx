import { useState, useEffect, useRef, useCallback } from 'react';
import { Search, UserPlus, Check, X, Send, MessageSquare, MessageCircle } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import { useMessagingSocket } from '../hooks/useMessagingSocket';
import {
  searchPublicUsers,
  getConnections,
  requestConnection,
  acceptConnection,
  rejectConnection,
  createConversation,
  getConversations,
  getConversationMessages,
  markConversationRead,
  getCurrentUser
} from '../services/api';
import './Chat.css';

const Chat = () => {
  const [currentUser, setCurrentUser] = useState(null);
  
  // Left Panel State
  const [activeTab, setActiveTab] = useState('conversations'); // 'conversations' | 'discover' | 'requests'
  const [conversations, setConversations] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [connections, setConnections] = useState({ accepted: [], pending_received: [], pending_sent: [], blocked: [] });
  
  // Right Panel State
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const messagesEndRef = useRef(null);

  const loadConversations = useCallback(async () => {
    try {
      const data = await getConversations();
      setConversations(data);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const loadConnections = useCallback(async () => {
    try {
      const data = await getConnections();
      setConnections(data);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const scrollToBottom = () => {
    setTimeout(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);
  };

  const activeConvRef = useRef(activeConversation);
  useEffect(() => {
    activeConvRef.current = activeConversation;
  }, [activeConversation]);

  // Real-time WebSocket event handler
  const handleIncomingMessage = useCallback((eventData) => {
    const msgObj = eventData.message || eventData;
    const targetConvId = eventData.conversation_id || msgObj.conversation_id;
    const currentActiveConv = activeConvRef.current;

    if (currentActiveConv && currentActiveConv.id === targetConvId) {
      setMessages(prev => {
        if (prev.some(m => m.id === msgObj.id)) return prev;
        return [...prev, {
          id: msgObj.id || Date.now(),
          conversation_id: targetConvId,
          sender_id: msgObj.sender_id,
          message: msgObj.message || msgObj.content,
          content: msgObj.content || msgObj.message,
          created_at: msgObj.created_at || new Date().toISOString()
        }];
      });
      scrollToBottom();
      markConversationRead(targetConvId).catch(() => {});
    }

    getConversations().then(data => setConversations(data)).catch(() => {});
  }, []);

  const { status: socketStatus, sendMessage: sendWsMessage } = useMessagingSocket(
    handleIncomingMessage
  );

  useEffect(() => {
    let isMounted = true;
    const initChat = async () => {
      try {
        const user = await getCurrentUser();
        if (isMounted && user) setCurrentUser(user);

        const [convs, conns] = await Promise.all([
          getConversations().catch(() => []),
          getConnections().catch(() => [])
        ]);
        if (isMounted) {
          if (Array.isArray(convs)) setConversations(convs);
          if (Array.isArray(conns)) setConnections(conns);
        }
      } catch (err) {
        console.error('Chat init error:', err);
      }
    };

    initChat();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery || searchQuery.length < 2) return;
    try {
      const res = await searchPublicUsers(searchQuery);
      setSearchResults(res.users || res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleStartConversation = async (targetUserId) => {
    try {
      const convRes = await createConversation(targetUserId);
      await loadConversations();
      const updatedConvs = await getConversations();
      const targetConv = updatedConvs.find(c => c.id === convRes.conversation_id || c.id === convRes.id);
      if (targetConv) {
        openConversation(targetConv);
      }
      setActiveTab('conversations');
    } catch (err) {
      alert(err.message || 'Failed to start conversation');
    }
  };

  const handleSendRequest = async (userId) => {
    try {
      await requestConnection(userId);
      setSearchResults(prev => prev.map(u => u.id === userId ? { ...u, connection_status: 'sent' } : u));
      loadConnections();
    } catch (err) {
      alert(err.message || 'Failed to send request');
    }
  };

  const handleAcceptRequest = async (userId) => {
    try {
      await acceptConnection(userId);
      loadConnections();
      loadConversations();
    } catch (err) {
      alert(err.message || 'Failed to accept request');
    }
  };

  const handleRejectRequest = async (userId) => {
    try {
      await rejectConnection(userId);
      loadConnections();
    } catch (err) {
      alert(err.message || 'Failed to reject request');
    }
  };

  const openConversation = async (conv) => {
    setActiveConversation(conv);
    try {
      const history = await getConversationMessages(conv.id);
      setMessages(history);
      scrollToBottom();
      await markConversationRead(conv.id);
      loadConversations();
    } catch (err) {
      console.error(err);
    }
  };

  const sendMessage = (e) => {
    e.preventDefault();
    if (!messageInput.trim() || !activeConversation) return;

    const content = messageInput.trim();
    const sent = sendWsMessage(activeConversation.id, content);
    
    if (!sent) {
      // Optimistic append if socket temporarily busy
      setMessages(prev => [...prev, {
        id: Date.now(),
        conversation_id: activeConversation.id,
        sender_id: currentUser?.id,
        message: content,
        content: content,
        created_at: new Date().toISOString()
      }]);
    }
    
    setMessageInput('');
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-viewport">
        <TopBar />
        <div className="chat-layout">
          
          {/* LEFT PANEL */}
          <div className="chat-sidebar glass-panel">
            <div className="chat-tabs">
              <button 
                className={activeTab === 'conversations' ? 'active' : ''} 
                onClick={() => setActiveTab('conversations')}
              >
                Chats
              </button>
              <button 
                className={activeTab === 'discover' ? 'active' : ''} 
                onClick={() => setActiveTab('discover')}
              >
                Discover
              </button>
              <button 
                className={activeTab === 'requests' ? 'active' : ''} 
                onClick={() => setActiveTab('requests')}
              >
                Requests {connections.pending_received.length > 0 && <span className="badge">{connections.pending_received.length}</span>}
              </button>
            </div>

            <div className="chat-sidebar-content">
              {activeTab === 'conversations' && (
                <div className="conversation-list">
                  {conversations.length === 0 ? (
                    <div className="empty-state">No conversations yet. Connect with someone in Discover!</div>
                  ) : (
                    conversations.map(conv => (
                      <div 
                        key={conv.id} 
                        className={`conversation-item ${activeConversation?.id === conv.id ? 'active' : ''}`}
                        onClick={() => openConversation(conv)}
                      >
                        <div className="avatar">{conv.other_avatar || conv.other_username.charAt(0).toUpperCase()}</div>
                        <div className="conv-details">
                          <div className="conv-header">
                            <span className="username">@{conv.other_username}</span>
                            {conv.unread_count > 0 && <span className="unread-dot" />}
                          </div>
                          <div className="last-message">{conv.last_message || 'No messages yet'}</div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {activeTab === 'discover' && (
                <div className="discover-list">
                  <form onSubmit={handleSearch} className="search-form">
                    <input 
                      type="text" 
                      placeholder="Search username..." 
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <button type="submit"><Search size={16} strokeWidth={1.8} /></button>
                  </form>
                  <div className="search-results">
                    {searchResults.map(user => (
                      <div key={user.id} className="user-card">
                        <div className="avatar">{user.avatar_initials}</div>
                        <div className="user-info">
                          <span className="name">{user.full_name}</span>
                          <span className="username">@{user.username}</span>
                        </div>
                        <div className="action" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                          <button 
                            onClick={() => handleStartConversation(user.id)} 
                            className="btn-icon"
                            title="Start Chat"
                          >
                            <MessageCircle size={16} strokeWidth={1.8}/>
                          </button>
                          {user.connection_status === 'none' && (
                            <button onClick={() => handleSendRequest(user.id)} className="btn-icon"><UserPlus size={16} strokeWidth={1.8}/></button>
                          )}
                          {user.connection_status === 'sent' && (
                            <span className="status-text">Pending</span>
                          )}
                          {user.connection_status === 'received' && (
                            <span className="status-text">Awaiting Reply</span>
                          )}
                          {user.connection_status === 'accepted' && (
                            <span className="status-text">Connected</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'requests' && (
                <div className="requests-list">
                  {connections.pending_received.length === 0 ? (
                    <div className="empty-state">No pending requests</div>
                  ) : (
                    connections.pending_received.map(req => (
                      <div key={req.id} className="user-card">
                        <div className="avatar">{req.avatar_initials}</div>
                        <div className="user-info">
                          <span className="name">{req.full_name}</span>
                          <span className="username">@{req.username}</span>
                        </div>
                        <div className="action-group">
                          <button onClick={() => handleAcceptRequest(req.id)} className="btn-icon success"><Check size={16} strokeWidth={1.8}/></button>
                          <button onClick={() => handleRejectRequest(req.id)} className="btn-icon danger"><X size={16} strokeWidth={1.8}/></button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>

          {/* RIGHT PANEL */}
          <div className="chat-main glass-panel">
            {!activeConversation ? (
              <div className="chat-placeholder">
                <MessageSquare size={48} strokeWidth={1.2} style={{ opacity: 0.3, marginBottom: '16px' }} />
                <h3>Select a conversation</h3>
                <p>Choose a connection from the left to start messaging.</p>
              </div>
            ) : (
              <div className="active-chat">
                <div className="chat-header">
                  <div className="avatar">{activeConversation.other_avatar || activeConversation.other_username?.charAt(0).toUpperCase()}</div>
                  <div className="chat-header-info">
                    <h3>@{activeConversation.other_username}</h3>
                    <span className="status-pill" style={{ fontSize: '11px', color: socketStatus === 'CONNECTED' ? 'var(--cyan)' : 'var(--text-tertiary)' }}>
                      ● {socketStatus}
                    </span>
                  </div>
                </div>
                
                <div className="messages-container">
                  {messages.map(msg => {
                    const isMine = msg.sender_id === currentUser?.id;
                    return (
                      <div key={msg.id} className={`message-bubble-wrapper ${isMine ? 'mine' : 'theirs'}`}>
                        <div className={`message-bubble ${isMine ? 'mine' : 'theirs'}`}>
                          {msg.content || msg.message}
                        </div>
                      </div>
                    );
                  })}
                  <div ref={messagesEndRef} />
                </div>
                
                <form onSubmit={sendMessage} className="message-input-area">
                  <input 
                    type="text" 
                    placeholder="Type a message..." 
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                  />
                  <button type="submit" disabled={!messageInput.trim()}>
                    <Send size={18} strokeWidth={1.8} />
                  </button>
                </form>
              </div>
            )}
          </div>
          
        </div>
      </div>
    </div>
  );
};

export default Chat;
