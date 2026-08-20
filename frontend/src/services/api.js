const defaultApiUrl = import.meta.env.PROD 
  ? 'https://mkc-backend-iguj.onrender.com' 
  : 'http://localhost:8000';
const rawApiUrl = import.meta.env.VITE_API_URL || defaultApiUrl;
const API_BASE_URL = rawApiUrl.replace(/\/+$/, '');

async function apiFetch(endpoint, options = {}) {
  const defaultHeaders = options.body ? { 'Content-Type': 'application/json' } : {};
  const config = {
    credentials: 'include',
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };
  return fetch(`${API_BASE_URL}${endpoint}`, config);
}

// -------------------------------------------------------------------
// AUTHENTICATION APIs
// -------------------------------------------------------------------

export async function checkUsernameAvailability(username) {
  const response = await apiFetch(`/api/auth/check-username?username=${encodeURIComponent(username)}`);
  if (!response.ok) {
    return { available: false, username, reason: 'Failed to validate username' };
  }
  return response.json();
}

export async function registerUser(data) {
  const response = await apiFetch('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || 'Registration failed.');
  }
  return response.json();
}

export async function loginUser(data) {
  const response = await apiFetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || 'Invalid username/email or password.');
  }
  return response.json();
}

export async function logoutUser() {
  const response = await apiFetch('/api/auth/logout', {
    method: 'POST',
  });
  return response.json();
}

export async function getCurrentUser() {
  const response = await apiFetch('/api/auth/me');
  if (!response.ok) {
    return null;
  }
  return response.json();
}

export async function forgotPassword(identifier) {
  const response = await apiFetch('/api/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ identifier }),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || 'Password reset request failed.');
  }
  return response.json();
}

export async function resetPassword(token, newPassword) {
  const response = await apiFetch('/api/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || 'Password reset failed.');
  }
  return response.json();
}

export async function verifyEmail(token) {
  const response = await apiFetch('/api/auth/verify-email', {
    method: 'POST',
    body: JSON.stringify({ token }),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || 'Email verification failed.');
  }
  return response.json();
}

export async function resendVerification() {
  const response = await apiFetch('/api/auth/resend-verification', {
    method: 'POST',
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || 'Failed to resend verification link.');
  }
  return response.json();
}

export async function changePassword(currentPassword, newPassword) {
  const response = await apiFetch('/api/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || 'Failed to change password.');
  }
  return response.json();
}

export async function getActiveSessions() {
  const response = await apiFetch('/api/auth/sessions');
  if (!response.ok) {
    throw new Error(`Failed to fetch sessions: ${response.statusText}`);
  }
  return response.json();
}

export async function revokeSession(sessionId) {
  const response = await apiFetch(`/api/auth/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || 'Failed to revoke session.');
  }
  return response.json();
}

export async function revokeOtherSessions() {
  const response = await apiFetch('/api/auth/sessions/revoke-others', {
    method: 'POST',
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || 'Failed to revoke other sessions.');
  }
  return response.json();
}

export async function deactivateAccount() {
  const response = await apiFetch('/api/auth/deactivate', {
    method: 'POST',
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || 'Failed to deactivate account.');
  }
  return response.json();
}

export async function deleteAccount(currentPassword, confirmationText) {
  const response = await apiFetch('/api/users/account', {
    method: 'DELETE',
    body: JSON.stringify({
      current_password: currentPassword,
      confirmation_text: confirmationText,
    }),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || 'Failed to delete account.');
  }
  return response.json();
}

export async function submitOnboarding(data) {
  const response = await apiFetch('/api/users/onboarding', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || 'Failed to submit onboarding.');
  }
  return response.json();
}

// -------------------------------------------------------------------
// USER & TELEMETRY APIs
// -------------------------------------------------------------------

export async function getUser() {
  const response = await apiFetch('/api/users');
  if (!response.ok) {
    throw new Error(`Failed to fetch user profile: ${response.statusText}`);
  }
  return response.json();
}

export async function getPublicUserProfile(userId) {
  const response = await apiFetch(`/api/users/${userId}`);
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to fetch profile: ${response.statusText}`);
  }
  return response.json();
}

export async function updateUser(data) {
  const response = await apiFetch('/api/users', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to update user profile: ${response.statusText}`);
  }
  return response.json();
}

export async function getMissions() {
  const response = await apiFetch('/api/missions');
  if (!response.ok) {
    throw new Error(`Failed to fetch missions: ${response.statusText}`);
  }
  return response.json();
}

export async function createMission(data) {
  const response = await apiFetch('/api/missions', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to create mission: ${response.statusText}`);
  }
  return response.json();
}

export async function toggleMission(id) {
  const response = await apiFetch(`/api/missions/${id}/toggle`, {
    method: 'PATCH',
  });
  if (!response.ok) {
    throw new Error(`Failed to toggle mission: ${response.statusText}`);
  }
  return response.json();
}

export async function getProgress() {
  const response = await apiFetch('/api/progress');
  if (!response.ok) {
    throw new Error(`Failed to fetch progress telemetry: ${response.statusText}`);
  }
  return response.json();
}

export async function getTelemetry() {
  const response = await apiFetch('/api/telemetry');
  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard telemetry: ${response.statusText}`);
  }
  return response.json();
}

export async function getGoals() {
  const response = await apiFetch('/api/goals');
  if (!response.ok) {
    throw new Error(`Failed to fetch goals: ${response.statusText}`);
  }
  return response.json();
}

export async function createGoal(data) {
  const response = await apiFetch('/api/goals', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to create goal: ${response.statusText}`);
  }
  return response.json();
}

export async function updateGoal(id, data) {
  const response = await apiFetch(`/api/goals/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update goal: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteGoal(id) {
  const response = await apiFetch(`/api/goals/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete goal: ${response.statusText}`);
  }
  return response.json();
}

export async function sendAICoachMessage(message) {
  const response = await apiFetch('/api/coach/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `AI Coach error: ${response.statusText}`);
  }
  return response.json();
}
export const sendCoachMessage = sendAICoachMessage;

export async function getAICoachHistory() {
  const response = await apiFetch('/api/coach/history');
  if (!response.ok) {
    throw new Error(`Failed to fetch chat history: ${response.statusText}`);
  }
  return response.json();
}
export const getCoachHistory = getAICoachHistory;

export async function clearAICoachHistory() {
  const response = await apiFetch('/api/coach/history', {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to clear chat history: ${response.statusText}`);
  }
  return response.json();
}
export const clearCoachHistory = clearAICoachHistory;

export async function getHabits() {
  const response = await apiFetch('/api/habits');
  if (!response.ok) {
    throw new Error(`Failed to fetch habits: ${response.statusText}`);
  }
  return response.json();
}

export async function getHabitStats() {
  const response = await apiFetch('/api/habits/stats');
  if (!response.ok) {
    throw new Error(`Failed to fetch habit stats: ${response.statusText}`);
  }
  return response.json();
}

export async function createHabit(data) {
  const response = await apiFetch('/api/habits', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to create habit: ${response.statusText}`);
  }
  return response.json();
}

export async function updateHabit(id, data) {
  const response = await apiFetch(`/api/habits/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to update habit: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteHabit(id) {
  const response = await apiFetch(`/api/habits/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete habit: ${response.statusText}`);
  }
  return response.json();
}

export async function toggleHabit(id, dateStr) {
  const response = await apiFetch(`/api/habits/${id}/toggle`, {
    method: 'POST',
    body: JSON.stringify({ date: dateStr }),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to toggle habit: ${response.statusText}`);
  }
  return response.json();
}

export async function getTodayJournal() {
  const response = await apiFetch('/api/journal/today');
  if (!response.ok) {
    throw new Error(`Failed to fetch today journal: ${response.statusText}`);
  }
  return response.json();
}

export async function getJournalHistory(limit = 30) {
  const response = await apiFetch(`/api/journal/history?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch journal history: ${response.statusText}`);
  }
  return response.json();
}

export async function getJournalStats() {
  const response = await apiFetch('/api/journal/stats');
  if (!response.ok) {
    throw new Error(`Failed to fetch journal stats: ${response.statusText}`);
  }
  return response.json();
}

export async function saveJournal(data) {
  const response = await apiFetch('/api/journal', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to save journal: ${response.statusText}`);
  }
  return response.json();
}
export const saveJournalEntry = saveJournal;

export async function analyzeJournal(entryId) {
  const response = await apiFetch(`/api/journal/${entryId}/analyze`, {
    method: 'POST',
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to analyze journal: ${response.statusText}`);
  }
  return response.json();
}
export const analyzeJournalEntry = analyzeJournal;

export async function deleteJournal(entryId) {
  const response = await apiFetch(`/api/journal/${entryId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete journal entry: ${response.statusText}`);
  }
  return response.json();
}
export const deleteJournalEntry = deleteJournal;

export async function getActiveBlueprint() {
  const response = await apiFetch('/api/blueprints/active');
  if (!response.ok) {
    throw new Error(`Failed to fetch active blueprint: ${response.statusText}`);
  }
  return response.json();
}

export async function getAllBlueprints() {
  const response = await apiFetch('/api/blueprints');
  if (!response.ok) {
    throw new Error(`Failed to fetch blueprints: ${response.statusText}`);
  }
  return response.json();
}

export async function getBlueprintById(id) {
  const response = await apiFetch(`/api/blueprints/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch blueprint ${id}: ${response.statusText}`);
  }
  return response.json();
}

export async function createBlueprint(data) {
  const response = await apiFetch('/api/blueprints', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to create blueprint: ${response.statusText}`);
  }
  return response.json();
}

export async function updateBlueprint(id, data) {
  const response = await apiFetch(`/api/blueprints/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to update blueprint: ${response.statusText}`);
  }
  return response.json();
}

export async function activateBlueprint(id) {
  const response = await apiFetch(`/api/blueprints/${id}/activate`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to activate blueprint ${id}: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteBlueprint(id) {
  const response = await apiFetch(`/api/blueprints/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete blueprint ${id}: ${response.statusText}`);
  }
  return response.json();
}

export async function createPhase(blueprintId, data) {
  const response = await apiFetch(`/api/blueprints/${blueprintId}/phases`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to add phase: ${response.statusText}`);
  }
  return response.json();
}
export const createBlueprintPhase = createPhase;

export async function updatePhase(phaseId, data) {
  const response = await apiFetch(`/api/blueprints/phases/${phaseId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to update phase: ${response.statusText}`);
  }
  return response.json();
}

export async function deletePhase(phaseId) {
  const response = await apiFetch(`/api/blueprints/phases/${phaseId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete phase: ${response.statusText}`);
  }
  return response.json();
}
export const deleteBlueprintPhase = deletePhase;

export async function createMilestone(phaseId, data) {
  const response = await apiFetch(`/api/blueprints/phases/${phaseId}/milestones`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to add milestone: ${response.statusText}`);
  }
  return response.json();
}
export const createBlueprintMilestone = createMilestone;

export async function toggleMilestone(milestoneId) {
  const response = await apiFetch(`/api/blueprints/milestones/${milestoneId}/toggle`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to toggle milestone: ${response.statusText}`);
  }
  return response.json();
}
export const toggleBlueprintMilestone = toggleMilestone;

export async function deleteMilestone(milestoneId) {
  const response = await apiFetch(`/api/blueprints/milestones/${milestoneId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete milestone: ${response.statusText}`);
  }
  return response.json();
}
export const deleteBlueprintMilestone = deleteMilestone;

export async function searchApplication(query) {
  const response = await apiFetch(`/api/search?q=${encodeURIComponent(query)}`);
  if (!response.ok) {
    throw new Error(`Search failed: ${response.statusText}`);
  }
  return response.json();
}

export async function getSettings() {
  const response = await apiFetch('/api/settings');
  if (!response.ok) {
    throw new Error(`Failed to fetch settings: ${response.statusText}`);
  }
  return response.json();
}

export async function updateSettings(data) {
  const response = await apiFetch('/api/settings', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to update settings: ${response.statusText}`);
  }
  return response.json();
}

export async function getCommunityPosts(category = 'all') {
  const response = await apiFetch(`/api/community/posts?category=${category}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch community posts: ${response.statusText}`);
  }
  return response.json();
}

export async function createCommunityPost(data) {
  const response = await apiFetch('/api/community/posts', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to create post: ${response.statusText}`);
  }
  return response.json();
}

export async function updateCommunityPost(id, data) {
  const response = await apiFetch(`/api/community/posts/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to update post: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteCommunityPost(id) {
  const response = await apiFetch(`/api/community/posts/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to delete post: ${response.statusText}`);
  }
  return response.json();
}

export async function toggleCommunityLike(id) {
  const response = await apiFetch(`/api/community/posts/${id}/like`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to toggle post like: ${response.statusText}`);
  }
  return response.json();
}

export async function unlikeCommunityPost(id) {
  const response = await apiFetch(`/api/community/posts/${id}/like`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to unlike post: ${response.statusText}`);
  }
  return response.json();
}

export async function getCommunityComments(id) {
  const response = await apiFetch(`/api/community/posts/${id}/comments`);
  if (!response.ok) {
    throw new Error(`Failed to fetch post comments: ${response.statusText}`);
  }
  return response.json();
}

export async function createCommunityComment(id, data) {
  const response = await apiFetch(`/api/community/posts/${id}/comments`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to add comment: ${response.statusText}`);
  }
  return response.json();
}

export async function updateCommunityComment(commentId, data) {
  const response = await apiFetch(`/api/community/comments/${commentId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to update comment: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteCommunityComment(commentId) {
  const response = await apiFetch(`/api/community/comments/${commentId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to delete comment: ${response.statusText}`);
  }
  return response.json();
}

export async function getDailyReflection() {
  const response = await apiFetch('/api/reflection/daily');
  if (!response.ok) {
    throw new Error(`Failed to fetch daily reflection: ${response.statusText}`);
  }
  return response.json();
}

// -------------------------------------------------------------------
// SOCIAL & CHAT APIs
// -------------------------------------------------------------------

export async function searchUsers(query) {
  const response = await apiFetch(`/api/social/search?q=${encodeURIComponent(query)}`);
  if (!response.ok) {
    throw new Error(`Search failed: ${response.statusText}`);
  }
  return response.json();
}

export async function getConnections() {
  const response = await apiFetch('/api/social/connections');
  if (!response.ok) {
    throw new Error(`Failed to fetch connections: ${response.statusText}`);
  }
  return response.json();
}

export async function requestConnection(userId) {
  const response = await apiFetch('/api/social/connections/request', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to request connection: ${response.statusText}`);
  }
  return response.json();
}

export async function acceptConnection(payloadOrUserId) {
  const body = typeof payloadOrUserId === 'object' && payloadOrUserId !== null
    ? payloadOrUserId
    : { user_id: payloadOrUserId };
  const response = await apiFetch('/api/social/connections/accept', {
    method: 'POST',
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to accept connection: ${response.statusText}`);
  }
  return response.json();
}

export async function rejectConnection(payloadOrUserId) {
  const body = typeof payloadOrUserId === 'object' && payloadOrUserId !== null
    ? payloadOrUserId
    : { user_id: payloadOrUserId };
  const response = await apiFetch('/api/social/connections/reject', {
    method: 'POST',
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to reject connection: ${response.statusText}`);
  }
  return response.json();
}

export async function searchPublicUsers(q) {
  const response = await apiFetch(`/api/users/search?q=${encodeURIComponent(q)}`);
  if (!response.ok) {
    throw new Error(`Failed to search users: ${response.statusText}`);
  }
  return response.json();
}

export async function createConversation(targetUserId) {
  const response = await apiFetch('/api/chat/conversations', {
    method: 'POST',
    body: JSON.stringify({ target_user_id: targetUserId }),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to create conversation: ${response.statusText}`);
  }
  return response.json();
}

export async function getConversations() {
  const response = await apiFetch('/api/chat/conversations');
  if (!response.ok) {
    throw new Error(`Failed to fetch conversations: ${response.statusText}`);
  }
  return response.json();
}

export async function getConversationMessages(conversationId) {
  const response = await apiFetch(`/api/chat/conversations/${conversationId}/messages`);
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to fetch messages: ${response.statusText}`);
  }
  return response.json();
}

export async function markConversationRead(conversationId) {
  const response = await apiFetch(`/api/chat/conversations/${conversationId}/read`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to mark conversation read: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteMessage(messageId) {
  const response = await apiFetch(`/api/chat/messages/${messageId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to delete message: ${response.statusText}`);
  }
  return response.json();
}

// -------------------------------------------------------------------
// NOTIFICATIONS APIs
// -------------------------------------------------------------------

export async function getNotifications(limit = 50, offset = 0) {
  const response = await apiFetch(`/api/notifications?limit=${limit}&offset=${offset}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch notifications: ${response.statusText}`);
  }
  return response.json();
}

export async function getUnreadNotificationCount() {
  const response = await apiFetch('/api/notifications/unread-count');
  if (!response.ok) {
    throw new Error(`Failed to fetch unread notification count: ${response.statusText}`);
  }
  return response.json();
}

export async function markNotificationRead(id) {
  const response = await apiFetch(`/api/notifications/${id}/read`, {
    method: 'PATCH',
  });
  if (!response.ok) {
    throw new Error(`Failed to mark notification as read: ${response.statusText}`);
  }
  return response.json();
}

export async function markAllNotificationsRead() {
  const response = await apiFetch('/api/notifications/read_all', {
    method: 'PATCH',
  });
  if (!response.ok) {
    throw new Error(`Failed to mark all notifications as read: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteNotification(id) {
  const response = await apiFetch(`/api/notifications/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete notification: ${response.statusText}`);
  }
  return response.json();
}

// -------------------------------------------------------------------
// PROGRESSION & CREDENTIALS APIs
// -------------------------------------------------------------------

export async function getProgression() {
  const response = await apiFetch('/api/progression');
  if (!response.ok) {
    throw new Error(`Failed to fetch progression: ${response.statusText}`);
  }
  return response.json();
}

export async function getCredentials() {
  const response = await apiFetch('/api/credentials');
  if (!response.ok) {
    throw new Error(`Failed to fetch credentials: ${response.statusText}`);
  }
  return response.json();
}

export async function getPublicCredentials(userId) {
  const response = await apiFetch(`/api/credentials/user/${userId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch user credentials: ${response.statusText}`);
  }
  return response.json();
}

export async function checkCredentials() {
  const response = await apiFetch('/api/credentials/check', {
    method: 'POST',
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to evaluate credentials: ${response.statusText}`);
  }
  return response.json();
}

export async function getVerifiedCredential(credentialId) {
  const response = await apiFetch(`/api/credentials/verify/${credentialId}`);
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to verify credential: ${response.statusText}`);
  }
  return response.json();
}

export async function submitFeedback(payload) {
  const response = await apiFetch('/api/feedback', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to submit feedback: ${response.statusText}`);
  }
  return response.json();
}

export async function getAdminFeedback(params = {}) {
  const query = new URLSearchParams();
  if (params.category) query.append('category', params.category);
  if (params.status) query.append('status', params.status);
  if (params.severity) query.append('severity', params.severity);
  if (params.limit) query.append('limit', params.limit);
  if (params.offset) query.append('offset', params.offset);

  const qs = query.toString() ? `?${query.toString()}` : '';
  const response = await apiFetch(`/api/admin/feedback${qs}`);
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to fetch admin feedback: ${response.statusText}`);
  }
  return response.json();
}

export async function getAdminFeedbackStats() {
  const response = await apiFetch('/api/admin/feedback/stats');
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to fetch feedback stats: ${response.statusText}`);
  }
  return response.json();
}

export async function updateAdminFeedback(id, payload) {
  const response = await apiFetch(`/api/admin/feedback/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to update feedback: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteAdminFeedback(id) {
  const response = await apiFetch(`/api/admin/feedback/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to delete feedback: ${response.statusText}`);
  }
  return response.json();
}



