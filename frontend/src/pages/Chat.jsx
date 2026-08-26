import { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, useLocation } from 'react-router-dom';
import { 
  Search, UserPlus, Check, X, Send, MessageSquare, MessageCircle, 
  Trash2, Smile, Sparkles, Image as ImageIcon, Mic, Play, Pause, 
  Loader2, Maximize2 
} from 'lucide-react';
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
  deleteMessage,
  uploadChatAttachment,
  getMediaUrl
} from '../services/api';
import './Chat.css';

// ============================================================================
// STICKER DEFINITIONS & PACKS
// ============================================================================
const STICKER_PACKS = {
  motivation: {
    name: 'Motivation',
    icon: '🔥',
    stickers: [
      { id: 'mkc_relentless', title: 'RELENTLESS', subtitle: 'Non-stop execution', color: '#f59e0b', icon: '🔥' },
      { id: 'mkc_lock_in', title: 'LOCK IN', subtitle: 'Zero distractions', color: '#38bdf8', icon: '🎯' },
      { id: 'mkc_discipline', title: '100% DISCIPLINE', subtitle: 'Emotion vs Standard', color: '#10b981', icon: '⚡' },
      { id: 'mkc_no_excuses', title: 'NO EXCUSES', subtitle: 'Only results', color: '#ef4444', icon: '🛡️' },
    ]
  },
  victory: {
    name: 'Victory',
    icon: '🏆',
    stickers: [
      { id: 'mkc_mission_complete', title: 'MISSION COMPLETE', subtitle: 'Protocol crushed', color: '#eab308', icon: '🏆' },
      { id: 'mkc_breakthrough', title: 'BREAKTHROUGH', subtitle: 'New standard set', color: '#a855f7', icon: '💎' },
      { id: 'mkc_champion', title: 'CHAMPION', subtitle: 'Mastery achieved', color: '#f59e0b', icon: '👑' },
      { id: 'mkc_milestone', title: 'MILESTONE CRUSHED', subtitle: 'Moving forward', color: '#06b6d4', icon: '🚀' },
    ]
  },
  discipline: {
    name: 'Discipline',
    icon: '⚡',
    stickers: [
      { id: 'mkc_deep_work', title: 'DEEP WORK MODE', subtitle: 'In the zone', color: '#6366f1', icon: '🧠' },
      { id: 'mkc_execute', title: 'EXECUTE NOW', subtitle: 'Action over talk', color: '#ec4899', icon: '⚡' },
      { id: 'mkc_daily_protocol', title: 'DAILY PROTOCOL', subtitle: 'Consistency compounds', color: '#14b8a6', icon: '📋' },
      { id: 'mkc_iron_will', title: 'IRON WILL', subtitle: 'Unbreakable focus', color: '#64748b', icon: '⚔️' },
    ]
  },
  goals: {
    name: 'Goals',
    icon: '🚀',
    stickers: [
      { id: 'mkc_level_up', title: 'LEVEL UP', subtitle: 'Upgraded capacity', color: '#3b82f6', icon: '📈' },
      { id: 'mkc_compounding', title: '1% DAILY WINS', subtitle: 'Compounding growth', color: '#22c55e', icon: '🌱' },
      { id: 'mkc_vision', title: 'VISION 2026', subtitle: 'Eyes on horizon', color: '#8b5cf6', icon: '✨' },
      { id: 'mkc_mastery', title: 'MASTERY KEY', subtitle: 'Unlock potential', color: '#d97706', icon: '🔑' },
    ]
  }
};

// ============================================================================
// EMOJI CATEGORIES
// ============================================================================
const EMOJI_CATEGORIES = {
  smileys: {
    label: 'Smileys',
    emojis: ['😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😋', '😛', '😜', '🤪', '😎', '🤩', '🥳', '😏', '🤓', '🧐', '🤠']
  },
  gestures: {
    label: 'Gestures',
    emojis: ['👍', '👎', '👊', '✊', '🤛', '🤜', '👏', '🙌', '👐', '🤲', '🤝', '🙏', '✍️', '💪', '🦾', '👈', '👉', '👆', '👇', '☝️', '✌️', '🤞', '🤟', '🤘', '🤙', '🖐️', '✋', '👌']
  },
  energy: {
    label: 'Momentum',
    emojis: ['🔥', '⚡', '💥', '✨', '🌟', '⭐', '💫', '🏆', '🥇', '🥈', '🥉', '🎯', '🚀', '💎', '🛡️', '⚔️', '👑', '🎖️', '🏅', '🦁', '🐺', '🦅', '🏔️', '🔑', '📈', '💯']
  },
  focus: {
    label: 'Focus',
    emojis: ['💡', '🧠', '📚', '📖', '🔬', '🧘', '⏳', '⏱️', '⏰', '📅', '📌', '📍', '📝', '📊', '📉', '💼', '🛠️', '⚙️', '🔒', '🔓', '🌐', '🧭', '🏁', '☀️', '☕']
  }
};

// ============================================================================
// AUDIO VOICE PLAYER COMPONENT
// ============================================================================
const AudioVoicePlayer = ({ src, duration, isMine }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [totalDuration, setTotalDuration] = useState(duration || 0);
  const audioRef = useRef(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadedMetadata = () => {
      if (audio.duration && !isNaN(audio.duration) && isFinite(audio.duration)) {
        setTotalDuration(Math.round(audio.duration));
      }
    };

    const handleTimeUpdate = () => {
      setCurrentTime(Math.round(audio.currentTime));
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
    };
  }, []);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().then(() => setIsPlaying(true)).catch(console.error);
    }
  };

  const handleSeek = (e) => {
    if (!audioRef.current || !totalDuration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const clickPos = (e.clientX - rect.left) / rect.width;
    const newTime = clickPos * totalDuration;
    audioRef.current.currentTime = newTime;
    setCurrentTime(Math.round(newTime));
  };

  const formatTime = (secs) => {
    const s = Math.max(0, Math.floor(secs || 0));
    const mins = Math.floor(s / 60);
    const remSecs = s % 60;
    return `${mins}:${remSecs < 10 ? '0' : ''}${remSecs}`;
  };

  const progressPercent = totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0;

  return (
    <div className={`voice-memo-player ${isMine ? 'mine' : 'theirs'}`}>
      <audio ref={audioRef} src={getMediaUrl(src)} preload="metadata" />
      <button 
        type="button" 
        className="voice-play-btn" 
        onClick={togglePlay} 
        aria-label={isPlaying ? "Pause voice message" : "Play voice message"}
      >
        {isPlaying ? <Pause size={15} /> : <Play size={15} style={{ marginLeft: '2px' }} />}
      </button>
      
      <div className="voice-progress-container" onClick={handleSeek}>
        <div className="voice-waveform-bars">
          {[40, 75, 55, 90, 60, 100, 45, 80, 65, 95, 50, 70, 85, 40, 60, 75, 90, 55, 45, 80].map((h, i) => (
            <div 
              key={i} 
              className={`waveform-bar ${((i + 1) / 20) * 100 <= progressPercent ? 'active' : ''}`}
              style={{ height: `${h}%` }} 
            />
          ))}
        </div>
      </div>
      
      <span className="voice-duration">
        {isPlaying ? formatTime(currentTime) : formatTime(totalDuration)}
      </span>
    </div>
  );
};

// ============================================================================
// MAIN CHAT COMPONENT
// ============================================================================
const Chat = () => {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const [currentUser, setCurrentUser] = useState(null);
  const [selectedProfileUserId, setSelectedProfileUserId] = useState(null);
  
  // Left Panel State
  const initialTab = searchParams.get('tab') || location.state?.tab;
  const [activeTab, setActiveTab] = useState(
    initialTab && ['conversations', 'discover', 'requests'].includes(initialTab)
      ? initialTab
      : 'conversations'
  );
  const [conversations, setConversations] = useState([]);
  const [convFilterQuery, setConvFilterQuery] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [connections, setConnections] = useState({ accepted: [], pending_received: [], pending_sent: [], blocked: [] });
  
  // Right Panel State
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [isOtherUserTyping, setIsOtherUserTyping] = useState(false);
  const [otherUserTypingUsername, setOtherUserTypingUsername] = useState('');

  // Rich Media State
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [activeEmojiCategory, setActiveEmojiCategory] = useState('smileys');
  const [showStickerPicker, setShowStickerPicker] = useState(false);
  const [activeStickerCategory, setActiveStickerCategory] = useState('motivation');
  const [isUploadingMedia, setIsUploadingMedia] = useState(false);
  const [lightboxImage, setLightboxImage] = useState(null);

  // Voice Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recordTimerRef = useRef(null);
  const fileInputRef = useRef(null);

  // Refs
  const messagesEndRef = useRef(null);
  const scrollTimerRef = useRef(null);
  const otherTypingTimerRef = useRef(null);
  const myTypingDebounceRef = useRef(null);
  const activeConvRef = useRef(activeConversation);

  useEffect(() => {
    activeConvRef.current = activeConversation;
  }, [activeConversation]);

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
      if (otherTypingTimerRef.current) clearTimeout(otherTypingTimerRef.current);
      if (myTypingDebounceRef.current) clearTimeout(myTypingDebounceRef.current);
      if (recordTimerRef.current) clearInterval(recordTimerRef.current);
    };
  }, []);

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

  const openConversation = useCallback(async (conv) => {
    setActiveConversation(conv);
    setIsOtherUserTyping(false);
    setShowEmojiPicker(false);
    setShowStickerPicker(false);
    try {
      const history = await getConversationMessages(conv.id);
      setMessages(history);
      scrollToBottom();
      await markConversationRead(conv.id);
      setConversations(prev => prev.map(c => c.id === conv.id ? { ...c, unread_count: 0 } : c));
    } catch (err) {
      console.error(err);
    }
  }, [scrollToBottom]);

  const handleStartConversation = useCallback(async (targetUserId) => {
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
  }, [openConversation]);

  // Notification socket listener
  const handleNotificationEvent = useCallback((notif) => {
    const nType = notif.type || notif.data?.type || notif.reference_type;
    if (nType === 'connection_request' || nType === 'connection_accepted') {
      loadConnections();
      loadConversations();
    }
  }, [loadConnections, loadConversations]);

  useNotificationsSocket(handleNotificationEvent);

  // Real-time WebSocket messaging handler
  const handleIncomingMessage = useCallback((eventData) => {
    if (eventData.type === 'typing.start') {
      const targetConvId = eventData.conversation_id;
      const currentActiveConv = activeConvRef.current;
      if (currentActiveConv && currentActiveConv.id === targetConvId) {
        setIsOtherUserTyping(true);
        setOtherUserTypingUsername(eventData.username || currentActiveConv.other_username || 'Member');
        if (otherTypingTimerRef.current) clearTimeout(otherTypingTimerRef.current);
        otherTypingTimerRef.current = setTimeout(() => {
          setIsOtherUserTyping(false);
        }, 3000);
      }
      return;
    }

    if (eventData.type === 'typing.stop') {
      const targetConvId = eventData.conversation_id;
      const currentActiveConv = activeConvRef.current;
      if (currentActiveConv && currentActiveConv.id === targetConvId) {
        setIsOtherUserTyping(false);
      }
      return;
    }

    const msgObj = eventData.message || eventData;
    const targetConvId = eventData.conversation_id || msgObj.conversation_id;
    const currentActiveConv = activeConvRef.current;
    const content = msgObj.content || msgObj.message || '';

    if (currentActiveConv && currentActiveConv.id === targetConvId) {
      setIsOtherUserTyping(false);
      setMessages(prev => {
        if (prev.some(m => m.id === msgObj.id)) return prev;
        return [...prev, {
          id: msgObj.id || Date.now(),
          conversation_id: targetConvId,
          sender_id: msgObj.sender_id,
          sender_username: msgObj.sender_username,
          message: content,
          content: content,
          message_type: msgObj.message_type || 'text',
          attachment_url: msgObj.attachment_url || null,
          attachment_metadata: msgObj.attachment_metadata || null,
          attachment_duration: msgObj.attachment_duration || null,
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
        
        if (msgObj.message_type === 'image') {
          conv.last_message = '📷 Photo';
        } else if (msgObj.message_type === 'voice') {
          conv.last_message = '🎤 Voice message';
        } else if (msgObj.message_type === 'sticker') {
          conv.last_message = '✨ Sticker';
        } else {
          conv.last_message = content;
        }
        
        conv.last_message_at = msgObj.created_at || new Date().toISOString();
        if (!currentActiveConv || currentActiveConv.id !== targetConvId) {
          conv.unread_count = (conv.unread_count || 0) + 1;
        }
        updated.splice(existingIndex, 1);
        return [conv, ...updated];
      } else {
        loadConversations();
        return prev;
      }
    });
  }, [loadConversations, scrollToBottom]);

  const { status: socketStatus, sendMessage: sendWsMessage, sendTyping } = useMessagingSocket(
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

          const convIdParam = searchParams.get('conversationId') || location.state?.conversationId;
          const userIdParam = searchParams.get('userId') || location.state?.userId;

          if (convIdParam) {
            const target = safeConvs.find(c => String(c.id) === String(convIdParam));
            if (target) {
              openConversation(target);
              setActiveTab('conversations');
            }
          } else if (userIdParam) {
            const target = safeConvs.find(c => String(c.other_user_id || c.other_user?.id) === String(userIdParam));
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
  }, [searchParams, location.state, openConversation, handleStartConversation]);

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

  const handleInputChange = (e) => {
    const val = e.target.value;
    setMessageInput(val);
    if (activeConversation) {
      sendTyping(activeConversation.id, true);
      if (myTypingDebounceRef.current) clearTimeout(myTypingDebounceRef.current);
      myTypingDebounceRef.current = setTimeout(() => {
        if (activeConversation) {
          sendTyping(activeConversation.id, false);
        }
      }, 2500);
    }
  };

  const sendMessage = (e) => {
    if (e) e.preventDefault();
    if (!messageInput.trim() || !activeConversation) return;

    if (myTypingDebounceRef.current) clearTimeout(myTypingDebounceRef.current);
    sendTyping(activeConversation.id, false);

    const content = messageInput.trim();
    const sent = sendWsMessage(activeConversation.id, content, { message_type: 'text' });
    
    if (!sent) {
      setMessages(prev => [...prev, {
        id: Date.now(),
        conversation_id: activeConversation.id,
        sender_id: currentUser?.id,
        message: content,
        content: content,
        message_type: 'text',
        created_at: new Date().toISOString()
      }]);
    }
    
    setMessageInput('');
    setShowEmojiPicker(false);
    setShowStickerPicker(false);
  };

  // EMOJI INSERTION
  const handleEmojiSelect = (emoji) => {
    setMessageInput(prev => prev + emoji);
  };

  // STICKER SENDING
  const handleSendSticker = (sticker) => {
    if (!activeConversation) return;
    const stickerPayload = {
      sticker_id: sticker.id,
      title: sticker.title,
      subtitle: sticker.subtitle,
      color: sticker.color,
      icon: sticker.icon,
    };

    sendWsMessage(activeConversation.id, sticker.title, {
      message_type: 'sticker',
      attachment_metadata: JSON.stringify(stickerPayload),
    });

    setMessages(prev => [...prev, {
      id: Date.now(),
      conversation_id: activeConversation.id,
      sender_id: currentUser?.id,
      message: sticker.title,
      content: sticker.title,
      message_type: 'sticker',
      attachment_metadata: JSON.stringify(stickerPayload),
      created_at: new Date().toISOString()
    }]);

    setShowStickerPicker(false);
    scrollToBottom();
  };

  // IMAGE UPLOAD & SEND
  const handleImageFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !activeConversation) return;

    try {
      setIsUploadingMedia(true);
      const res = await uploadChatAttachment(file);
      if (res?.url) {
        sendWsMessage(activeConversation.id, '', {
          message_type: 'image',
          attachment_url: res.url,
          attachment_metadata: JSON.stringify({ filename: res.filename, size: res.size }),
        });

        setMessages(prev => [...prev, {
          id: Date.now(),
          conversation_id: activeConversation.id,
          sender_id: currentUser?.id,
          message: '',
          content: '',
          message_type: 'image',
          attachment_url: res.url,
          created_at: new Date().toISOString()
        }]);
        scrollToBottom();
      }
    } catch (err) {
      alert(err.message || 'Failed to upload image.');
    } finally {
      setIsUploadingMedia(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // VOICE RECORDING CONTROLS
  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingSeconds(0);

      recordTimerRef.current = setInterval(() => {
        setRecordingSeconds(prev => prev + 1);
      }, 1000);
    } catch {
      alert('Microphone access is required to record voice messages. Please check your browser permissions.');
    }
  };

  const cancelVoiceRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (recordTimerRef.current) clearInterval(recordTimerRef.current);
    setIsRecording(false);
    setRecordingSeconds(0);
    audioChunksRef.current = [];
  };

  const finishAndSendVoiceRecording = async () => {
    if (!mediaRecorderRef.current || !activeConversation) return;

    if (recordTimerRef.current) clearInterval(recordTimerRef.current);
    const duration = recordingSeconds;
    setIsRecording(false);

    mediaRecorderRef.current.onstop = async () => {
      try {
        setIsUploadingMedia(true);
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const audioFile = new File([audioBlob], `voice_${Date.now()}.webm`, { type: 'audio/webm' });
        
        const res = await uploadChatAttachment(audioFile);
        if (res?.url) {
          sendWsMessage(activeConversation.id, '', {
            message_type: 'voice',
            attachment_url: res.url,
            attachment_duration: duration,
          });

          setMessages(prev => [...prev, {
            id: Date.now(),
            conversation_id: activeConversation.id,
            sender_id: currentUser?.id,
            message: '',
            content: '',
            message_type: 'voice',
            attachment_url: res.url,
            attachment_duration: duration,
            created_at: new Date().toISOString()
          }]);
          scrollToBottom();
        }
      } catch (err) {
        alert(err.message || 'Failed to send voice message.');
      } finally {
        setIsUploadingMedia(false);
        setRecordingSeconds(0);
        audioChunksRef.current = [];
      }
    };

    mediaRecorderRef.current.stop();
  };

  const handleDeleteMessage = async (messageId) => {
    try {
      await deleteMessage(messageId);
      setMessages(prev => prev.filter(m => m.id !== messageId));
    } catch (err) {
      alert(err.message || 'Failed to delete message.');
    }
  };

  const filteredConversations = conversations.filter(c => {
    if (!convFilterQuery.trim()) return true;
    const q = convFilterQuery.toLowerCase();
    const username = (c.other_username || '').toLowerCase();
    const fullName = (c.other_full_name || '').toLowerCase();
    const lastMsg = (c.last_message || '').toLowerCase();
    return username.includes(q) || fullName.includes(q) || lastMsg.includes(q);
  });

  return (
    <>
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
                  {conversations.length > 0 && (
                    <div className="chat-filter-box">
                      <input
                        type="text"
                        className="chat-filter-input"
                        placeholder="Filter chats..."
                        value={convFilterQuery}
                        onChange={(e) => setConvFilterQuery(e.target.value)}
                      />
                    </div>
                  )}
                  {filteredConversations.length === 0 ? (
                    <div className="empty-state">
                      {conversations.length === 0
                        ? "No conversations yet. Connect with someone in Discover!"
                        : `No chats matching "${convFilterQuery}"`}
                    </div>
                  ) : (
                    filteredConversations.map(conv => (
                      <div 
                        key={conv.id} 
                        className={`conversation-item ${activeConversation?.id === conv.id ? 'active' : ''}`}
                        onClick={() => openConversation(conv)}
                      >
                        <div className="avatar">{conv.other_avatar || conv.other_username?.charAt(0).toUpperCase()}</div>
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
                      placeholder="Search by username or name..." 
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <button type="submit" disabled={isSearching}>
                      <Search size={16} />
                    </button>
                  </form>

                  {isSearching ? (
                    <div className="empty-state">Searching directory...</div>
                  ) : searchResults.length === 0 ? (
                    <div className="empty-state">
                      {searchPerformed ? "No users found matching your search." : "Search to discover and connect with peers."}
                    </div>
                  ) : (
                    searchResults.map(user => (
                      <div key={user.id} className="user-card">
                        <div 
                          className="avatar clickable" 
                          onClick={() => setSelectedProfileUserId(user.id)}
                          title="View Profile"
                        >
                          {user.avatar_initials || user.username?.charAt(0).toUpperCase()}
                        </div>
                        <div 
                          className="user-info clickable"
                          onClick={() => setSelectedProfileUserId(user.id)}
                          title="View Profile"
                        >
                          <span className="username">@{user.username}</span>
                          <span className="name">{user.full_name}</span>
                        </div>
                        <div className="user-actions">
                          {user.connection_status === 'none' && (
                            <button 
                              className="btn-icon" 
                              title="Connect"
                              onClick={() => handleSendRequest(user.id)}
                            >
                              <UserPlus size={16} />
                            </button>
                          )}
                          {user.connection_status === 'sent' && (
                            <span className="status-text pending">Pending</span>
                          )}
                          {user.connection_status === 'received' && (
                            <div className="action-group">
                              <button 
                                className="btn-icon success" 
                                title="Accept"
                                onClick={() => handleAcceptRequest(user.id)}
                              >
                                <Check size={16} />
                              </button>
                              <button 
                                className="btn-icon danger" 
                                title="Decline"
                                onClick={() => handleRejectRequest(user.id)}
                              >
                                <X size={16} />
                              </button>
                            </div>
                          )}
                          {user.connection_status === 'accepted' && (
                            <button 
                              className="btn-icon primary" 
                              title="Message"
                              onClick={() => handleStartConversation(user.id)}
                            >
                              <MessageCircle size={16} />
                            </button>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {activeTab === 'requests' && (
                <div className="requests-list">
                  {(!connections.pending_received || connections.pending_received.length === 0) ? (
                    <div className="empty-state">No pending requests</div>
                  ) : (
                    connections.pending_received.map(req => (
                      <div key={req.request_id || req.id} className="user-card">
                        <div 
                          className="avatar clickable" 
                          onClick={() => setSelectedProfileUserId(req.user_id || req.id)}
                          title="View Profile"
                        >
                          {req.avatar_initials || req.username?.charAt(0).toUpperCase()}
                        </div>
                        <div 
                          className="user-info clickable"
                          onClick={() => setSelectedProfileUserId(req.user_id || req.id)}
                          title="View Profile"
                        >
                          <span className="username">@{req.username}</span>
                          <span className="name">{req.full_name}</span>
                        </div>
                        <div className="action-group">
                          <button 
                            className="btn-icon success" 
                            title="Accept"
                            onClick={() => handleAcceptRequest(req.user_id || req.id, req.request_id || req.id)}
                          >
                            <Check size={16} />
                          </button>
                          <button 
                            className="btn-icon danger" 
                            title="Decline"
                            onClick={() => handleRejectRequest(req.user_id || req.id, req.request_id || req.id)}
                          >
                            <X size={16} />
                          </button>
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
                
                {/* MESSAGES LIST */}
                <div className="messages-container">
                  {messages.map(msg => {
                    const isMine = msg.sender_id === currentUser?.id;
                    const msgType = msg.message_type || 'text';

                    // Parse sticker metadata if sticker
                    let stickerMeta = null;
                    if (msgType === 'sticker') {
                      try {
                        stickerMeta = typeof msg.attachment_metadata === 'string' 
                          ? JSON.parse(msg.attachment_metadata) 
                          : msg.attachment_metadata;
                      } catch {
                        stickerMeta = { title: msg.message || 'MKC STICKER', icon: '✨', color: '#f59e0b' };
                      }
                    }

                    return (
                      <div key={msg.id} className={`message-bubble-wrapper ${isMine ? 'mine' : 'theirs'} ${msgType}`}>
                        {isMine && (
                          <button
                            onClick={() => handleDeleteMessage(msg.id)}
                            className="msg-delete-btn"
                            title="Delete message"
                          >
                            <Trash2 size={13} strokeWidth={1.6} />
                          </button>
                        )}
                        
                        {/* RENDER BY MESSAGE TYPE */}
                        {msgType === 'image' && (
                          <div className={`message-bubble image-bubble ${isMine ? 'mine' : 'theirs'}`}>
                            <div 
                              className="chat-image-preview-wrapper"
                              onClick={() => setLightboxImage(msg.attachment_url)}
                              title="Click to expand"
                            >
                              <img src={getMediaUrl(msg.attachment_url)} alt="Attachment" className="chat-image-attachment" />
                              <div className="chat-image-overlay">
                                <Maximize2 size={16} />
                              </div>
                            </div>
                            {msg.content && msg.content.trim() && (
                              <div className="chat-image-caption">{msg.content}</div>
                            )}
                          </div>
                        )}

                        {msgType === 'voice' && (
                          <div className={`message-bubble voice-bubble ${isMine ? 'mine' : 'theirs'}`}>
                            <AudioVoicePlayer 
                              src={msg.attachment_url} 
                              duration={msg.attachment_duration} 
                              isMine={isMine} 
                            />
                          </div>
                        )}

                        {msgType === 'sticker' && stickerMeta && (
                          <div className={`message-bubble sticker-bubble ${isMine ? 'mine' : 'theirs'}`}>
                            <div 
                              className="mkc-chat-sticker-card"
                              style={{ borderColor: stickerMeta.color || 'var(--cyan)' }}
                            >
                              <span className="sticker-icon">{stickerMeta.icon || '🔥'}</span>
                              <div className="sticker-meta">
                                <span className="sticker-title" style={{ color: stickerMeta.color || 'var(--cyan)' }}>
                                  {stickerMeta.title}
                                </span>
                                {stickerMeta.subtitle && (
                                  <span className="sticker-subtitle">{stickerMeta.subtitle}</span>
                                )}
                              </div>
                            </div>
                          </div>
                        )}

                        {msgType === 'text' && (
                          <div className={`message-bubble ${isMine ? 'mine' : 'theirs'}`}>
                            {msg.content || msg.message}
                          </div>
                        )}
                      </div>
                    );
                  })}

                  {isOtherUserTyping && (
                    <div className="typing-indicator-wrapper">
                      <div className="typing-dots">
                        <div className="typing-dot" />
                        <div className="typing-dot" />
                        <div className="typing-dot" />
                      </div>
                      <span className="typing-text">@{otherUserTypingUsername} is typing...</span>
                    </div>
                  )}

                  {isUploadingMedia && (
                    <div className="typing-indicator-wrapper" style={{ borderColor: 'var(--cyan)' }}>
                      <Loader2 size={14} className="spin-icon" style={{ color: 'var(--cyan)' }} />
                      <span className="typing-text" style={{ color: 'var(--cyan)' }}>Uploading media...</span>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>

                {/* EMOJI PICKER POPUP */}
                {showEmojiPicker && (
                  <div className="emoji-picker-modal glass-panel">
                    <div className="emoji-category-tabs">
                      {Object.entries(EMOJI_CATEGORIES).map(([catKey, cat]) => (
                        <button
                          key={catKey}
                          type="button"
                          className={`emoji-cat-btn ${activeEmojiCategory === catKey ? 'active' : ''}`}
                          onClick={() => setActiveEmojiCategory(catKey)}
                        >
                          {cat.label}
                        </button>
                      ))}
                    </div>
                    <div className="emoji-grid">
                      {EMOJI_CATEGORIES[activeEmojiCategory].emojis.map((em, idx) => (
                        <button
                          key={idx}
                          type="button"
                          className="emoji-item-btn"
                          onClick={() => handleEmojiSelect(em)}
                        >
                          {em}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* STICKER PICKER POPUP */}
                {showStickerPicker && (
                  <div className="sticker-picker-modal glass-panel">
                    <div className="sticker-category-tabs">
                      {Object.entries(STICKER_PACKS).map(([packKey, pack]) => (
                        <button
                          key={packKey}
                          type="button"
                          className={`sticker-cat-btn ${activeStickerCategory === packKey ? 'active' : ''}`}
                          onClick={() => setActiveStickerCategory(packKey)}
                        >
                          <span>{pack.icon}</span> {pack.name}
                        </button>
                      ))}
                    </div>
                    <div className="sticker-grid">
                      {STICKER_PACKS[activeStickerCategory].stickers.map(sticker => (
                        <div
                          key={sticker.id}
                          className="sticker-picker-card"
                          onClick={() => handleSendSticker(sticker)}
                          style={{ borderColor: sticker.color }}
                        >
                          <span className="sticker-icon">{sticker.icon}</span>
                          <span className="sticker-title" style={{ color: sticker.color }}>
                            {sticker.title}
                          </span>
                          <span className="sticker-subtitle">{sticker.subtitle}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* ACTIVE VOICE RECORDING BAR */}
                {isRecording ? (
                  <div className="voice-recording-bar">
                    <div className="recording-indicator">
                      <div className="recording-pulsing-dot" />
                      <span className="recording-time">Recording: {Math.floor(recordingSeconds / 60)}:{(recordingSeconds % 60).toString().padStart(2, '0')}</span>
                    </div>
                    <div className="recording-controls">
                      <button 
                        type="button" 
                        className="btn-recording-cancel" 
                        onClick={cancelVoiceRecording}
                        title="Cancel recording"
                      >
                        <X size={18} /> Cancel
                      </button>
                      <button 
                        type="button" 
                        className="btn-recording-send" 
                        onClick={finishAndSendVoiceRecording}
                        title="Send voice message"
                      >
                        <Send size={16} /> Send Memo
                      </button>
                    </div>
                  </div>
                ) : (
                  /* NORMAL INPUT AREA */
                  <form onSubmit={sendMessage} className="message-input-area">
                    <input 
                      type="file" 
                      ref={fileInputRef} 
                      style={{ display: 'none' }} 
                      accept="image/*"
                      onChange={handleImageFileChange}
                    />

                    <button 
                      type="button" 
                      className={`chat-action-btn ${showEmojiPicker ? 'active' : ''}`}
                      onClick={() => {
                        setShowEmojiPicker(prev => !prev);
                        setShowStickerPicker(false);
                      }}
                      title="Insert Emoji"
                    >
                      <Smile size={19} strokeWidth={1.7} />
                    </button>

                    <button 
                      type="button" 
                      className={`chat-action-btn ${showStickerPicker ? 'active' : ''}`}
                      onClick={() => {
                        setShowStickerPicker(prev => !prev);
                        setShowEmojiPicker(false);
                      }}
                      title="Send MKC Sticker"
                    >
                      <Sparkles size={19} strokeWidth={1.7} />
                    </button>

                    <button 
                      type="button" 
                      className="chat-action-btn"
                      onClick={() => fileInputRef.current?.click()}
                      title="Attach Image"
                    >
                      <ImageIcon size={19} strokeWidth={1.7} />
                    </button>

                    <input 
                      type="text" 
                      placeholder="Type a message..." 
                      value={messageInput}
                      onChange={handleInputChange}
                    />

                    {messageInput.trim() ? (
                      <button type="submit" className="chat-send-btn" title="Send message">
                        <Send size={18} strokeWidth={1.8} />
                      </button>
                    ) : (
                      <button 
                        type="button" 
                        className="chat-mic-btn"
                        onClick={startVoiceRecording}
                        title="Record Voice Memo"
                      >
                        <Mic size={18} strokeWidth={1.8} />
                      </button>
                    )}
                  </form>
                )}
              </div>
            )}
          </div>
          
        </div>

      {/* LIGHTBOX MODAL FOR IMAGES */}
      {lightboxImage && (
        <div className="chat-lightbox-overlay" onClick={() => setLightboxImage(null)}>
          <div className="chat-lightbox-content" onClick={e => e.stopPropagation()}>
            <img src={getMediaUrl(lightboxImage)} alt="Enlarged preview" className="lightbox-img" />
            <button 
              type="button" 
              className="lightbox-close-btn" 
              onClick={() => setLightboxImage(null)}
              title="Close image"
            >
              <X size={20} />
            </button>
          </div>
        </div>
      )}

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
    </>
  );
};

export default Chat;
