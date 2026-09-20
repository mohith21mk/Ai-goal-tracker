/**
 * Automated Test Suite for Netlify Functions Backend
 * Mastery Key Coach (MKC)
 */

const { app } = require('../dist-functions/api');
const { setMockQueryHandler } = require('../dist-functions/src/db');
const { hashPassword, verifyPassword, validateUsername } = require('../dist-functions/src/utils/security');
const http = require('http');

let server;
let baseUrl;

// In-Memory Database Store for Testing
const dbStore = {
  users: [
    {
      id: 1,
      email: 'demo@masterykeycoach.com',
      username: 'mohith_ai',
      password_hash: 'pbkdf2_sha256$100000$7bd8e23af69c904aa5df7661fed76545$202db117259a1e81aa82c1a84bac9919073d3b3d3efaf50f34a5ec98c4dd6c7d',
      full_name: 'Mastery Key Coach Demo',
      role: 'admin',
      is_active: 1,
      mkc_id: 'MKC-2026-DEMO01',
      avatar_initials: 'MK',
      bio: 'Demo account',
      email_verified: 1,
      onboarding_completed: 1,
      created_at: new Date().toISOString(),
    },
    {
      id: 2,
      email: 'regular@test.com',
      username: 'regular_user',
      password_hash: hashPassword('TestPass123!'),
      full_name: 'Regular Tester',
      role: 'user',
      is_active: 1,
      mkc_id: 'MKC-2026-REG01',
      avatar_initials: 'RT',
      bio: 'Regular user',
      email_verified: 1,
      onboarding_completed: 1,
      created_at: new Date().toISOString(),
    },
  ],
  app_sessions: [],
  user_settings: [
    { user_id: 1, theme: 'dark', notifications_enabled: 1, coach_style: 'strategic', daily_reminder_time: '08:00', profile_visibility: 'public' },
    { user_id: 2, theme: 'light', notifications_enabled: 1, coach_style: 'tactical', daily_reminder_time: '09:00', profile_visibility: 'public' }
  ],
  missions: [
    { id: 101, user_id: 1, title: 'Morning Mindset Protocol', description: 'Morning mindfulness', category: 'mindset', time: '15 min', difficulty: 'easy', xp_reward: 15, completed: 0, goal_id: 1, created_at: new Date().toISOString() },
    { id: 102, user_id: 1, title: 'Deep Work Architecture Block', description: 'Core engineering session', category: 'productivity', time: '45 min', difficulty: 'medium', xp_reward: 25, completed: 0, goal_id: 1, created_at: new Date().toISOString() },
  ],
  mission_logs: [],
  habits: [
    { id: 201, user_id: 1, title: 'Cold Plunge / Cold Shower', description: 'Vagus nerve stimulation', category: 'wellness', frequency: 'daily', target_days_per_week: 7, status: 'active', created_at: new Date().toISOString() },
    { id: 202, user_id: 1, title: 'Daily Code Commit', description: 'GitHub activity', category: 'productivity', frequency: 'daily', target_days_per_week: 7, status: 'active', created_at: new Date().toISOString() },
  ],
  habit_logs: [],
  goals: [
    { id: 1, user_id: 1, title: 'AI Engineering Mastery', description: 'Become an industry-ready AI Engineer', category: 'career', status: 'active', target_date: '2028-06-30', created_at: new Date().toISOString() }
  ],
  journal_entries: [],
  user_credentials: [],
  community_posts: [],
  community_likes: [],
  community_comments: [],
  user_connections: [],
  user_follows: [],
  messages: [],
  notifications: [],
  feedback: []
};

// Setup Mock Query Engine
setMockQueryHandler(async (sql, params = []) => {
  const norm = sql.trim().replace(/\s+/g, ' ');
  const upper = norm.toUpperCase();

  // SELECT 1 as healthy
  if (upper.includes('SELECT 1 AS HEALTHY') || upper.includes('SELECT 1')) {
    return { rows: [{ healthy: 1 }], rowCount: 1 };
  }

  // Users lookup
  if (upper.includes('FROM USERS') && upper.includes('LOWER(EMAIL) =') && upper.includes('LOWER(USERNAME) =')) {
    const ident = (params[0] || '').toLowerCase();
    const rows = dbStore.users.filter(u => u.email.toLowerCase() === ident || u.username.toLowerCase() === ident);
    return { rows, rowCount: rows.length };
  }

  if (upper.includes('SELECT') && upper.includes('FROM USERS WHERE ID = $1')) {
    const uid = params[0];
    const rows = dbStore.users.filter(u => u.id === uid);
    return { rows, rowCount: rows.length };
  }

  if (upper.includes('SELECT ID, EMAIL, USERNAME FROM USERS WHERE LOWER(EMAIL) = $1 OR LOWER(USERNAME) = $2')) {
    const em = (params[0] || '').toLowerCase();
    const un = (params[1] || '').toLowerCase();
    const rows = dbStore.users.filter(u => u.email.toLowerCase() === em || u.username.toLowerCase() === un);
    return { rows, rowCount: rows.length };
  }

  // User insert
  if (upper.includes('INSERT INTO USERS')) {
    const newId = dbStore.users.length + 1;
    const user = {
      id: newId,
      email: params[0],
      full_name: params[1],
      username: params[2],
      password_hash: params[3],
      mkc_id: params[4],
      avatar_initials: params[5],
      bio: params[6],
      role: params[7],
      email_verified: params[8],
      onboarding_completed: params[9],
      created_at: new Date().toISOString(),
      is_active: 1
    };
    dbStore.users.push(user);
    return { rows: [user], rowCount: 1 };
  }

  // Sessions lookup & insert
  if (upper.includes('SELECT USER_ID, EXPIRES_AT, REVOKED_AT FROM APP_SESSIONS WHERE TOKEN = $1')) {
    const token = params[0];
    const rows = dbStore.app_sessions.filter(s => s.token === token);
    return { rows, rowCount: rows.length };
  }

  if (upper.includes('INSERT INTO APP_SESSIONS')) {
    const session = {
      token: params[0],
      user_id: params[1],
      expires_at: params[2],
      user_agent: params[3],
      ip_address: params[4],
      last_seen_at: new Date().toISOString(),
      revoked_at: null
    };
    dbStore.app_sessions.push(session);
    return { rows: [session], rowCount: 1 };
  }

  if (upper.includes('UPDATE APP_SESSIONS SET LAST_SEEN_AT')) {
    return { rows: [], rowCount: 1 };
  }

  if (upper.includes('UPDATE APP_SESSIONS SET REVOKED_AT')) {
    const token = params[0];
    const s = dbStore.app_sessions.find(x => x.token === token);
    if (s) s.revoked_at = new Date().toISOString();
    return { rows: [], rowCount: 1 };
  }

  // User settings
  if (upper.includes('FROM USER_SETTINGS WHERE USER_ID = $1')) {
    const rows = dbStore.user_settings.filter(s => s.user_id === params[0]);
    return { rows, rowCount: rows.length };
  }
  if (upper.includes('INSERT INTO USER_SETTINGS')) {
    const s = { user_id: params[0], theme: params[1], notifications_enabled: params[2], coach_style: params[3], daily_reminder_time: params[4], profile_visibility: params[5] };
    dbStore.user_settings.push(s);
    return { rows: [s], rowCount: 1 };
  }

  // Missions
  if (upper.includes('FROM MISSIONS WHERE USER_ID = $1')) {
    const rows = dbStore.missions.filter(m => m.user_id === params[0]);
    return { rows, rowCount: rows.length };
  }
  if (upper.includes('SELECT ID, XP_REWARD FROM MISSIONS WHERE ID = $1 AND USER_ID = $2')) {
    const rows = dbStore.missions.filter(m => m.id === params[0] && m.user_id === params[1]);
    return { rows, rowCount: rows.length };
  }
  if (upper.includes('INSERT INTO MISSIONS')) {
    const newId = 100 + dbStore.missions.length + 1;
    const m = { id: newId, title: params[0], description: params[1], category: params[2], time: params[3], difficulty: params[4], xp_reward: params[5], completed: 0, user_id: params[6], goal_id: params[7] };
    dbStore.missions.push(m);
    return { rows: [m], rowCount: 1 };
  }
  if (upper.includes('UPDATE MISSIONS SET COMPLETED')) {
    return { rows: [], rowCount: 1 };
  }

  // Mission logs
  if (upper.includes('FROM MISSION_LOGS WHERE USER_ID = $1 AND COMPLETED_DATE = $2')) {
    const rows = dbStore.mission_logs.filter(l => l.user_id === params[0] && l.completed_date === params[1]);
    return { rows, rowCount: rows.length };
  }
  if (upper.includes('FROM MISSION_LOGS WHERE USER_ID = $1 AND MISSION_ID = $2 AND COMPLETED_DATE = $3')) {
    const rows = dbStore.mission_logs.filter(l => l.user_id === params[0] && l.mission_id === params[1] && l.completed_date === params[2]);
    return { rows, rowCount: rows.length };
  }
  if (upper.includes('INSERT INTO MISSION_LOGS')) {
    const newId = dbStore.mission_logs.length + 1;
    const log = { id: newId, user_id: params[0], mission_id: params[1], completed_date: params[2], xp_reward: params[3] };
    dbStore.mission_logs.push(log);
    return { rows: [log], rowCount: 1 };
  }
  if (upper.includes('DELETE FROM MISSION_LOGS WHERE ID = $1')) {
    const idx = dbStore.mission_logs.findIndex(l => l.id === params[0]);
    if (idx !== -1) dbStore.mission_logs.splice(idx, 1);
    return { rows: [], rowCount: 1 };
  }
  if (upper.includes('FROM MISSION_LOGS WHERE USER_ID = $1')) {
    const rows = dbStore.mission_logs.filter(l => l.user_id === params[0]);
    return { rows, rowCount: rows.length };
  }

  // Habits
  if (upper.includes('FROM HABITS WHERE USER_ID = $1 AND STATUS = $2')) {
    const rows = dbStore.habits.filter(h => h.user_id === params[0] && h.status === params[1]);
    return { rows, rowCount: rows.length };
  }
  if (upper.includes('FROM HABITS WHERE USER_ID = $1')) {
    const rows = dbStore.habits.filter(h => h.user_id === params[0]);
    return { rows, rowCount: rows.length };
  }
  if (upper.includes('FROM HABITS WHERE ID = $1 AND USER_ID = $2')) {
    const rows = dbStore.habits.filter(h => h.id === params[0] && h.user_id === params[1]);
    return { rows, rowCount: rows.length };
  }
  if (upper.includes('INSERT INTO HABITS')) {
    const newId = 200 + dbStore.habits.length + 1;
    const h = { id: newId, user_id: params[0], title: params[1], description: params[2], category: params[3], frequency: params[4], target_days_per_week: params[5], status: 'active' };
    dbStore.habits.push(h);
    return { rows: [h], rowCount: 1 };
  }

  // Habit logs
  if (upper.includes('FROM HABIT_LOGS WHERE HABIT_ID = $1 AND COMPLETED_DATE = $2')) {
    const rows = dbStore.habit_logs.filter(l => l.habit_id === params[0] && l.completed_date === params[1]);
    return { rows, rowCount: rows.length };
  }
  if (upper.includes('FROM HABIT_LOGS WHERE USER_ID = $1')) {
    const rows = dbStore.habit_logs.filter(l => l.user_id === params[0]);
    return { rows, rowCount: rows.length };
  }
  if (upper.includes('INSERT INTO HABIT_LOGS')) {
    const newId = dbStore.habit_logs.length + 1;
    const log = { id: newId, habit_id: params[0], user_id: params[1], completed_date: params[2] };
    dbStore.habit_logs.push(log);
    return { rows: [log], rowCount: 1 };
  }
  if (upper.includes('DELETE FROM HABIT_LOGS WHERE ID = $1')) {
    const idx = dbStore.habit_logs.findIndex(l => l.id === params[0]);
    if (idx !== -1) dbStore.habit_logs.splice(idx, 1);
    return { rows: [], rowCount: 1 };
  }

  // Goals
  if (upper.includes('FROM GOALS WHERE USER_ID = $1')) {
    const rows = dbStore.goals.filter(g => g.user_id === params[0]);
    return { rows, rowCount: rows.length };
  }

  // Credentials
  if (upper.includes('FROM USER_CREDENTIALS WHERE USER_ID = $1')) {
    const rows = dbStore.user_credentials.filter(c => c.user_id === params[0]);
    return { rows, rowCount: rows.length };
  }

  // Messages
  if (upper.includes('INSERT INTO MESSAGES')) {
    const newId = dbStore.messages.length + 1;
    const m = { id: newId, user_id: params[0], sender: params[1], content: params[2], created_at: new Date().toISOString() };
    dbStore.messages.push(m);
    return { rows: [m], rowCount: 1 };
  }
  if (upper.includes('FROM MESSAGES WHERE USER_ID = $1')) {
    const rows = dbStore.messages.filter(m => m.user_id === params[0]);
    return { rows, rowCount: rows.length };
  }
  if (upper.includes('DELETE FROM MESSAGES WHERE USER_ID = $1')) {
    const prevLen = dbStore.messages.length;
    dbStore.messages = dbStore.messages.filter(m => m.user_id !== params[0]);
    return { rows: [], rowCount: prevLen - dbStore.messages.length };
  }

  // Admin overview counts
  if (upper.includes('SELECT COUNT(*) FROM USERS WHERE IS_ACTIVE = 1')) return { rows: [{ count: '2' }], rowCount: 1 };
  if (upper.includes('SELECT COUNT(*) FROM USERS')) return { rows: [{ count: '2' }], rowCount: 1 };
  if (upper.includes('SELECT COUNT(*) FROM MISSION_LOGS')) return { rows: [{ count: String(dbStore.mission_logs.length) }], rowCount: 1 };
  if (upper.includes('SELECT COUNT(*) FROM HABIT_LOGS')) return { rows: [{ count: String(dbStore.habit_logs.length) }], rowCount: 1 };
  if (upper.includes('SELECT COUNT(*) FROM FEEDBACK')) return { rows: [{ count: '0' }], rowCount: 1 };

  return { rows: [], rowCount: 0 };
});

// Helper for making HTTP requests
async function request(path, options = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, baseUrl);
    const reqOptions = {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    };

    const req = http.request(url, reqOptions, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        let json = null;
        try { json = JSON.parse(body); } catch {}
        resolve({
          status: res.statusCode,
          headers: res.headers,
          data: json,
          raw: body
        });
      });
    });

    req.on('error', reject);
    if (options.body) {
      req.write(typeof options.body === 'string' ? options.body : JSON.stringify(options.body));
    }
    req.end();
  });
}

// ----------------------------------------------------------------------------
// Test Runner
// ----------------------------------------------------------------------------
async function runTests() {
  console.log('===============================================================');
  console.log('STARTING NETLIFY FUNCTIONS BACKEND AUTOMATED VALIDATION SUITE');
  console.log('===============================================================');

  let passed = 0;
  let failed = 0;

  function assert(condition, message) {
    if (condition) {
      console.log(`  ✓ PASS: ${message}`);
      passed++;
    } else {
      console.error(`  ✗ FAIL: ${message}`);
      failed++;
    }
  }

  // 1. Password Hashing & Compatibility
  console.log('\n[1] Security & Password Verification:');
  const testHash = 'pbkdf2_sha256$100000$7bd8e23af69c904aa5df7661fed76545$202db117259a1e81aa82c1a84bac9919073d3b3d3efaf50f34a5ec98c4dd6c7d';
  assert(verifyPassword('Password123!', testHash), 'PBKDF2 verifies Password123! against Python hash');
  assert(!verifyPassword('WrongPassword', testHash), 'PBKDF2 rejects wrong password');
  const genHash = hashPassword('MySecurePass99!');
  assert(verifyPassword('MySecurePass99!', genHash), 'Generated PBKDF2 hash verifies with verifyPassword');

  // Username validation
  assert(validateUsername('mohith_ai').valid, 'Valid username accepted');
  assert(!validateUsername('admin').valid, 'Reserved username rejected');
  assert(!validateUsername('123abc').valid, 'Username starting with number rejected');

  // Start Express Test Server on ephemeral port
  server = app.listen(0);
  const port = server.address().port;
  baseUrl = `http://localhost:${port}`;
  console.log(`\nTest server listening at ${baseUrl}`);

  // 2. Health & Readiness Endpoints
  console.log('\n[2] Health & Readiness Endpoints:');
  const rHealth = await request('/health');
  assert(rHealth.status === 200 && rHealth.data.status === 'ok', 'GET /health returns 200 ok');

  const rApiHealth = await request('/api/health');
  assert(rApiHealth.status === 200 && rApiHealth.data.service.includes('Netlify Functions'), 'GET /api/health returns Netlify Functions identity');

  const rReady = await request('/ready');
  assert(rReady.status === 200 && rReady.data.database === 'connected', 'GET /ready verifies database connectivity');

  // 3. Authentication & Sessions
  console.log('\n[3] Authentication & Session Management:');
  // Login with invalid credentials
  const rBadLogin = await request('/api/auth/login', {
    method: 'POST',
    body: { email: 'demo@masterykeycoach.com', password: 'WrongPassword' }
  });
  assert(rBadLogin.status === 401, 'POST /api/auth/login rejects incorrect password with 401');

  // Login demo user
  const rLogin = await request('/api/auth/login', {
    method: 'POST',
    body: { email: 'demo@masterykeycoach.com', password: 'Password123!' }
  });
  assert(rLogin.status === 200 && rLogin.data.user.email === 'demo@masterykeycoach.com', 'POST /api/auth/login logs in demo user');

  const setCookie = rLogin.headers['set-cookie'];
  assert(setCookie && setCookie[0].includes('mkc_session='), 'POST /api/auth/login returns HttpOnly mkc_session cookie');

  const cookieHeader = setCookie ? setCookie[0].split(';')[0] : '';

  // Auth me with cookie
  const rMe = await request('/api/auth/me', {
    headers: { 'Cookie': cookieHeader }
  });
  assert(rMe.status === 200 && rMe.data.user.role === 'admin', 'GET /api/auth/me authenticates with session cookie and detects admin');

  // Auth check unauthorized
  const rMeNoAuth = await request('/api/auth/me');
  assert(rMeNoAuth.status === 401, 'GET /api/auth/me returns 401 when no session cookie is provided');

  // 4. Daily Mission Auto-Reset & Toggle Logic
  console.log('\n[4] Missions & Daily Auto-Reset Logic:');
  const rMissionsBefore = await request('/api/missions', { headers: { 'Cookie': cookieHeader } });
  assert(rMissionsBefore.status === 200 && rMissionsBefore.data.missions.length === 2, 'GET /api/missions returns 2 missions');
  assert(rMissionsBefore.data.missions[0].completed === 0, 'Mission 101 starts uncompleted today');

  // Toggle mission 101 -> completed for today
  const rToggle1 = await request('/api/missions/101/toggle', {
    method: 'POST',
    headers: { 'Cookie': cookieHeader }
  });
  assert(rToggle1.status === 200 && rToggle1.data.completed === 1, 'POST /api/missions/101/toggle marks mission completed for today');

  const rMissionsAfter = await request('/api/missions', { headers: { 'Cookie': cookieHeader } });
  assert(rMissionsAfter.data.missions[0].completed === 1, 'GET /api/missions now shows mission 101 as completed today');

  // Toggle mission 101 again -> uncompleted
  const rToggle2 = await request('/api/missions/101/toggle', {
    method: 'POST',
    headers: { 'Cookie': cookieHeader }
  });
  assert(rToggle2.status === 200 && rToggle2.data.completed === 0, 'Second toggle marks mission uncompleted for today');

  // Re-complete mission 101 for telemetry checks
  await request('/api/missions/101/toggle', { method: 'POST', headers: { 'Cookie': cookieHeader } });

  // 5. Habits & Habit Logs
  console.log('\n[5] Habits & Habit Logs:');
  const rHabits = await request('/api/habits', { headers: { 'Cookie': cookieHeader } });
  assert(rHabits.status === 200 && rHabits.data.habits.length === 2, 'GET /api/habits returns 2 habits');
  assert(rHabits.data.habits[0].completed_today === 0, 'Habit 201 starts uncompleted today');

  // Toggle habit 201 -> completed
  const rHabitToggle = await request('/api/habits/201/toggle', {
    method: 'POST',
    headers: { 'Cookie': cookieHeader }
  });
  assert(rHabitToggle.status === 200 && rHabitToggle.data.completed === true, 'POST /api/habits/201/toggle marks habit completed for today');

  // 6. Overall Performance vs Daily Progress
  console.log('\n[6] Overall Performance vs Daily Progress Engine:');
  const rProgress = await request('/api/progress', { headers: { 'Cookie': cookieHeader } });
  assert(rProgress.status === 200, 'GET /api/progress returns 200');

  const dp = rProgress.data.daily_progress;
  const op = rProgress.data.overall_performance;
  assert(dp.completed_missions === 1 && dp.total_missions === 2, 'Daily progress records 1/2 missions completed today');
  assert(dp.completed_habits === 1 && dp.total_habits === 2, 'Daily progress records 1/2 habits completed today');
  assert(dp.score === 50, 'Daily progress score is 50% for 1/2 missions and 1/2 habits');
  assert(op.score < 50, 'Overall performance is volume-confidence damped (does NOT instantly become 90-100 on day 1)');
  assert(op.confidence_factor < 0.2, 'Confidence factor is conservative for small sample size');

  // 7. AI Coach
  console.log('\n[7] AI Coach Chat:');
  const rChat = await request('/api/coach/chat', {
    method: 'POST',
    headers: { 'Cookie': cookieHeader },
    body: { message: 'How do I maintain focus on my AI goals today?' }
  });
  assert(rChat.status === 200 && rChat.data.reply.length > 0, 'POST /api/coach/chat returns valid coaching response');
  assert(rChat.data.context_used === true, 'AI Coach leveraged user background context');

  const rHistory = await request('/api/coach/history', { headers: { 'Cookie': cookieHeader } });
  assert(rHistory.status === 200 && rHistory.data.count >= 2, 'GET /api/coach/history records prompt and reply');

  // 8. Admin Controls & Security Authorization
  console.log('\n[8] Admin Controls & Role Authorization:');
  // Login regular user (role = 'user')
  const rUserLogin = await request('/api/auth/login', {
    method: 'POST',
    body: { email: 'regular@test.com', password: 'TestPass123!' }
  });
  const userCookie = rUserLogin.headers['set-cookie'][0].split(';')[0];

  // Regular user attempts admin overview
  const rAdminForbidden = await request('/api/admin/overview', {
    headers: { 'Cookie': userCookie }
  });
  assert(rAdminForbidden.status === 403, 'Regular user is forbidden (403) from accessing GET /api/admin/overview');

  // Admin user accesses admin overview
  const rAdminAllowed = await request('/api/admin/overview', {
    headers: { 'Cookie': cookieHeader }
  });
  assert(rAdminAllowed.status === 200 && rAdminAllowed.data.total_users === 2, 'Admin user successfully accesses GET /api/admin/overview');

  // 9. Logout & Session Invalidation
  console.log('\n[9] Logout & Revocation:');
  const rLogout = await request('/api/auth/logout', {
    method: 'POST',
    headers: { 'Cookie': cookieHeader }
  });
  assert(rLogout.status === 200, 'POST /api/auth/logout returns 200');

  const rMeAfterLogout = await request('/api/auth/me', {
    headers: { 'Cookie': cookieHeader }
  });
  assert(rMeAfterLogout.status === 401, 'Revoked session cookie returns 401 on subsequent requests');

  // Teardown
  server.close();

  console.log('\n===============================================================');
  console.log(`TEST SUMMARY: ${passed} PASSED, ${failed} FAILED`);
  console.log('===============================================================');

  if (failed > 0) {
    process.exit(1);
  }
}

runTests().catch((err) => {
  console.error('Test error:', err);
  if (server) server.close();
  process.exit(1);
});
