import { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, useLocation } from 'react-router-dom';
import { Search, UserPlus, Check, X, Send, MessageSquare, MessageCircle, Trash2 } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import { useMessagingSocket } from '../hooks/useMessagingSocket';
import { useNotificationsSocket } from '../hooks/useNotificationsSocket';
import UserProfilePanel from '../components/UserProfilePanel';
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
  getCurrentUser,
  deleteMessage
} from '../services/api';
import './Chat.css';

const Chat = () => {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const [currentUser, setCurrentUser] = useState(null);
  const [selectedProfileUserId, setSelectedProfileUserId] = useState(null);
  
  // Left Panel State
  const [activeTab, setActiveTab] = useState('conversations'); // 'conversations' | 'discover' | 'requests'
  const [conversations, setConversations] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchPerformed, setSearchPerformed] = useState(false);
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

  const scrollTimerRef = useRef(null);

  const loadConnections = useCallback(async () => {
    try {
      const data = await getConnections();
      setConnections(data);
    } catch (err) {
      console.error(err);
    }
  }, []);

  // Listen for real-time notification socket events to refresh connections & requests
  const handleNotificationEvent = useCallback((notif) => {
    const nType = notif.type || notif.data?.type || notif.reference_type;
    if (nType === 'connection_request' || nType === 'connection_accepted') {
      loadConnections();
      loadConversations();
    }
  }, [loadConnections, loadConversations]);

  useNotificationsSocket(handleNotificationEvent);

  // Sync tab with URL search parameter (?tab=requests) or router navigation state
  useEffect(() => {
    const tabParam = searchParams.get('tab') || location.state?.tab;
    if (tabParam && ['conversations', 'discover', 'requests'].includes(tabParam)) {
      setActiveTab(tabParam);
      if (tabParam === 'requests' || tabParam === 'discover') {
        loadConnections();
      }
      if (tabParam === 'conversations') {
        loadConversations();
      }
    }
  }, [searchParams, location.state, loadConnections, loadConversations]);

  const scrollToBottom = useCallback(() => {
    if (scrollTimerRef.current) clearTimeout(scrollTimerRef.current);
    scrollTimerRef.current = setTimeout(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);
  }, []);

  useEffect(() => {
    return () => {
      if (scrollTimerRef.current) clearTimeout(scrollTimerRef.current);
    };
  }, []);

  const activeConvRef = useRef(activeConversation);
  useEffect(() => {
    activeConvRef.current = activeConversation;
  }, [activeConversation]);

  // Real-time WebSocket event handler with local state updates (NO HTTP spam)
  const handleIncomingMessage = useCallback((eventData) => {
    const msgObj = eventData.message || eventData;
    const targetConvId = eventData.conversation_id || msgObj.conversation_id;
    const currentActiveConv = activeConvRef.current;
    const content = msgObj.content || msgObj.message || '';

    if (currentActiveConv && currentActiveConv.id === targetConvId) {
      setMessages(prev => {
        if (prev.some(m => m.id === msgObj.id)) return prev;
        return [...prev, {
          id: msgObj.id || Date.now(),
          conversation_id: targetConvId,
          sender_id: msgObj.sender_id,
          message: content,
          content: content,
          created_at: msgObj.created_at || new Date().toISOString()
        }];
      });
      scrollToBottom();
      markConversationRead(targetConvId).catch(() => {});
    }

    // Update conversation list locally without HTTP refetch
    setConversations(prev => {
      if (!Array.isArray(prev)) return prev;
      const existingIndex = prev.findIndex(c => c.id === targetConvId);
      if (existingIndex !== -1) {
        const updated = [...prev];
        const conv = { ...updated[existingIndex] };
        conv.last_message = content;
        conv.last_message_at = msgObj.created_at || new Date().toISOString();
        if (!currentActiveConv || currentActiveConv.id !== targetConvId) {
          conv.unread_count = (conv.unread_count || 0) + 1;
        }
        updated.splice(existingIndex, 1);
        return [conv, ...updated];
      } else {
        // Only fetch if from a completely unknown new conversation
        loadConversations();
        return prev;
      }
    });
  }, [loadConversations, scrollToBottom]);

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
          getConnections().catch(() => ({ accepted: [], pending_received: [], pending_sent: [], blocked: [] }))
        ]);

        if (isMounted) {
          const safeConvs = Array.isArray(convs) ? convs : [];
          setConversations(safeConvs);
          if (conns && typeof conns === 'object' && !Array.isArray(conns)) {
            setConnections(conns);
          }

          // Auto-select conversation or user from query parameters
          const convIdParam = searchParams.get('conversationId') || location.state?.conversationId;
          const userIdParam = searchParams.get('userId') || location.state?.userId;

          if (convIdParam) {
            const target = safeConvs.find(c => String(c.id) === String(convIdParam));
            if (target) {
              openConversation(target);
              setActiveTab('conversations');
            }
          } else if (userIdParam) {
            const target = safeConvs.find(c => String(c.other_user?.id) === String(userIdParam));
            if (target) {
              openConversation(target);
              setActiveTab('conversations');
            } else {
              handleStartConversation(Number(userIdParam));
            }
          }
        }
      } catch (err) {
        console.error('Chat init error:', err);
      }
    };

    initChat();
    return () => {
      isMounted = false;
    };
  }, [searchParams, location.state]);

  const executeSearch = useCallback(async (query) => {
    const q = (query || '').trim();
    setIsSearching(true);
    setSearchPerformed(Boolean(q));
    try {
      const res = await searchPublicUsers(q);
      const list = res?.users || (Array.isArray(res) ? res : []);
      setSearchResults(list);
    } catch (err) {
      console.error('Search error:', err);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleSearch = (e) => {
    if (e) e.preventDefault();
    executeSearch(searchQuery);
  };

  useEffect(() => {
    if (activeTab !== 'discover') return;
    const timer = setTimeout(() => {
      executeSearch(searchQuery);
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery, activeTab, executeSearch]);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'requests' || tab === 'discover') {
      loadConnections();
    }
    if (tab === 'discover') {
      executeSearch(searchQuery);
    }
  };

  const handleStartConversation = async (targetUserId) => {
    try {
      const convRes = await createConversation(targetUserId);
      const updatedConvs = await getConversations();
      setConversations(updatedConvs);
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

  const handleAcceptRequest = async (userId, requestId) => {
    try {
      await acceptConnection({ user_id: userId, request_id: requestId });
      await Promise.all([loadConnections(), loadConversations()]);
    } catch (err) {
      alert(err.message || 'Failed to accept request');
    }
  };

  const handleRejectRequest = async (userId, requestId) => {
    try {
      await rejectConnection({ user_id: userId, request_id: requestId });
      await loadConnections();
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
      setConversations(prev => prev.map(c => c.id === conv.id ? { ...c, unread_count: 0 } : c));
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

  const handleDeleteMessage = async (messageId) => {
    try {
      await deleteMessage(messageId);
      setMessages(prev => prev.filter(m => m.id !== messageId));
    } catch (err) {
      alert(err.message || 'Failed to delete message.');
    }
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
                onClick={() => handleTabChange('conversations')}
              >
                Chats
              </button>
              <button 
                className={activeTab === 'discover' ? 'active' : ''} 
                onClick={() => handleTabChange('discover')}
              >
                Discover
              </button>
              <button 
                className={activeTab === 'requests' ? 'active' : ''} 
                onClick={() => handleTabChange('requests')}
              >
                Requests {connections.pending_received?.length > 0 && <span className="badge">{connections.pending_received.length}</span>}
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
                      placeholder="Search username or MKC ID..." 
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <button type="submit" aria-label="Search">
                      <Search size={16} strokeWidth={1.8} />
                    </button>
                  </form>
                  <div className="search-results">
                    {isSearching ? (
                      <div className="empty-state">Searching community members...</div>
                    ) : searchResults.length > 0 ? (
                      searchResults.map(user => {
                        const displayName = user.full_name || user.display_name || user.username || 'Member';
                        const usernameDisplay = user.username || 'member';
                        const initials = user.avatar_initials || usernameDisplay.substring(0, 2).toUpperCase();
                        const mkcId = user.mkc_id || (user.id ? `MKC-${user.id}` : '');

                        return (
                          <div key={user.id} className="user-card">
                            <div 
                              className="avatar clickable" 
                              style={{ cursor: 'pointer' }}
                              onClick={() => setSelectedProfileUserId(user.id)}
                              title="View Profile"
                            >
                              {initials}
                            </div>
                            <div 
                              className="user-info clickable" 
                              style={{ cursor: 'pointer' }}
                              onClick={() => setSelectedProfileUserId(user.id)}
                              title="View Profile"
                            >
                              <span className="name">{displayName}</span>
                              <span className="username">@{usernameDisplay}</span>
                              {mkcId && (
                                <span style={{ fontSize: '10px', color: 'var(--text-tertiary)', fontFamily: 'monospace', display: 'block', marginTop: '2px' }}>
                                  {mkcId}
                                </span>
                              )}
                            </div>
                            <div className="action" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                              {user.connection_status === 'accepted' && (
                                <button 
                                  onClick={() => handleStartConversation(user.id)} 
                                  className="btn-icon"
                                  title="Start Chat"
                                >
                                  <MessageCircle size={16} strokeWidth={1.8}/>
                                </button>
                              )}
                              {user.connection_status === 'none' && (
                                <button 
                                  onClick={() => handleSendRequest(user.id)} 
                                  className="btn-icon"
                                  title="Send Connection Request"
                                >
                                  <UserPlus size={16} strokeWidth={1.8}/>
                                </button>
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
                        );
                      })
                    ) : searchPerformed ? (
                      <div className="empty-state">No members found matching &quot;{searchQuery}&quot;</div>
                    ) : (
                      <div className="empty-state">Search by username, name, or MKC ID</div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'requests' && (
                <div className="requests-list">
                  {(!connections.pending_received || connections.pending_received.length === 0) ? (
                    <div className="empty-state">No pending requests</div>
                  ) : (
                    connections.pending_received.map(req => {
                      const targetUserId = req.user_id || req.id;
                      const reqId = req.request_id || req.connection_id || req.id;
                      const isHighlighted = String(reqId) === String(searchParams.get('requestId') || location.state?.requestId) ||
                                            String(targetUserId) === String(location.state?.senderId);
                      return (
                        <div 
                          key={reqId} 
                          className={`user-card ${isHighlighted ? 'highlighted-request' : ''}`}
                          style={isHighlighted ? { border: '1px solid var(--electric-blue, #22B8FF)', boxShadow: '0 0 16px rgba(34, 184, 255, 0.3)' } : undefined}
                        >
                          <div 
                            className="avatar clickable" 
                            style={{ cursor: 'pointer' }}
                            onClick={() => setSelectedProfileUserId(targetUserId)}
                            title="View Profile"
                          >
                            {req.avatar_initials || req.username?.slice(0, 2).toUpperCase() || 'MK'}
                          </div>
                          <div 
                            className="user-info clickable" 
                            style={{ cursor: 'pointer' }}
                            onClick={() => setSelectedProfileUserId(targetUserId)}
                            title="View Profile"
                          >
                            <span className="name">{req.full_name || req.username}</span>
                            <span className="username">@{req.username}</span>
                            {req.bio && (
                              <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block', maxWidth: '180px' }}>
                                {req.bio}
                              </span>
                            )}
                          </div>
                          <div className="action-group">
                            <button 
                              onClick={() => handleAcceptRequest(targetUserId, reqId)} 
                              className="btn-icon success"
                              title="Accept Connection Request"
                            >
                              <Check size={16} strokeWidth={1.8}/>
                            </button>
                            <button 
                              onClick={() => handleRejectRequest(targetUserId, reqId)} 
                              className="btn-icon danger"
                              title="Decline Connection Request"
                            >
                              <X size={16} strokeWidth={1.8}/>
                            </button>
                          </div>
                        </div>
                      );
                    })
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
                  <div 
                    className="avatar clickable" 
                    style={{ cursor: 'pointer' }}
                    onClick={() => setSelectedProfileUserId(activeConversation.other_user_id)}
                    title="View Profile"
                  >
                    {activeConversation.other_avatar || activeConversation.other_username?.charAt(0).toUpperCase()}
                  </div>
                  <div 
                    className="chat-header-info clickable" 
                    style={{ cursor: 'pointer' }}
                    onClick={() => setSelectedProfileUserId(activeConversation.other_user_id)}
                    title="View Profile"
                  >
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
                        {isMine && (
                          <button
                            onClick={() => handleDeleteMessage(msg.id)}
                            className="msg-delete-btn"
                            title="Delete message"
                          >
                            <Trash2 size={13} strokeWidth={1.6} />
                          </button>
                        )}
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

      {/* User Profile Panel Modal */}
      {selectedProfileUserId && (
        <UserProfilePanel
          userId={selectedProfileUserId}
          onClose={() => setSelectedProfileUserId(null)}
          onStartConversation={(targetId) => {
            setSelectedProfileUserId(null);
            handleStartConversation(targetId);
          }}
          onConnectionUpdated={() => {
            loadConnections();
            loadConversations();
            if (searchQuery && searchQuery.length >= 2) {
              searchPublicUsers(searchQuery).then(res => setSearchResults(res.users || res)).catch(() => {});
            }
          }}
        />
      )}
    </div>
  );
};

export default Chat;
