import os
import sqlite3
from pathlib import Path
from .config import settings

DB_PATH = Path(__file__).resolve().parent / "app.db"


def _is_postgres():
    db_url = settings.DATABASE_URL
    return db_url.startswith('postgres://') or db_url.startswith('postgresql://')


class _CompatRow(dict):
    """A dict subclass that also supports integer indexing like sqlite3.Row."""
    def __getitem__(self, key):
        if isinstance(key, int):
            vals = list(self.values())
            if 0 <= key < len(vals):
                return vals[key]
            return None
        return super().__getitem__(key)


class _PgCompatCursor:
    """Wraps a psycopg2 RealDictCursor to accept '?' placeholders and translate to '%s'."""
    def __init__(self, real_cursor):
        self._cursor = real_cursor

    def execute(self, sql, params=None):
        sql = sql.replace('?', '%s')
        stripped = sql.strip()
        upper_stripped = stripped.upper()
        self._last_insert_id = None
        if upper_stripped.startswith('INSERT') and 'RETURNING' not in upper_stripped:
            # Add RETURNING id for tables that have auto-increment id
            # Skip for tables with composite PKs (conversation_members)
            # and string PKs (app_sessions)
            skip_tables = ('app_sessions', 'conversation_members')
            should_return = True
            for t in skip_tables:
                if t.upper() in upper_stripped:
                    should_return = False
                    break
            if should_return:
                returning_sql = stripped.rstrip().rstrip(';') + ' RETURNING id'
                self._cursor.execute(returning_sql, params)
                row = self._cursor.fetchone()
                if row:
                    self._last_insert_id = row['id'] if (isinstance(row, dict) and 'id' in row) else (row[0] if isinstance(row, (list, tuple)) else None)
                else:
                    self._last_insert_id = None
                return
        return self._cursor.execute(sql, params)

    def executemany(self, sql, params_list):
        sql = sql.replace('?', '%s')
        return self._cursor.executemany(sql, params_list)

    def fetchone(self):
        row = self._cursor.fetchone()
        return _CompatRow(row) if row else None

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [_CompatRow(r) for r in rows]

    @property
    def lastrowid(self):
        return getattr(self, '_last_insert_id', None)

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def description(self):
        return self._cursor.description

    def close(self):
        return self._cursor.close()

    def __iter__(self):
        return iter(self._cursor)


class _PgCompatConnection:
    """Wraps a psycopg2 connection to return CompatCursor instances."""
    def __init__(self, real_conn):
        self._conn = real_conn

    def cursor(self):
        return _PgCompatCursor(self._conn.cursor())

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    @property
    def autocommit(self):
        return self._conn.autocommit

    @autocommit.setter
    def autocommit(self, value):
        self._conn.autocommit = value


def get_connection():
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgres://") or db_url.startswith("postgresql://"):
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            pg_url = db_url.replace("postgres://", "postgresql://", 1)
            conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
            return _PgCompatConnection(conn)
        except Exception as err:
            # Fallback to local SQLite if PostgreSQL connection fails in local testing
            pass

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_demo_user() -> None:
    """Ensures demo user exists with synchronized password. Safe for concurrent Gunicorn workers."""
    conn = None
    try:
        from .services.logger import logger
        from .services.auth import hash_password

        demo_pwd_hash = hash_password("Password123!")
        conn = get_connection()
        cursor = conn.cursor()

        if _is_postgres():
            cursor.execute(
                """
                INSERT INTO users (email, username, password_hash, full_name, mkc_id, avatar_initials, bio, role, email_verified, onboarding_completed)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'user', 1, 1)
                ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash
                RETURNING id
                """,
                ("demo@masterykeycoach.com", "mohith_ai", demo_pwd_hash, "Mastery Key Coach Demo", "MKC-2026-DEMO01", "MK", "AI Engineering & Full-Stack Systems Mastery Demo Account"),
            )
            row = cursor.fetchone()
            user_id = row["id"] if isinstance(row, dict) else (row[0] if row else None)
            if user_id:
                cursor.execute(
                    """
                    INSERT INTO user_settings (user_id, theme, notifications_enabled, coach_style, daily_reminder_time, profile_visibility)
                    VALUES (?, 'dark', 1, 'strategic', '08:00', 'public')
                    ON CONFLICT (user_id) DO NOTHING
                    """,
                    (user_id,),
                )
        else:
            cursor.execute(
                """
                INSERT OR IGNORE INTO users (email, username, password_hash, full_name, mkc_id, avatar_initials, bio, role, email_verified, onboarding_completed)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'user', 1, 1)
                """,
                ("demo@masterykeycoach.com", "mohith_ai", demo_pwd_hash, "Mastery Key Coach Demo", "MKC-2026-DEMO01", "MK", "AI Engineering & Full-Stack Systems Mastery Demo Account"),
            )
            cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (demo_pwd_hash, "demo@masterykeycoach.com"))
            cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@masterykeycoach.com",))
            row = cursor.fetchone()
            user_id = row[0] if row else None
            if user_id:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO user_settings (user_id, theme, notifications_enabled, coach_style, daily_reminder_time, profile_visibility)
                    VALUES (?, 'dark', 1, 'strategic', '08:00', 'public')
                    """,
                    (user_id,),
                )

        conn.commit()
        logger.info("Demo user verified and synchronized (demo@masterykeycoach.com).")
    except Exception as err:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        from .services.logger import logger
        logger.exception(f"Failed to ensure demo user: {err}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        # PostgreSQL schema is managed by Alembic migrations + SQLAlchemy ORM
        from .db_session import engine, init_orm_db
        engine.dispose()
        init_orm_db()
        _ensure_demo_user()
        return

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Create users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE,
            password_hash TEXT,
            is_active INTEGER DEFAULT 1,
            mkc_id TEXT UNIQUE,
            avatar_initials TEXT,
            bio TEXT,
            role TEXT DEFAULT 'user' NOT NULL,
            email_verified INTEGER DEFAULT 0,
            verified_at TIMESTAMP,
            onboarding_completed INTEGER DEFAULT 0,
            onboarding_data TEXT,
            deactivated_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Safely migrate existing database schema if columns are missing
    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [r["name"] for r in cursor.fetchall()]
    if "mkc_id" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN mkc_id TEXT")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_mkc_id ON users(mkc_id)")
    if "avatar_initials" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN avatar_initials TEXT")
    if "bio" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT")
    if "username" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
    if "password_hash" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    if "is_active" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
    if "email_verified" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0")
    if "verified_at" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN verified_at TIMESTAMP")
    if "onboarding_completed" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN onboarding_completed INTEGER DEFAULT 0")
    if "onboarding_data" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN onboarding_data TEXT")
    if "deactivated_at" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN deactivated_at TIMESTAMP")
    if "role" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user' NOT NULL")
    conn.commit()

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_lower ON users(LOWER(username))")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower ON users(LOWER(email))")
    conn.commit()

    # 1.5 Create app_sessions table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS app_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            revoked_at TIMESTAMP,
            user_agent TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute("PRAGMA table_info(app_sessions)")
    existing_session_cols = [r["name"] for r in cursor.fetchall()]
    if "last_seen_at" not in existing_session_cols:
        cursor.execute("ALTER TABLE app_sessions ADD COLUMN last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    if "revoked_at" not in existing_session_cols:
        cursor.execute("ALTER TABLE app_sessions ADD COLUMN revoked_at TIMESTAMP")
    if "user_agent" not in existing_session_cols:
        cursor.execute("ALTER TABLE app_sessions ADD COLUMN user_agent TEXT")
    if "ip_address" not in existing_session_cols:
        cursor.execute("ALTER TABLE app_sessions ADD COLUMN ip_address TEXT")
    conn.commit()

    # 1.6 Create password_resets table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used_at TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pwd_resets_user_hash ON password_resets(user_id, token_hash)")
    conn.commit()

    # 1.7 Create email_verifications table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS email_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used_at TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_verif_token ON email_verifications(token_hash)")
    conn.commit()

    # 1.8 Create ai_activity_logs table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action_type TEXT,
            target_id INTEGER,
            status TEXT DEFAULT 'success',
            latency_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()

    # Seed demo user if users table is empty
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@masterykeycoach.com",))
    user_row = cursor.fetchone()

    # Import hash helper for demo user migration
    from .services.auth import hash_password

    if not user_row:
        default_pwd_hash = hash_password("Password123!")
        cursor.execute(
            "INSERT INTO users (email, full_name, username, password_hash, avatar_initials) VALUES (?, ?, ?, ?, ?)",
            ("demo@masterykeycoach.com", "Mohith", "mohith_ai", default_pwd_hash, "MK"),
        )
        conn.commit()
        cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@masterykeycoach.com",))
        user_row = cursor.fetchone()
    else:
        # Update existing demo user credentials and username
        cursor.execute(
            "UPDATE users SET username = ?, password_hash = ? WHERE email = ?",
            ("mohith_ai", hash_password("Password123!"), "demo@masterykeycoach.com"),
        )
        conn.commit()

    demo_user_id = user_row["id"]

    # Populate persistent unique MKC ID and initials for users if empty
    cursor.execute("SELECT id, email, full_name, created_at, mkc_id, avatar_initials, bio FROM users")
    all_users = cursor.fetchall()
    import random
    import string

    for u in all_users:
        u_id = u["id"]
        u_mkc_id = u["mkc_id"]
        u_initials = u["avatar_initials"]
        u_name = u["full_name"] or "User"

        updates = []
        params = []

        if not u_mkc_id:
            created_str = str(u["created_at"] or "")
            year = "2026"
            if len(created_str) >= 4 and created_str[:4].isdigit():
                year = created_str[:4]

            while True:
                rnd_hex = "".join(random.choices(string.hexdigits.upper()[:16], k=6))
                candidate_id = f"MKC-{year}-{rnd_hex}"
                cursor.execute("SELECT id FROM users WHERE mkc_id = ?", (candidate_id,))
                if not cursor.fetchone():
                    u_mkc_id = candidate_id
                    break

            updates.append("mkc_id = ?")
            params.append(u_mkc_id)

        if not u_initials:
            parts = u_name.strip().split()
            if len(parts) >= 2:
                derived_initials = (parts[0][0] + parts[-1][0]).upper()
            elif len(parts) == 1:
                derived_initials = parts[0][:2].upper()
            else:
                derived_initials = "MK"
            updates.append("avatar_initials = ?")
            params.append(derived_initials)

        if u["bio"] is None:
            updates.append("bio = ?")
            params.append("AI Engineering & Full-Stack Systems Mastery")

        if updates:
            params.append(u_id)
            cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)

    conn.commit()

    # 2. Create goals table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'general',
            status TEXT DEFAULT 'active',
            target_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()

    # Evolve goals table safely if blueprint_id or milestone_id are missing
    cursor.execute("PRAGMA table_info(goals)")
    existing_goal_cols = [col["name"] for col in cursor.fetchall()]

    if "blueprint_id" not in existing_goal_cols:
        cursor.execute("ALTER TABLE goals ADD COLUMN blueprint_id INTEGER NULL")
        conn.commit()

    if "milestone_id" not in existing_goal_cols:
        cursor.execute("ALTER TABLE goals ADD COLUMN milestone_id INTEGER NULL")
        conn.commit()

    # Seed default goal if no goals exist for demo user
    cursor.execute("SELECT id FROM goals WHERE user_id = ?", (demo_user_id,))
    goal_row = cursor.fetchone()
    if not goal_row:
        cursor.execute(
            """
            INSERT INTO goals (user_id, title, description, category, status, target_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                demo_user_id,
                "AI Engineering Mastery",
                "Become an industry-ready AI Engineer by building strong foundations in Python, DSA, machine learning, backend engineering, cloud, and AI application development.",
                "career",
                "active",
                "2028-06-30",
            ),
        )
        conn.commit()
        cursor.execute("SELECT id FROM goals WHERE user_id = ?", (demo_user_id,))
        goal_row = cursor.fetchone()

    default_goal_id = goal_row["id"]

    # 3. Create or evolve missions table safely
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS missions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'general',
            time TEXT DEFAULT '15 min',
            difficulty TEXT DEFAULT 'easy',
            xp_reward INTEGER DEFAULT 10,
            completed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()

    for col_def in [
        ("user_id", "INTEGER"),
        ("goal_id", "INTEGER"),
        ("completed_at", "TIMESTAMP NULL"),
        ("created_at", "TIMESTAMP NULL")
    ]:
        try:
            cursor.execute(f"ALTER TABLE missions ADD COLUMN {col_def[0]} {col_def[1]}")
            conn.commit()
        except Exception:
            pass

    cursor.execute("UPDATE missions SET completed_at = CURRENT_TIMESTAMP WHERE completed = 1 AND completed_at IS NULL")
    cursor.execute("UPDATE missions SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM missions")
    count = cursor.fetchone()[0]

    if count == 0:
        default_missions = [
            ("Morning Meditation Protocol", "Mindfulness and breathwork routine", "wellness", "10 min", "easy", 10, 0, demo_user_id, default_goal_id),
            ("Deep Work Block & Code Architecture", "Complete uninterrupted focused engineering work", "productivity", "2 hrs", "hard", 25, 1, demo_user_id, default_goal_id),
            ("High-Intensity Workout Session", "Physical conditioning and strength protocol", "fitness", "45 min", "hard", 20, 0, demo_user_id, default_goal_id),
            ("Mastery Reading & Knowledge Note", "Read 20 pages and extract core mental models", "learning", "20 min", "easy", 10, 1, demo_user_id, default_goal_id),
            ("Gratitude & Vision Reflection", "Journal 3 strategic wins and future vision", "mindset", "5 min", "easy", 10, 0, demo_user_id, default_goal_id),
        ]
        cursor.executemany(
            """
            INSERT INTO missions (title, description, category, time, difficulty, xp_reward, completed, user_id, goal_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            default_missions,
        )
        conn.commit()
    else:
        cursor.execute(
            "UPDATE missions SET user_id = ?, goal_id = ? WHERE user_id IS NULL",
            (demo_user_id, default_goal_id),
        )
        conn.commit()

    # 4. Create messages table for AI Coach chat history persistence
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sender TEXT NOT NULL CHECK(sender IN ('user', 'coach')),
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_user_created ON messages(user_id, created_at, id)")
    conn.commit()

    # 5. Create habits & habit_logs tables
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'general',
            frequency TEXT DEFAULT 'daily',
            target_days_per_week INTEGER DEFAULT 7,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS habit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            completed_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(habit_id) REFERENCES habits(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id),
            UNIQUE(habit_id, completed_date)
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habit_logs_habit_date ON habit_logs(habit_id, completed_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habit_logs_user_date ON habit_logs(user_id, completed_date)")
    conn.commit()

    # Seed default habits if empty
    cursor.execute("SELECT COUNT(*) FROM habits WHERE user_id = ?", (demo_user_id,))
    habit_count = cursor.fetchone()[0]

    if habit_count == 0:
        default_habits = [
            (demo_user_id, "Hydration Protocol (3L Water)", "Maintain optimal cellular hydration throughout the day", "wellness", "daily", 7, "active"),
            (demo_user_id, "10k Daily Steps", "Daily movement and cardiovascular health conditioning", "fitness", "daily", 7, "active"),
            (demo_user_id, "60-Min AI Deep Learning", "Dedicated focus block on machine learning and system architecture", "learning", "daily", 6, "active"),
            (demo_user_id, "Cold Shower Conditioning", "Vagus nerve stimulation and mental fortitude training", "mindset", "daily", 5, "active"),
        ]
        cursor.executemany(
            """
            INSERT INTO habits (user_id, title, description, category, frequency, target_days_per_week, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            default_habits,
        )
        conn.commit()

    # 6. Create journal_entries table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            entry_date TEXT NOT NULL,
            mood TEXT NOT NULL DEFAULT 'focused',
            energy_level INTEGER NOT NULL DEFAULT 7 CHECK(energy_level BETWEEN 1 AND 10),
            wins_text TEXT,
            challenges_text TEXT,
            learnings_text TEXT,
            growth_next_text TEXT,
            ai_analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            UNIQUE(user_id, entry_date)
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_user_date ON journal_entries(user_id, entry_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_user_created ON journal_entries(user_id, created_at DESC)")
    conn.commit()

    # 7. Create Life Blueprint Tables (Phase 8)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS life_blueprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            vision TEXT,
            target_date TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS blueprint_areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blueprint_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            icon TEXT DEFAULT '🎯',
            position INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(blueprint_id) REFERENCES life_blueprints(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS blueprint_phases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blueprint_id INTEGER NOT NULL,
            area_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            phase_number INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            position INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(blueprint_id) REFERENCES life_blueprints(id) ON DELETE CASCADE,
            FOREIGN KEY(area_id) REFERENCES blueprint_areas(id) ON DELETE SET NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS blueprint_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phase_id INTEGER NOT NULL,
            blueprint_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            target_date TEXT,
            completed INTEGER DEFAULT 0,
            completed_at TIMESTAMP NULL,
            position INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(phase_id) REFERENCES blueprint_phases(id) ON DELETE CASCADE,
            FOREIGN KEY(blueprint_id) REFERENCES life_blueprints(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_blueprints_user ON life_blueprints(user_id, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_phases_blueprint ON blueprint_phases(blueprint_id, phase_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_milestones_phase ON blueprint_milestones(phase_id, position)")
    conn.commit()

    # Seed default initial blueprint if empty
    cursor.execute("SELECT COUNT(*) FROM life_blueprints WHERE user_id = ?", (demo_user_id,))
    blueprint_count = cursor.fetchone()[0]

    if blueprint_count == 0:
        cursor.execute(
            """
            INSERT INTO life_blueprints (user_id, title, description, vision, target_date, status)
            VALUES (?, ?, ?, ?, ?, 'active')
            """,
            (
                demo_user_id,
                "Become an AI Engineer by 2028",
                "Comprehensive strategic roadmap to master software engineering, data structures, machine learning, and AI application architecture.",
                "Placement-ready AI Engineer building production-grade intelligent systems.",
                "2028-06-30",
            ),
        )
        conn.commit()
        bp_id = cursor.lastrowid

        # Seed Life Areas
        areas = [
            (bp_id, demo_user_id, "Career & Engineering", "Software & AI technical mastery", "💻", 1),
            (bp_id, demo_user_id, "Mindset & Leadership", "Cognitive clarity & resilience", "🧠", 2),
            (bp_id, demo_user_id, "Health & Fitness", "Physical energy & stamina", "⚡", 3),
        ]
        cursor.executemany(
            """
            INSERT INTO blueprint_areas (blueprint_id, user_id, name, description, icon, position)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            areas,
        )
        conn.commit()

        # Seed Phases
        phases = [
            (bp_id, 1, "Phase 1: Foundation & Core CS", "Master Python, DSA, git, and backend fundamentals", 1, "completed", 1),
            (bp_id, 2, "Phase 2: AI & Machine Learning", "Deep dive into ML models, neural networks, and LLM orchestration", 2, "active", 2),
            (bp_id, 3, "Phase 3: Portfolio & Placement Mastery", "Build flagship AI applications, system design, and mock interviews", 3, "pending", 3),
        ]
        phase_ids = []
        for p in phases:
            cursor.execute(
                """
                INSERT INTO blueprint_phases (blueprint_id, area_id, title, description, phase_number, status, position)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                p,
            )
            conn.commit()
            phase_ids.append(cursor.lastrowid)

        # Seed Milestones
        milestones = [
            (phase_ids[0], bp_id, "Master Python & Object-Oriented Design", "Complete core OOP & data structures", "2026-03-31", 1, "2026-03-30 10:00:00", 1),
            (phase_ids[0], bp_id, "Build REST APIs with FastAPI & SQLite", "Design production-grade backend API layers", "2026-06-30", 1, "2026-06-25 14:00:00", 2),
            (phase_ids[1], bp_id, "Learn ML Fundamentals & Scikit-Learn", "Understand regression, classification, and model evaluation", "2026-11-30", 1, "2026-08-01 09:00:00", 1),
            (phase_ids[1], bp_id, "Build LLM Orchestration Applications", "Integrate Gemini REST APIs, prompt engineering, and agentic workflows", "2027-03-31", 0, None, 2),
            (phase_ids[1], bp_id, "Master PyTorch & Deep Neural Networks", "Implement vision and transformer architectures from scratch", "2027-08-31", 0, None, 3),
            (phase_ids[2], bp_id, "Deploy Flagship AI Web Platform", "Full-stack deployment with CI/CD, database, and real-time inference", "2027-12-31", 0, None, 1),
            (phase_ids[2], bp_id, "Complete 50+ Advanced DSA Mock Interviews", "High-pressure problem solving and system design practice", "2028-04-30", 0, None, 2),
        ]
        cursor.executemany(
            """
            INSERT INTO blueprint_milestones (phase_id, blueprint_id, title, description, target_date, completed, completed_at, position)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            milestones,
        )
        conn.commit()

        # Link default active goal to blueprint phase 2
        cursor.execute("UPDATE goals SET blueprint_id = ?, milestone_id = ? WHERE id = ?", (bp_id, milestones[3][0], default_goal_id))
        conn.commit()

    # 13. Create user_settings table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            theme TEXT DEFAULT 'dark',
            notifications_enabled INTEGER DEFAULT 1,
            coach_style TEXT DEFAULT 'strategic',
            daily_reminder_time TEXT DEFAULT '08:00',
            profile_visibility TEXT DEFAULT 'public',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    # 14. Create community_posts table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS community_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            author_name TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            credential_id INTEGER,
            likes_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(credential_id) REFERENCES user_credentials(id) ON DELETE SET NULL
        )
        """
    )
    try:
        cursor.execute("ALTER TABLE community_posts ADD COLUMN credential_id INTEGER REFERENCES user_credentials(id)")
    except Exception:
        pass

    # 15. Create community_likes table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS community_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(post_id, user_id),
            FOREIGN KEY(post_id) REFERENCES community_posts(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    # 16. Create community_comments table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS community_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            author_name TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(post_id) REFERENCES community_posts(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    # 17. Create user_connections table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_id INTEGER NOT NULL,
            recipient_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(requester_id, recipient_id),
            FOREIGN KEY(requester_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(recipient_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    # Indexes for Community & Connections
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_created ON community_posts(created_at DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_author ON community_posts(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_likes_post_user ON community_likes(post_id, user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_post ON community_comments(post_id, created_at ASC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_created ON community_comments(created_at ASC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_conn_requester ON user_connections(requester_id, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_conn_recipient ON user_connections(recipient_id, status)")

    # 13. Create conversations table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # 14. Create conversation_members table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_members (
            conversation_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (conversation_id, user_id),
            FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    # 15. Create chat_messages table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_at TIMESTAMP,
            FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
            FOREIGN KEY(sender_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    # Chat & messaging performance indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_members_user ON conversation_members(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_conv ON chat_messages(conversation_id, created_at ASC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_unread ON chat_messages(conversation_id, sender_id, read_at)")

    # 16. Create notifications table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT,
            reference_type TEXT,
            reference_id INTEGER,
            data TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute("PRAGMA table_info(notifications)")
    notif_cols = [r["name"] for r in cursor.fetchall()]
    if "data" not in notif_cols:
        cursor.execute("ALTER TABLE notifications ADD COLUMN data TEXT")

    # Notification indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_created ON notifications(user_id, created_at DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_ref ON notifications(reference_type, reference_id)")

    # 18. Create user_credentials table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            credential_type TEXT NOT NULL,
            slug TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            tier TEXT DEFAULT 'bronze',
            xp_value INTEGER DEFAULT 50,
            evidence_type TEXT NOT NULL,
            evidence_id TEXT,
            issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, slug),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_credentials_user ON user_credentials(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_credentials_slug ON user_credentials(user_id, slug)")

    # 19. Create feedback table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT DEFAULT 'Normal' NOT NULL,
            status TEXT DEFAULT 'new' NOT NULL,
            admin_notes TEXT,
            page_url TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at)")

    conn.commit()
    conn.close()

    from .db_session import engine, init_orm_db
    engine.dispose()
    init_orm_db()
