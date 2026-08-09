import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "app.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Create users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Seed demo user if users table is empty
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@masterykeycoach.com",))
    user_row = cursor.fetchone()
    if not user_row:
        cursor.execute(
            "INSERT INTO users (email, full_name) VALUES (?, ?)",
            ("demo@masterykeycoach.com", "Mohith"),
        )
        conn.commit()
        cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@masterykeycoach.com",))
        user_row = cursor.fetchone()

    demo_user_id = user_row["id"]

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
            completed INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()

    cursor.execute("PRAGMA table_info(missions)")
    existing_columns = [col["name"] for col in cursor.fetchall()]

    if "user_id" not in existing_columns:
        cursor.execute("ALTER TABLE missions ADD COLUMN user_id INTEGER")
        conn.commit()

    if "goal_id" not in existing_columns:
        cursor.execute("ALTER TABLE missions ADD COLUMN goal_id INTEGER")
        conn.commit()

    if "completed_at" not in existing_columns:
        cursor.execute("ALTER TABLE missions ADD COLUMN completed_at TIMESTAMP NULL")
        conn.commit()

    cursor.execute("UPDATE missions SET completed_at = CURRENT_TIMESTAMP WHERE completed = 1 AND completed_at IS NULL")
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

    conn.close()
