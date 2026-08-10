const API_BASE_URL = 'http://localhost:8000';

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

export async function getDailyReflection() {
  const response = await apiFetch('/api/reflection/daily');
  if (!response.ok) {
    throw new Error(`Failed to fetch daily reflection: ${response.statusText}`);
  }
  return response.json();
}
