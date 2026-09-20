# Mastery Key Coach — Supabase PostgreSQL Database Migration Script

This document contains the complete, production-ready PostgreSQL DDL and initial seed script for **Mastery Key Coach (MKC)**.

> **Target Database:** Supabase Free PostgreSQL (or any standard PostgreSQL 14+ instance)
> **How to execute:**
> 1. Log into your free Supabase project at [database.new](https://database.new) or [app.supabase.com](https://app.supabase.com).
> 2. Open **SQL Editor** on the left menu.
> 3. Click **New Query**, paste the entire SQL script below, and click **RUN**.
> 4. Copy the connection string from **Project Settings -> Database -> Connection string (NodeJS / URI)** and save it as `DATABASE_URL` in Netlify.

---

```sql
-- ============================================================================
-- MASTERY KEY COACH (MKC) — PRODUCTION POSTGRESQL SCHEMA FOR SUPABASE
-- ============================================================================

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    username VARCHAR(100) UNIQUE,
    password_hash TEXT,
    is_active INTEGER DEFAULT 1,
    mkc_id VARCHAR(50) UNIQUE,
    avatar_initials VARCHAR(10),
    bio TEXT,
    role VARCHAR(50) DEFAULT 'user' NOT NULL,
    email_verified INTEGER DEFAULT 0,
    verified_at TIMESTAMPTZ,
    onboarding_completed INTEGER DEFAULT 0,
    onboarding_data TEXT,
    deactivated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_lower ON users(LOWER(username));
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower ON users(LOWER(email));
CREATE INDEX IF NOT EXISTS idx_users_mkc_id ON users(mkc_id);

-- 2. APP SESSIONS TABLE (HttpOnly Cookie Sessions)
CREATE TABLE IF NOT EXISTS app_sessions (
    token VARCHAR(255) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    last_seen_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMPTZ,
    user_agent TEXT,
    ip_address VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON app_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON app_sessions(expires_at);

-- 3. PASSWORD RESETS TABLE
CREATE TABLE IF NOT EXISTS password_resets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_pwd_resets_user_hash ON password_resets(user_id, token_hash);

-- 4. EMAIL VERIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS email_verifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_email_verif_token ON email_verifications(token_hash);

-- 5. AI ACTIVITY LOGS TABLE
CREATE TABLE IF NOT EXISTS ai_activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action_type VARCHAR(100),
    target_id INTEGER,
    status VARCHAR(50) DEFAULT 'success',
    latency_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_activity_user ON ai_activity_logs(user_id, created_at DESC);

-- 6. LIFE BLUEPRINTS & ROADMAP TABLES
CREATE TABLE IF NOT EXISTS life_blueprints (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    vision TEXT,
    target_date VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_blueprints_user ON life_blueprints(user_id, status);

CREATE TABLE IF NOT EXISTS blueprint_areas (
    id SERIAL PRIMARY KEY,
    blueprint_id INTEGER NOT NULL REFERENCES life_blueprints(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(50) DEFAULT '🎯',
    position INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_areas_blueprint ON blueprint_areas(blueprint_id, position);

CREATE TABLE IF NOT EXISTS blueprint_phases (
    id SERIAL PRIMARY KEY,
    blueprint_id INTEGER NOT NULL REFERENCES life_blueprints(id) ON DELETE CASCADE,
    area_id INTEGER REFERENCES blueprint_areas(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    phase_number INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    position INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_phases_blueprint ON blueprint_phases(blueprint_id, phase_number);

CREATE TABLE IF NOT EXISTS blueprint_milestones (
    id SERIAL PRIMARY KEY,
    phase_id INTEGER NOT NULL REFERENCES blueprint_phases(id) ON DELETE CASCADE,
    blueprint_id INTEGER NOT NULL REFERENCES life_blueprints(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_date VARCHAR(50),
    completed INTEGER DEFAULT 0,
    completed_at TIMESTAMPTZ,
    position INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_milestones_phase ON blueprint_milestones(phase_id, position);
CREATE INDEX IF NOT EXISTS idx_milestones_blueprint ON blueprint_milestones(blueprint_id);

-- 7. GOALS TABLE
CREATE TABLE IF NOT EXISTS goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) DEFAULT 'general',
    status VARCHAR(50) DEFAULT 'active',
    target_date VARCHAR(50),
    blueprint_id INTEGER REFERENCES life_blueprints(id) ON DELETE SET NULL,
    milestone_id INTEGER REFERENCES blueprint_milestones(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_goals_user ON goals(user_id, status);

-- 8. MISSIONS TABLE
CREATE TABLE IF NOT EXISTS missions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    goal_id INTEGER REFERENCES goals(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) DEFAULT 'general',
    time VARCHAR(50) DEFAULT '15 min',
    difficulty VARCHAR(50) DEFAULT 'easy',
    xp_reward INTEGER DEFAULT 10,
    completed INTEGER DEFAULT 0,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_missions_user ON missions(user_id, completed);

-- 9. MISSION LOGS TABLE (Daily Mission Auto-Reset & History)
CREATE TABLE IF NOT EXISTS mission_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mission_id INTEGER NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    completed_date VARCHAR(50) NOT NULL,
    completed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    xp_reward INTEGER DEFAULT 10,
    CONSTRAINT uq_mission_user_date UNIQUE (user_id, mission_id, completed_date)
);

CREATE INDEX IF NOT EXISTS idx_mission_logs_user_date ON mission_logs(user_id, completed_date);
CREATE INDEX IF NOT EXISTS idx_mission_logs_mission_date ON mission_logs(mission_id, completed_date);

-- 10. AI COACH MESSAGES TABLE (Chat Persistence)
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sender VARCHAR(50) NOT NULL CHECK(sender IN ('user', 'coach')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_user_created ON messages(user_id, created_at ASC);

-- 11. HABITS & HABIT LOGS TABLES
CREATE TABLE IF NOT EXISTS habits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) DEFAULT 'general',
    frequency VARCHAR(50) DEFAULT 'daily',
    target_days_per_week INTEGER DEFAULT 7,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_habits_user ON habits(user_id, status);

CREATE TABLE IF NOT EXISTS habit_logs (
    id SERIAL PRIMARY KEY,
    habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    completed_date VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_habit_log_date UNIQUE (habit_id, completed_date)
);

CREATE INDEX IF NOT EXISTS idx_habit_logs_habit_date ON habit_logs(habit_id, completed_date);
CREATE INDEX IF NOT EXISTS idx_habit_logs_user_date ON habit_logs(user_id, completed_date);

-- 12. JOURNAL ENTRIES TABLE
CREATE TABLE IF NOT EXISTS journal_entries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entry_date VARCHAR(50) NOT NULL,
    mood VARCHAR(50) NOT NULL DEFAULT 'focused',
    energy_level INTEGER NOT NULL DEFAULT 7 CHECK(energy_level BETWEEN 1 AND 10),
    wins_text TEXT,
    challenges_text TEXT,
    learnings_text TEXT,
    growth_next_text TEXT,
    ai_analysis TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_journal_user_date UNIQUE (user_id, entry_date)
);

CREATE INDEX IF NOT EXISTS idx_journal_user_date ON journal_entries(user_id, entry_date);
CREATE INDEX IF NOT EXISTS idx_journal_user_created ON journal_entries(user_id, created_at DESC);

-- 13. USER SETTINGS TABLE
CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(50) DEFAULT 'dark',
    notifications_enabled INTEGER DEFAULT 1,
    coach_style VARCHAR(50) DEFAULT 'strategic',
    daily_reminder_time VARCHAR(20) DEFAULT '08:00',
    profile_visibility VARCHAR(50) DEFAULT 'public',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 14. USER CREDENTIALS & ACHIEVEMENTS TABLE
CREATE TABLE IF NOT EXISTS user_credentials (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    credential_type VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    tier VARCHAR(50) DEFAULT 'bronze',
    xp_value INTEGER DEFAULT 50,
    evidence_type VARCHAR(100) NOT NULL,
    evidence_id TEXT,
    issued_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_credentials_user_slug UNIQUE (user_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_credentials_user ON user_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_credentials_slug ON user_credentials(user_id, slug);

-- 15. COMMUNITY POSTS, LIKES, COMMENTS TABLES
CREATE TABLE IF NOT EXISTS community_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    author_name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100) DEFAULT 'general',
    credential_id INTEGER REFERENCES user_credentials(id) ON DELETE SET NULL,
    likes_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_posts_created ON community_posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_author ON community_posts(user_id);

CREATE TABLE IF NOT EXISTS community_likes (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES community_posts(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_post_user_like UNIQUE (post_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_likes_post_user ON community_likes(post_id, user_id);

CREATE TABLE IF NOT EXISTS community_comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES community_posts(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    author_name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_comments_post ON community_comments(post_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_comments_created ON community_comments(created_at ASC);

-- 16. SOCIAL CONNECTIONS & FOLLOWS TABLES
CREATE TABLE IF NOT EXISTS user_connections (
    id SERIAL PRIMARY KEY,
    requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_connection UNIQUE (requester_id, recipient_id)
);

CREATE INDEX IF NOT EXISTS idx_user_conn_requester ON user_connections(requester_id, status);
CREATE INDEX IF NOT EXISTS idx_user_conn_recipient ON user_connections(recipient_id, status);

CREATE TABLE IF NOT EXISTS user_follows (
    id SERIAL PRIMARY KEY,
    follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_follow UNIQUE (follower_id, following_id)
);

CREATE INDEX IF NOT EXISTS idx_user_follows_follower ON user_follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_user_follows_following ON user_follows(following_id);

-- 17. PEER CHAT CONVERSATIONS & MESSAGES TABLES
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_members (
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (conversation_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_conv_members_user ON conversation_members(user_id);

CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    attachment_url TEXT,
    attachment_metadata TEXT,
    attachment_duration INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_conv ON chat_messages(conversation_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_unread ON chat_messages(conversation_id, sender_id, read_at);

-- 18. NOTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    reference_type VARCHAR(100),
    reference_id INTEGER,
    data TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_created ON notifications(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_ref ON notifications(reference_type, reference_id);

-- 19. FEEDBACK & BUG REPORTING TABLE
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(50) DEFAULT 'Normal' NOT NULL,
    status VARCHAR(50) DEFAULT 'new' NOT NULL,
    admin_notes TEXT,
    page_url TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);
CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback(category);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at DESC);

-- ============================================================================
-- INITIAL SEED DATA FOR DEMO ACCOUNT & STARTER ENTITIES
-- ============================================================================

-- Password: "Password123!" hashed with PBKDF2-SHA256 (100,000 iterations, salt: 9e6eb7b9b005eef3, key: 32 bytes)
INSERT INTO users (
    email,
    username,
    password_hash,
    full_name,
    mkc_id,
    avatar_initials,
    bio,
    role,
    email_verified,
    onboarding_completed
)
VALUES (
    'demo@masterykeycoach.com',
    'mohith_ai',
    'pbkdf2_sha256$100000$7bd8e23af69c904aa5df7661fed76545$202db117259a1e81aa82c1a84bac9919073d3b3d3efaf50f34a5ec98c4dd6c7d',
    'Mastery Key Coach Demo',
    'MKC-2026-DEMO01',
    'MK',
    'AI Engineering & Full-Stack Systems Mastery Demo Account',
    'admin',
    1,
    1
)
ON CONFLICT (email) DO UPDATE 
SET password_hash = EXCLUDED.password_hash, role = 'admin';

-- Seed User Settings for Demo User
INSERT INTO user_settings (user_id, theme, notifications_enabled, coach_style, daily_reminder_time, profile_visibility)
SELECT id, 'dark', 1, 'strategic', '08:00', 'public'
FROM users
WHERE email = 'demo@masterykeycoach.com'
ON CONFLICT (user_id) DO NOTHING;

-- Seed Default Goal
INSERT INTO goals (user_id, title, description, category, status, target_date)
SELECT id, 'AI Engineering Mastery', 'Become an industry-ready AI Engineer by building strong foundations in Python, DSA, machine learning, backend engineering, cloud, and AI application development.', 'career', 'active', '2028-06-30'
FROM users
WHERE email = 'demo@masterykeycoach.com'
AND NOT EXISTS (
    SELECT 1 FROM goals g JOIN users u ON g.user_id = u.id WHERE u.email = 'demo@masterykeycoach.com'
);

-- Seed Default Daily Missions
INSERT INTO missions (title, description, category, time, difficulty, xp_reward, completed, user_id)
SELECT 'Morning Mindset Protocol', 'Strategic planning and mental clarity routine', 'mindset', '15 min', 'easy', 15, 0, u.id
FROM users u WHERE u.email = 'demo@masterykeycoach.com'
AND NOT EXISTS (SELECT 1 FROM missions m WHERE m.user_id = u.id AND m.title = 'Morning Mindset Protocol');

INSERT INTO missions (title, description, category, time, difficulty, xp_reward, completed, user_id)
SELECT 'Deep Work Architecture Block', 'High-focus deep work session on core engineering', 'productivity', '45 min', 'medium', 25, 0, u.id
FROM users u WHERE u.email = 'demo@masterykeycoach.com'
AND NOT EXISTS (SELECT 1 FROM missions m WHERE m.user_id = u.id AND m.title = 'Deep Work Architecture Block');

INSERT INTO missions (title, description, category, time, difficulty, xp_reward, completed, user_id)
SELECT 'Physical Conditioning & Workout', 'High-intensity physical workout session', 'wellness', '30 min', 'medium', 20, 0, u.id
FROM users u WHERE u.email = 'demo@masterykeycoach.com'
AND NOT EXISTS (SELECT 1 FROM missions m WHERE m.user_id = u.id AND m.title = 'Physical Conditioning & Workout');

-- Seed Default Habits
INSERT INTO habits (title, category, frequency, target_days_per_week, status, user_id)
SELECT 'Cold Plunge / Cold Shower', 'wellness', 'daily', 7, 'active', u.id
FROM users u WHERE u.email = 'demo@masterykeycoach.com'
AND NOT EXISTS (SELECT 1 FROM habits h WHERE h.user_id = u.id AND h.title = 'Cold Plunge / Cold Shower');

INSERT INTO habits (title, category, frequency, target_days_per_week, status, user_id)
SELECT 'Daily Code Commit & Review', 'productivity', 'daily', 7, 'active', u.id
FROM users u WHERE u.email = 'demo@masterykeycoach.com'
AND NOT EXISTS (SELECT 1 FROM habits h WHERE h.user_id = u.id AND h.title = 'Daily Code Commit & Review');

INSERT INTO habits (title, category, frequency, target_days_per_week, status, user_id)
SELECT 'Read 20 Pages Non-Fiction', 'learning', 'daily', 7, 'active', u.id
FROM users u WHERE u.email = 'demo@masterykeycoach.com'
AND NOT EXISTS (SELECT 1 FROM habits h WHERE h.user_id = u.id AND h.title = 'Read 20 Pages Non-Fiction');

-- Seed Default Community Starter Posts
INSERT INTO community_posts (user_id, author_name, content, category, likes_count)
SELECT u.id, 'Mastery Key Coach Demo', 'Welcome to the Mastery Key Network! Execute your daily protocols, track momentum, and compound 1% improvements daily.', 'general', 0
FROM users u WHERE u.email = 'demo@masterykeycoach.com'
AND NOT EXISTS (SELECT 1 FROM community_posts WHERE author_name = 'Mastery Key Coach Demo' AND content LIKE 'Welcome%');

INSERT INTO community_posts (user_id, author_name, content, category, likes_count)
SELECT u.id, 'Mastery Key Coach Demo', 'Milestone breakthrough: Completed 14-day consecutive deep work protocol and deployed system architecture.', 'wins', 0
FROM users u WHERE u.email = 'demo@masterykeycoach.com'
AND NOT EXISTS (SELECT 1 FROM community_posts WHERE author_name = 'Mastery Key Coach Demo' AND content LIKE 'Milestone%');

INSERT INTO community_posts (user_id, author_name, content, category, likes_count)
SELECT u.id, 'Mastery Key Coach Demo', 'Discipline principle: Motivation is an emotional impulse; discipline is an automated engineering system.', 'mindset', 0
FROM users u WHERE u.email = 'demo@masterykeycoach.com'
AND NOT EXISTS (SELECT 1 FROM community_posts WHERE author_name = 'Mastery Key Coach Demo' AND content LIKE 'Discipline%');
```
