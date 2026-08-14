import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Globe,
  MessageSquare,
  MessageCircle,
  Trophy,
  Brain,
  HelpCircle,
  TriangleAlert,
  Heart,
  Trash2,
  Award
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import VictoryCredentialCard from '../components/VictoryCredentialCard';
import CertificateModal from '../components/CertificateModal';
import {
  getCommunityPosts,
  createCommunityPost,
  deleteCommunityPost,
  toggleCommunityLike,
  getCommunityComments,
  createCommunityComment,
  deleteCommunityComment,
  createConversation,
  getUser,
  getCredentials
} from '../services/api';
import './Community.css';

const CATEGORIES = [
  { id: 'all', label: 'All Feeds', icon: Globe },
  { id: 'general', label: 'General', icon: MessageSquare },
  { id: 'wins', label: 'Victory Wins', icon: Trophy },
  { id: 'mindset', label: 'Mindset Insights', icon: Brain },
  { id: 'questions', label: 'Q&A Discussions', icon: HelpCircle },
];

const Community = () => {
  const navigate = useNavigate();
  const [posts, setPosts] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [newPostContent, setNewPostContent] = useState('');
  const [newPostCategory, setNewPostCategory] = useState('general');
  const [selectedCredentialId, setSelectedCredentialId] = useState(null);
  const [userCredentials, setUserCredentials] = useState([]);
  const [certModalData, setCertModalData] = useState(null);
  const [currentUserId, setCurrentUserId] = useState(1);

  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState(null);

  // Active expanded comments map: { [postId]: { comments: [], loading: false, open: true, input: '' } }
  const [commentsState, setCommentsState] = useState({});

  const handleMessageAuthor = async (targetUserId) => {
    if (!targetUserId || targetUserId === currentUserId) return;
    try {
      await createConversation(targetUserId);
      navigate('/messages');
    } catch (err) {
      const msg = err.message || '';
      if (msg.includes('connected') || msg.includes('403')) {
        alert('Send a connection request to message this user.');
      } else {
        console.error('Failed to open chat:', err);
        alert('Could not start conversation. Please try again.');
      }
    }
  };

  const isMountedRef = useRef(true);

  const loadPosts = async (cat = selectedCategory) => {
    try {
      const data = await getCommunityPosts(cat === 'all' ? null : cat);
      if (!isMountedRef.current) return;
      if (Array.isArray(data)) {
        setPosts(data);
      }
      setError(null);
    } catch (err) {
      if (!isMountedRef.current) return;
      console.error('Failed to fetch community posts:', err);
      setError('Could not connect to community network.');
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    isMountedRef.current = true;
    async function init() {
      try {
        const [u, pData, creds] = await Promise.all([
          getUser().catch(() => ({ id: 1 })),
          getCommunityPosts(null).catch(() => []),
          getCredentials().catch(() => [])
        ]);

        if (isMountedRef.current) {
          if (u && u.id) {
            setCurrentUserId(u.id);
          }
          if (Array.isArray(pData)) setPosts(pData);
          if (Array.isArray(creds)) setUserCredentials(creds);
          setLoading(false);
        }
      } catch (err) {
        if (isMountedRef.current) {
          console.error('Failed community init:', err);
          setError('Could not connect to community network.');
          setLoading(false);
        }
      }
    }
    init();
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const handleCategoryChange = (catId) => {
    setSelectedCategory(catId);
    setLoading(true);
    loadPosts(catId);
  };

  const handleCreatePost = async (e) => {
    e.preventDefault();
    if (!newPostContent.trim() || publishing) return;

    setPublishing(true);
    try {
      await createCommunityPost({
        content: newPostContent.trim(),
        category: newPostCategory,
        credential_id: newPostCategory === 'wins' ? selectedCredentialId : null
      });

      setNewPostContent('');
      setSelectedCredentialId(null);
      await loadPosts(selectedCategory);
    } catch (err) {
      alert(err.message || 'Failed to publish post.');
    } finally {
      setPublishing(false);
    }
  };

  const handleDeletePost = async (postId) => {
    if (!window.confirm('Are you sure you want to delete this post?')) return;

    setPosts(prev => prev.filter(p => p.id !== postId));
    try {
      await deleteCommunityPost(postId);
    } catch (err) {
      alert(err.message || 'Failed to delete post.');
      await loadPosts(selectedCategory);
    }
  };

  const handleToggleLike = async (postId) => {
    // Optimistic toggle
    setPosts(prev => prev.map(p => {
      if (p.id === postId) {
        const nextLiked = !p.user_has_liked;
        return {
          ...p,
          user_has_liked: nextLiked,
          likes_count: nextLiked ? p.likes_count + 1 : Math.max(0, p.likes_count - 1)
        };
      }
      return p;
    }));

    try {
      const res = await toggleCommunityLike(postId);
      setPosts(prev => prev.map(p => {
        if (p.id === postId) {
          return {
            ...p,
            user_has_liked: res.user_has_liked,
            likes_count: res.likes_count
          };
        }
        return p;
      }));
    } catch (err) {
      console.error('Failed to toggle like:', err);
    }
  };

  const handleToggleCommentsThread = async (postId) => {
    const currentState = commentsState[postId];
    const isOpen = currentState?.open;

    if (isOpen) {
      setCommentsState(prev => ({
        ...prev,
        [postId]: { ...prev[postId], open: false }
      }));
      return;
    }

    setCommentsState(prev => ({
      ...prev,
      [postId]: { comments: [], loading: true, open: true, input: '' }
    }));

    try {
      const cList = await getCommunityComments(postId);
      setCommentsState(prev => ({
        ...prev,
        [postId]: { comments: cList || [], loading: false, open: true, input: '' }
      }));
    } catch (err) {
      console.error('Failed to fetch comments:', err);
      setCommentsState(prev => ({
        ...prev,
        [postId]: { comments: [], loading: false, open: true, input: '' }
      }));
    }
  };

  const handleAddComment = async (e, postId) => {
    e.preventDefault();
    const commentInput = commentsState[postId]?.input?.trim();
    if (!commentInput) return;

    try {
      const newComment = await createCommunityComment(postId, { content: commentInput });
      setCommentsState(prev => ({
        ...prev,
        [postId]: {
          ...prev[postId],
          comments: [...(prev[postId]?.comments || []), newComment],
          input: ''
        }
      }));

      setPosts(prev => prev.map(p => p.id === postId ? { ...p, comments_count: (p.comments_count || 0) + 1 } : p));
    } catch (err) {
      console.error('Failed to add comment:', err);
    }
  };

  const handleDeleteComment = async (postId, commentId) => {
    try {
      await deleteCommunityComment(commentId);
      setCommentsState(prev => ({
        ...prev,
        [postId]: {
          ...prev[postId],
          comments: (prev[postId]?.comments || []).filter(c => c.id !== commentId)
        }
      }));
      setPosts(prev => prev.map(p => p.id === postId ? { ...p, comments_count: Math.max(0, (p.comments_count || 1) - 1) } : p));
    } catch (err) {
      console.error('Failed to delete comment:', err);
    }
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-viewport">
        <TopBar />
        <div className="community-container">
          {/* Header */}
          <div className="community-header">
            <div className="community-header-left">
              <h1 className="font-serif">Mastery Key Network</h1>
              <p>Share victories, mindset insights, and collaborate with high-performance peers.</p>
            </div>
          </div>

          {error && (
            <div style={{ padding: '12px 16px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #EF4444', borderRadius: '12px', color: '#EF4444', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <TriangleAlert size={16} /> {error}
            </div>
          )}

          {/* Create Post Card */}
          <div className="community-create-card glass-panel">
            <form onSubmit={handleCreatePost}>
              <textarea
                placeholder="Share a milestone victory, mindset breakthrough, or technical question..."
                value={newPostContent}
                onChange={(e) => setNewPostContent(e.target.value)}
                className="community-textarea"
                required
              />
              {/* Category selector & Attachments */}
              <div className="community-create-actions">
                <select
                  value={newPostCategory}
                  onChange={(e) => {
                    setNewPostCategory(e.target.value);
                    if (e.target.value !== 'wins') setSelectedCredentialId(null);
                  }}
                  className="community-category-select"
                >
                  <option value="general">General</option>
                  <option value="wins">Victory Wins</option>
                  <option value="mindset">Mindset Insights</option>
                  <option value="questions">Q&A Discussions</option>
                </select>

                <button
                  type="submit"
                  disabled={publishing || !newPostContent.trim()}
                  className="btn-publish-post"
                >
                  {publishing ? 'Publishing...' : 'Publish Post →'}
                </button>
              </div>

              {/* Credential Attachment Picker for Victory Wins */}
              {newPostCategory === 'wins' && (
                <div className="community-credential-picker">
                  <div className="credential-picker-header">
                    <Award size={14} style={{ color: 'var(--cyan)' }} />
                    <span>Attach Verified Achievement (Optional):</span>
                  </div>
                  {userCredentials.length === 0 ? (
                    <span className="no-credentials-hint">No verified credentials earned yet. You can still share your win!</span>
                  ) : (
                    <div className="credential-picker-chips">
                      {userCredentials.map(cred => {
                        const isSelected = selectedCredentialId === cred.id;
                        return (
                          <VictoryCredentialCard
                            key={cred.id || cred.slug}
                            credential={cred}
                            compact={true}
                            interactive={true}
                            selected={isSelected}
                            onClick={() => setSelectedCredentialId(isSelected ? null : cred.id)}
                          />
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </form>
          </div>

          {/* Category Filter Tabs */}
          <div className="community-filter-bar">
            {CATEGORIES.map((cat) => {
              const Icon = cat.icon;
              return (
                <button
                  key={cat.id}
                  onClick={() => handleCategoryChange(cat.id)}
                  className={`community-filter-btn ${selectedCategory === cat.id ? 'active' : ''}`}
                >
                  <span><Icon size={16} /></span>
                  <span>{cat.label}</span>
                </button>
              );
            })}
          </div>

          {/* Posts Feed */}
          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-tertiary)' }}>Syncing Community Network Feed...</div>
          ) : posts.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', background: 'var(--card-bg)', borderRadius: '16px', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)' }}>
              No community posts found in this feed. Be the first to publish your breakthrough above!
            </div>
          ) : (
            <div className="community-feed">
              {posts.map((post) => {
                const cState = commentsState[post.id];
                const isOwned = post.user_id === currentUserId;

                return (
                  <div key={post.id} className="post-card glass-panel">
                    <div className="post-header">
                      <div className="post-author-info">
                        <div className="post-author-avatar">
                          {post.author_name ? post.author_name.charAt(0).toUpperCase() : 'M'}
                        </div>
                        <div>
                          <div className="post-author-name">{post.author_name}</div>
                          <div className="post-time">{post.created_at || 'Just now'}</div>
                        </div>
                      </div>
                      <span className="post-category-pill">{post.category || 'general'}</span>
                    </div>

                    <div className="post-body">{post.content}</div>

                    {/* Attached Verified Credential Badge */}
                    {post.credential && (
                      <div className="post-credential-attachment">
                        <VictoryCredentialCard
                          credential={post.credential}
                          userName={post.author_name}
                          interactive={true}
                          onClick={() => setCertModalData({
                            credential: post.credential,
                            user: { full_name: post.author_name }
                          })}
                        />
                      </div>
                    )}

                    <div className="post-footer">
                      <button
                        onClick={() => handleToggleLike(post.id)}
                        className={`post-action-btn ${post.user_has_liked ? 'liked' : ''}`}
                      >
                        <span>
                          <Heart
                            size={16}
                            fill={post.user_has_liked ? '#EF4444' : 'none'}
                            color={post.user_has_liked ? '#EF4444' : 'currentColor'}
                          />
                        </span>
                        <span>{post.likes_count ?? 0} Likes</span>
                      </button>

                      <button
                        onClick={() => handleToggleCommentsThread(post.id)}
                        className="post-action-btn"
                      >
                        <span><MessageSquare size={16} /></span>
                        <span>{post.comments_count ?? 0} Comments</span>
                      </button>

                      {!isOwned && (
                        <button
                          onClick={() => handleMessageAuthor(post.user_id)}
                          className="post-action-btn"
                          title="Message Author"
                        >
                          <span><MessageCircle size={16} /></span>
                          <span>Message</span>
                        </button>
                      )}

                      {isOwned && (
                        <button
                          onClick={() => handleDeletePost(post.id)}
                          className="btn-delete-post"
                          title="Delete post"
                        >
                          <Trash2 size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '4px' }} /> Delete
                        </button>
                      )}
                    </div>

                    {/* Expandable Comments Section */}
                    {cState?.open && (
                      <div className="comments-section">
                        {cState.loading ? (
                          <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>Loading comments...</div>
                        ) : cState.comments.length === 0 ? (
                          <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>No comments yet. Start the conversation!</div>
                        ) : (
                          cState.comments.map((c) => (
                            <div key={c.id} className="comment-item" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <div>
                                <div className="comment-author">{c.author_name}</div>
                                <div className="comment-text">{c.content}</div>
                              </div>
                              {c.user_id === currentUserId && (
                                <button
                                  onClick={() => handleDeleteComment(post.id, c.id)}
                                  className="btn-delete-post"
                                  title="Delete comment"
                                  style={{ padding: '2px 6px', fontSize: '11px' }}
                                >
                                  <Trash2 size={12} />
                                </button>
                              )}
                            </div>
                          ))
                        )}

                        <form
                          onSubmit={(e) => handleAddComment(e, post.id)}
                          className="comment-form"
                        >
                          <input
                            type="text"
                            placeholder="Write a comment..."
                            value={cState.input || ''}
                            onChange={(e) => setCommentsState(prev => ({
                              ...prev,
                              [post.id]: { ...prev[post.id], input: e.target.value }
                            }))}
                            className="comment-input"
                          />
                          <button type="submit" className="btn-submit-comment">Comment</button>
                        </form>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {certModalData && (
        <CertificateModal
          credential={certModalData.credential}
          user={certModalData.user}
          onClose={() => setCertModalData(null)}
        />
      )}
    </div>
  );
};

export default Community;
