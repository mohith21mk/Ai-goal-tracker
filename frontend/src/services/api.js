const API_BASE_URL = 'http://localhost:8000';

export async function getUser() {
  const response = await fetch(`${API_BASE_URL}/api/users`);
  if (!response.ok) {
    throw new Error(`Failed to fetch user profile: ${response.statusText}`);
  }
  return response.json();
}

export async function getMissions() {
  const response = await fetch(`${API_BASE_URL}/api/missions`);
  if (!response.ok) {
    throw new Error(`Failed to fetch missions: ${response.statusText}`);
  }
  return response.json();
}

export async function createMission(data) {
  const response = await fetch(`${API_BASE_URL}/api/missions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to create mission: ${response.statusText}`);
  }
  return response.json();
}

export async function toggleMission(id) {
  const response = await fetch(`${API_BASE_URL}/api/missions/${id}/toggle`, {
    method: 'PATCH',
  });
  if (!response.ok) {
    throw new Error(`Failed to toggle mission: ${response.statusText}`);
  }
  return response.json();
}

export async function getProgress() {
  const response = await fetch(`${API_BASE_URL}/api/progress`);
  if (!response.ok) {
    throw new Error(`Failed to fetch progress telemetry: ${response.statusText}`);
  }
  return response.json();
}

export async function getTelemetry() {
  const response = await fetch(`${API_BASE_URL}/api/telemetry`);
  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard telemetry: ${response.statusText}`);
  }
  return response.json();
}

export async function getGoals() {
  const response = await fetch(`${API_BASE_URL}/api/goals`);
  if (!response.ok) {
    throw new Error(`Failed to fetch goals: ${response.statusText}`);
  }
  return response.json();
}

export async function createGoal(data) {
  const response = await fetch(`${API_BASE_URL}/api/goals`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to create goal: ${response.statusText}`);
  }
  return response.json();
}

export async function getGoal(id) {
  const response = await fetch(`${API_BASE_URL}/api/goals/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch goal: ${response.statusText}`);
  }
  return response.json();
}

export async function updateGoal(id, data) {
  const response = await fetch(`${API_BASE_URL}/api/goals/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update goal: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteGoal(id) {
  const response = await fetch(`${API_BASE_URL}/api/goals/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete goal: ${response.statusText}`);
  }
  return response.json();
}

export async function sendCoachMessage(prompt) {
  const response = await fetch(`${API_BASE_URL}/api/coach/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message: prompt }),
  });
  if (!response.ok) {
    throw new Error(`Failed to get coaching response: ${response.statusText}`);
  }
  return response.json();
}

export async function getCoachHistory(limit = 50) {
  const response = await fetch(`${API_BASE_URL}/api/coach/history?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch chat history: ${response.statusText}`);
  }
  return response.json();
}

export async function clearCoachHistory() {
  const response = await fetch(`${API_BASE_URL}/api/coach/history`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to clear chat history: ${response.statusText}`);
  }
  return response.json();
}

export async function getHabits() {
  const response = await fetch(`${API_BASE_URL}/api/habits`);
  if (!response.ok) {
    throw new Error(`Failed to fetch habits: ${response.statusText}`);
  }
  return response.json();
}

export async function getHabitStats() {
  const response = await fetch(`${API_BASE_URL}/api/habits/stats`);
  if (!response.ok) {
    throw new Error(`Failed to fetch habit stats: ${response.statusText}`);
  }
  return response.json();
}

export async function createHabit(data) {
  const response = await fetch(`${API_BASE_URL}/api/habits`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to create habit: ${response.statusText}`);
  }
  return response.json();
}

export async function updateHabit(id, data) {
  const response = await fetch(`${API_BASE_URL}/api/habits/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update habit: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteHabit(id) {
  const response = await fetch(`${API_BASE_URL}/api/habits/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete habit: ${response.statusText}`);
  }
  return response.json();
}

export async function toggleHabit(id, dateStr) {
  const response = await fetch(`${API_BASE_URL}/api/habits/${id}/toggle`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ date: dateStr }),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to toggle habit: ${response.statusText}`);
  }
  return response.json();
}

export async function getTodayJournal() {
  const response = await fetch(`${API_BASE_URL}/api/journal/today`);
  if (!response.ok) {
    throw new Error(`Failed to fetch today's journal: ${response.statusText}`);
  }
  return response.json();
}

export async function saveJournalEntry(data) {
  const response = await fetch(`${API_BASE_URL}/api/journal`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to save journal entry: ${response.statusText}`);
  }
  return response.json();
}

export async function getJournalHistory(limit = 30) {
  const response = await fetch(`${API_BASE_URL}/api/journal/history?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch journal history: ${response.statusText}`);
  }
  return response.json();
}

export async function getJournalStats() {
  const response = await fetch(`${API_BASE_URL}/api/journal/stats`);
  if (!response.ok) {
    throw new Error(`Failed to fetch journal stats: ${response.statusText}`);
  }
  return response.json();
}

export async function analyzeJournalEntry(id) {
  const response = await fetch(`${API_BASE_URL}/api/journal/${id}/analyze`, {
    method: 'POST',
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to analyze journal entry: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteJournalEntry(id) {
  const response = await fetch(`${API_BASE_URL}/api/journal/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete journal entry: ${response.statusText}`);
  }
  return response.json();
}

export async function getBlueprints() {
  const response = await fetch(`${API_BASE_URL}/api/blueprints`);
  if (!response.ok) {
    throw new Error(`Failed to fetch blueprints: ${response.statusText}`);
  }
  return response.json();
}

export async function getActiveBlueprint() {
  const response = await fetch(`${API_BASE_URL}/api/blueprints/active`);
  if (!response.ok) {
    throw new Error(`Failed to fetch active blueprint: ${response.statusText}`);
  }
  return response.json();
}

export async function getBlueprint(id) {
  const response = await fetch(`${API_BASE_URL}/api/blueprints/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch blueprint details: ${response.statusText}`);
  }
  return response.json();
}

export async function createBlueprint(data) {
  const response = await fetch(`${API_BASE_URL}/api/blueprints`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to create blueprint: ${response.statusText}`);
  }
  return response.json();
}

export async function updateBlueprint(id, data) {
  const response = await fetch(`${API_BASE_URL}/api/blueprints/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update blueprint: ${response.statusText}`);
  }
  return response.json();
}

export async function activateBlueprint(id) {
  const response = await fetch(`${API_BASE_URL}/api/blueprints/${id}/activate`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to activate blueprint: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteBlueprint(id) {
  const response = await fetch(`${API_BASE_URL}/api/blueprints/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete blueprint: ${response.statusText}`);
  }
  return response.json();
}

export async function createBlueprintPhase(blueprintId, data) {
  const response = await fetch(`${API_BASE_URL}/api/blueprints/${blueprintId}/phases`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to create phase: ${response.statusText}`);
  }
  return response.json();
}

export async function updateBlueprintPhase(phaseId, data) {
  const response = await fetch(`${API_BASE_URL}/api/blueprints/phases/${phaseId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update phase: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteBlueprintPhase(phaseId) {
  const response = await fetch(`${API_BASE_URL}/api/blueprints/phases/${phaseId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete phase: ${response.statusText}`);
  }
  return response.json();
}

export async function createBlueprintMilestone(phaseId, data) {
  const response = await fetch(`${API_BASE_URL}/api/blueprints/phases/${phaseId}/milestones`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to create milestone: ${response.statusText}`);
  }
  return response.json();
}

export async function toggleBlueprintMilestone(milestoneId) {
  const response = await fetch(`${API_BASE_URL}/api/blueprints/milestones/${milestoneId}/toggle`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to toggle milestone: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteBlueprintMilestone(milestoneId) {
  const response = await fetch(`${API_BASE_URL}/api/blueprints/milestones/${milestoneId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete milestone: ${response.statusText}`);
  }
  return response.json();
}

export async function searchApplication(query) {
  const encoded = encodeURIComponent(query);
  const response = await fetch(`${API_BASE_URL}/api/search?q=${encoded}`);
  if (!response.ok) {
    throw new Error(`Failed to execute search: ${response.statusText}`);
  }
  return response.json();
}

export async function getSettings() {
  const response = await fetch(`${API_BASE_URL}/api/settings`);
  if (!response.ok) {
    throw new Error(`Failed to fetch settings: ${response.statusText}`);
  }
  return response.json();
}

export async function updateSettings(data) {
  const response = await fetch(`${API_BASE_URL}/api/settings`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to update settings: ${response.statusText}`);
  }
  return response.json();
}

export async function getCommunityPosts(category) {
  const url = category ? `${API_BASE_URL}/api/community/posts?category=${encodeURIComponent(category)}` : `${API_BASE_URL}/api/community/posts`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch community posts: ${response.statusText}`);
  }
  return response.json();
}

export async function createCommunityPost(data) {
  const response = await fetch(`${API_BASE_URL}/api/community/posts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to create community post: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteCommunityPost(id) {
  const response = await fetch(`${API_BASE_URL}/api/community/posts/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete community post: ${response.statusText}`);
  }
  return response.json();
}

export async function toggleCommunityLike(id) {
  const response = await fetch(`${API_BASE_URL}/api/community/posts/${id}/like`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to toggle post like: ${response.statusText}`);
  }
  return response.json();
}

export async function getCommunityComments(id) {
  const response = await fetch(`${API_BASE_URL}/api/community/posts/${id}/comments`);
  if (!response.ok) {
    throw new Error(`Failed to fetch post comments: ${response.statusText}`);
  }
  return response.json();
}

export async function createCommunityComment(id, data) {
  const response = await fetch(`${API_BASE_URL}/api/community/posts/${id}/comments`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || `Failed to add comment: ${response.statusText}`);
  }
  return response.json();
}
