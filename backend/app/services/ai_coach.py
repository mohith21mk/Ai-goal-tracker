import os
import json
import sqlite3
import urllib.request
import urllib.error
import asyncio
from typing import Dict, Any, List
from pathlib import Path

from ..config import settings
from ..api.progress import compute_telemetry

DB_PATH = Path(__file__).resolve().parent.parent / "app.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_db_context() -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch demo user ID and name
    cursor.execute("SELECT id, full_name FROM users WHERE email = ?", ("demo@masterykeycoach.com",))
    user_row = cursor.fetchone()
    user_id = user_row["id"] if user_row else 1
    user_name = user_row["full_name"] if user_row else "Mohith"

    # Fetch active goals
    cursor.execute("SELECT title, category, status FROM goals WHERE status = 'active'")
    goal_rows = cursor.fetchall()
    goals = [dict(r) for r in goal_rows]

    conn.close()
    return {
        "user_id": user_id,
        "user_name": user_name,
        "goals": goals
    }


def save_chat_message(user_id: int, sender: str, content: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (user_id, sender, content) VALUES (?, ?, ?)",
        (user_id, sender, content)
    )
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()
    return msg_id


def fetch_chat_history(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    # Clamp limit between 1 and 100
    safe_limit = min(max(1, limit), 100)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, sender, content, created_at
        FROM messages
        WHERE user_id = ?
        ORDER BY created_at ASC, id ASC
        LIMIT ?
        """,
        (user_id, safe_limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_chat_history(user_id: int) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count


def _call_gemini_rest_api(gemini_url: str, payload: dict) -> Dict[str, Any]:
    json_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        gemini_url,
        data=json_bytes,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=12.0) as response:
        resp_bytes = response.read()
        return json.loads(resp_bytes.decode("utf-8"))


async def generate_coaching_response(user_message: str) -> Dict[str, Any]:
    # 1. Gather live database context
    context = get_db_context()
    user_id = context["user_id"]
    user_name = context["user_name"]
    goals = context["goals"]
    goals_text = ", ".join([f"'{g['title']}' ({g['category']})" for g in goals]) if goals else "Personal Growth"

    # Save incoming user message to SQLite DB
    try:
        save_chat_message(user_id, "user", user_message)
    except Exception as err:
        raise RuntimeError(f"Database persistence error saving user prompt: {err}")

    try:
        telemetry = await compute_telemetry()
    except Exception:
        telemetry = {
            "discipline_score": 60,
            "mindset_strength": 0,
            "consistency": 35,
            "growth_index": 36,
            "streak_days": 1,
            "xp_earned": 45,
            "mission_completion": {"completed": 3, "total": 5, "percentage": 60}
        }

    discipline = telemetry.get("discipline_score", 60)
    consistency = telemetry.get("consistency", 35)
    streak = telemetry.get("streak_days", 1)
    comp_pct = telemetry.get("mission_completion", {}).get("percentage", 60)
    completed_count = telemetry.get("mission_completion", {}).get("completed", 3)
    total_count = telemetry.get("mission_completion", {}).get("total", 5)

    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")

    # 2. Handle missing or placeholder API Key gracefully
    if not api_key or api_key.startswith("your_") or api_key == "placeholder":
        fallback_reply = (
            f"Action locked in for '{user_message}', {user_name}! "
            f"Your current discipline score is {discipline}/100 with {completed_count}/{total_count} protocols complete. "
            f"Keep focusing on '{goals_text}' with total execution today."
        )
        try:
            save_chat_message(user_id, "coach", fallback_reply)
        except Exception as err:
            raise RuntimeError(f"Database persistence error saving fallback coach reply: {err}")

        return {
            "reply": fallback_reply,
            "context_used": True,
            "live_llm": False,
            "note": "Live Gemini API synthesis is in preview mode. Add GEMINI_API_KEY to backend/.env for live LLM responses."
        }

    # 3. Build structured prompt for Gemini
    system_prompt = (
        f"You are AI Coach, a supportive, highly strategic, and disciplined personal growth coach for the Mastery Key Coach system.\n"
        f"User Profile: {user_name}\n"
        f"Active Goals: {goals_text}\n"
        f"Discipline Telemetry: Score = {discipline}/100, Consistency = {consistency}/100, Active Streak = {streak} days.\n"
        f"Daily Mission Completion: {completed_count}/{total_count} ({comp_pct}%).\n\n"
        f"Instructions:\n"
        f"- Provide a direct, motivating, 2-4 sentence coaching response.\n"
        f"- Reference their goal or telemetry where appropriate.\n"
        f"- Tone: Concise, inspiring, futuristic, disciplined, and actionable.\n\n"
        f"User Input: {user_message}"
    )

    candidate_models = ["gemini-flash-latest", "gemini-2.0-flash", "gemini-pro-latest"]
    configured_model = getattr(settings, "GEMINI_MODEL", "gemini-flash-latest")
    if configured_model in candidate_models:
        candidate_models.remove(configured_model)
    candidate_models.insert(0, configured_model)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": system_prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 300
        }
    }

    last_error = None
    reply_text = None
    used_model = None

    for model_name in candidate_models:
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            data = await asyncio.to_thread(_call_gemini_rest_api, gemini_url, payload)
            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts and "text" in parts[0]:
                    reply_text = parts[0]["text"].strip()
                    used_model = model_name
                    break
        except urllib.error.HTTPError as err:
            last_error = f"HTTP {err.code}: {err.reason}"
            if err.code in (404, 400):
                continue
            elif err.code == 429:
                await asyncio.sleep(1.0)
                continue
        except Exception as err:
            last_error = str(err)
            continue

    if not reply_text:
        reply_text = (
            f"Focus locked on '{user_message}', {user_name}! "
            f"Your discipline is currently at {discipline}/100 with {completed_count}/{total_count} daily protocols complete. "
            f"Stay relentless on your active goal '{goals_text}'."
        )

    # Save coach reply to SQLite DB
    try:
        save_chat_message(user_id, "coach", reply_text)
    except Exception as err:
        raise RuntimeError(f"Database persistence error saving coach response: {err}")

    return {
        "reply": reply_text,
        "context_used": True,
        "live_llm": bool(used_model),
        "model": used_model or "fallback",
        "error": last_error if not used_model else None
    }
