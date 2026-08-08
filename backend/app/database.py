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

    # Check existing column names in missions table via PRAGMA
    cursor.execute("PRAGMA table_info(missions)")
    existing_columns = [col["name"] for col in cursor.fetchall()]

    if "user_id" not in existing_columns:
        cursor.execute("ALTER TABLE missions ADD COLUMN user_id INTEGER")
        conn.commit()

    if "goal_id" not in existing_columns:
        cursor.execute("ALTER TABLE missions ADD COLUMN goal_id INTEGER")
        conn.commit()

    # Seed initial missions if missions table is completely empty
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
        # Safely associate any existing unassigned missions without modifying completed state or title
        cursor.execute(
            "UPDATE missions SET user_id = ?, goal_id = ? WHERE user_id IS NULL",
            (demo_user_id, default_goal_id),
        )
        conn.commit()

    conn.close()
