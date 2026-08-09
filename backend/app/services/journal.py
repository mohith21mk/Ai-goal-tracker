import os
import json
import sqlite3
import urllib.request
import urllib.error
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..config import settings

DB_PATH = Path(__file__).resolve().parent.parent / "app.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_demo_user_id() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@masterykeycoach.com",))
    row = cursor.fetchone()
    conn.close()
    return row["id"] if row else 1


def get_today_date_str() -> str:
    return date.today().strftime("%Y-%m-%d")


def get_journal_entry_by_id(entry_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM journal_entries WHERE id = ? AND user_id = ?",
        (entry_id, user_id),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_today_journal_entry(user_id: int) -> Optional[Dict[str, Any]]:
    today_str = get_today_date_str()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM journal_entries WHERE user_id = ? AND entry_date = ?",
        (user_id, today_str),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def upsert_journal_entry(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    entry_date = data.get("entry_date") or get_today_date_str()
    mood = data.get("mood", "focused")
    energy_level = data.get("energy_level", 7)
    wins_text = data.get("wins_text", "")
    challenges_text = data.get("challenges_text", "")
    learnings_text = data.get("learnings_text", "")
    growth_next_text = data.get("growth_next_text", "")

    # Ensure energy_level is bounded 1-10
    energy_level = max(1, min(10, int(energy_level)))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO journal_entries (
            user_id, entry_date, mood, energy_level,
            wins_text, challenges_text, learnings_text, growth_next_text,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, entry_date) DO UPDATE SET
            mood = excluded.mood,
            energy_level = excluded.energy_level,
            wins_text = excluded.wins_text,
            challenges_text = excluded.challenges_text,
            learnings_text = excluded.learnings_text,
            growth_next_text = excluded.growth_next_text,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            user_id,
            entry_date,
            mood,
            energy_level,
            wins_text,
            challenges_text,
            learnings_text,
            growth_next_text,
        ),
    )
    conn.commit()

    # Retrieve the upserted row
    cursor.execute(
        "SELECT * FROM journal_entries WHERE user_id = ? AND entry_date = ?",
        (user_id, entry_date),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row)


def get_journal_history(user_id: int, limit: int = 30) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM journal_entries
        WHERE user_id = ?
        ORDER BY entry_date DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_journal_entry(entry_id: int, user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM journal_entries WHERE id = ? AND user_id = ?", (entry_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def compute_journal_stats(user_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT entry_date, mood, energy_level
        FROM journal_entries
        WHERE user_id = ?
        ORDER BY entry_date DESC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {
            "total_entries": 0,
            "journal_streak": 0,
            "longest_journal_streak": 0,
            "avg_energy_7d": 0.0,
            "latest_mood": None,
            "mood_distribution": {},
        }

    total_entries = len(rows)
    entry_dates = {r["entry_date"] for r in rows}

    # Reflection Streak
    today_dt = date.today()
    today_str = today_dt.strftime("%Y-%m-%d")
    yesterday_str = (today_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    streak = 0
    start_dt = None
    if today_str in entry_dates:
        start_dt = today_dt
    elif yesterday_str in entry_dates:
        start_dt = today_dt - timedelta(days=1)

    if start_dt:
        curr_dt = start_dt
        while curr_dt.strftime("%Y-%m-%d") in entry_dates:
            streak += 1
            curr_dt -= timedelta(days=1)

    # Longest Journal Streak
    sorted_dates = sorted([datetime.strptime(d, "%Y-%m-%d").date() for d in entry_dates])
    longest_streak = 0
    if sorted_dates:
        curr_run = 1
        max_run = 1
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] == sorted_dates[i - 1] + timedelta(days=1):
                curr_run += 1
            else:
                curr_run = 1
            if curr_run > max_run:
                max_run = curr_run
        longest_streak = max_run

    # 7-Day Energy Average
    past_7_days = {(today_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)}
    recent_7_energies = [r["energy_level"] for r in rows if r["entry_date"] in past_7_days]
    avg_energy_7d = round(sum(recent_7_energies) / len(recent_7_energies), 1) if recent_7_energies else 0.0

    # Mood Distribution
    mood_counts: Dict[str, int] = {}
    for r in rows[:30]:
        m = r["mood"]
        mood_counts[m] = mood_counts.get(m, 0) + 1

    latest_mood = rows[0]["mood"] if rows else None

    return {
        "total_entries": total_entries,
        "journal_streak": streak,
        "longest_journal_streak": max(longest_streak, streak),
        "avg_energy_7d": avg_energy_7d,
        "latest_mood": latest_mood,
        "mood_distribution": mood_counts,
    }


def _call_gemini_api_sync(api_key: str, prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    with urllib.request.urlopen(req, timeout=12) as response:
        res_body = response.read().decode("utf-8")
        res_json = json.loads(res_body)

        candidates = res_json.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "").strip()

    raise RuntimeError("Empty response payload from Gemini API.")


async def generate_journal_ai_analysis(entry_id: int, user_id: int) -> Dict[str, Any]:
    entry = get_journal_entry_by_id(entry_id, user_id)
    if not entry:
        raise KeyError(f"Journal entry {entry_id} not found.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT full_name FROM users WHERE id = ?", (user_id,))
    u_row = cursor.fetchone()
    user_name = u_row["full_name"] if u_row else "Mohith"

    cursor.execute("SELECT title FROM goals WHERE user_id = ? AND status = 'active'", (user_id,))
    goals = [r["title"] for r in cursor.fetchall()]
    conn.close()

    api_key = settings.GEMINI_API_KEY
    live_llm = False
    ai_feedback = ""

    prompt = f"""
You are the AI Mindset Coach inside Mastery Key Coach.
Provide a structured 3-part mindset reflection analysis for {user_name}.

User Context:
- Active Goals: {', '.join(goals) if goals else 'General Growth'}
- Reflection Date: {entry['entry_date']}
- Self-Reported Mood: {entry['mood']}
- Energy Level: {entry['energy_level']}/10

Journal Reflection Inputs:
- Wins ("What went well"): {entry['wins_text'] or 'Focused execution.'}
- Challenges ("What challenged me"): {entry['challenges_text'] or 'Pacing and focus retention.'}
- Learnings ("What I learned"): {entry['learnings_text'] or 'Micro-steps yield big progress.'}
- Tomorrow Growth ("What I will improve"): {entry['growth_next_text'] or 'Maintain high momentum.'}

Instructions:
Generate your response structured under EXACTLY these three bold markdown headings:

**Mindset Validation & Reframe**
[Validate their wins and self-reported energy level warmly and constructively]

**Strategic Actionable Insight**
[Transform their reported challenge into a tactical engineering/mindset opportunity]

**Tomorrow's Growth Focus**
[Provide one clear, high-leverage action anchor for tomorrow]

Keep tone empowering, concise, and tactical. Do not use generic fluff.
"""

    if api_key and api_key != "YOUR_GEMINI_API_KEY_HERE":
        try:
            ai_feedback = await asyncio.to_thread(_call_gemini_api_sync, api_key, prompt)
            live_llm = True
        except Exception as err:
            print(f"Gemini API call failed for journal analysis: {err}")

    if not live_llm or not ai_feedback:
        ai_feedback = (
            f"**Mindset Validation & Reframe**\n"
            f"Excellent self-awareness today, {user_name}. Logging your reflection with a {entry['mood']} mindset at energy level {entry['energy_level']}/10 demonstrates consistent emotional ownership and mental discipline.\n\n"
            f"**Strategic Actionable Insight**\n"
            f"Reframing your challenge ('{entry['challenges_text'] or 'Focus retention'}') reveals where your attention friction lives. Break tomorrow's first major task into an uninterrupted 25-minute deep focus sprint.\n\n"
            f"**Tomorrow's Growth Focus**\n"
            f"Execute your target improvement ('{entry['growth_next_text'] or 'High momentum'}') within the first 60 minutes of your workday."
        )

    # Save generated AI analysis back to database
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE journal_entries SET ai_analysis = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (ai_feedback, entry_id),
    )
    conn.commit()
    conn.close()

    updated_entry = get_journal_entry_by_id(entry_id, user_id)
    return {
        "live_llm": live_llm,
        "entry": updated_entry,
    }
