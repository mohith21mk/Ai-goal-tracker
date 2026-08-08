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
