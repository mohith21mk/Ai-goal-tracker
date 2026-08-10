import os
import json
import sqlite3
import urllib.request
import urllib.error
import asyncio
from typing import Dict, Any, List
from pathlib import Path

from ..config import settings

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
    cursor.execute("SELECT title, category FROM goals WHERE status = 'active' LIMIT 2")
    goal_rows = cursor.fetchall()
    goals = [dict(r) for r in goal_rows]

    # Fetch fast mission summary
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) FROM missions")
    m_row = cursor.fetchone()
    total_missions = m_row[0] if m_row else 0
    completed_missions = m_row[1] if m_row and m_row[1] else 0

    conn.close()
    return {
        "user_id": user_id,
        "user_name": user_name,
        "goals": goals,
        "total_missions": total_missions,
        "completed_missions": completed_missions,
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
    with urllib.request.urlopen(req, timeout=6.0) as response:
        resp_bytes = response.read()
        return json.loads(resp_bytes.decode("utf-8"))


async def generate_coaching_response(user_message: str) -> Dict[str, Any]:
    # 1. Gather fast lightweight context in single DB call
    context = get_db_context()
    user_id = context["user_id"]
    user_name = context["user_name"]
    goals = context["goals"]
    goals_text = ", ".join([f"'{g['title']}'" for g in goals]) if goals else "Personal Mastery"
    completed_missions = context["completed_missions"]
    total_missions = context["total_missions"]

    # Save user prompt
    try:
        save_chat_message(user_id, "user", user_message)
    except Exception as err:
        raise RuntimeError(f"Database error saving prompt: {err}")

    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")

    # Fallback response if API key is not configured
    if not api_key or api_key.startswith("your_") or api_key == "placeholder":
        fallback_reply = (
            f"Focus locked in on '{user_message}', {user_name}! "
            f"You have completed {completed_missions}/{total_missions} protocols today. "
            f"Stay executing on '{goals_text}' with total discipline."
        )
        try:
            save_chat_message(user_id, "coach", fallback_reply)
        except Exception as err:
            raise RuntimeError(f"Database error saving fallback reply: {err}")

        return {
            "reply": fallback_reply,
            "context_used": True,
            "live_llm": False,
            "note": "Add GEMINI_API_KEY to backend/.env for live LLM response."
        }

    # 2. Fetch last 6 turns of conversation history for multi-turn context
    recent_history = fetch_chat_history(user_id, limit=6)

    # 3. Construct System Instructions & Multi-Turn Contents Payload
    system_instruction = (
        f"You are AI Coach, an elite, highly intelligent, disciplined personal growth and engineering mentor for {user_name}.\n"
        f"User Active Goals: {goals_text}\n"
        f"Today's Protocol Progress: {completed_missions}/{total_missions} completed.\n\n"
        f"GROUNDING INSTRUCTIONS:\n"
        f"1. Answer the user's explicit question FIRST, directly, accurately, and concisely (2-4 sentences).\n"
        f"2. Use personal mastery context ONLY when directly relevant to the user's prompt.\n"
        f"3. If the user asks a general knowledge or technical question, answer it clearly without forcing telemetry mentions.\n"
        f"4. Tone: Concise, inspiring, structured, disciplined, and practical."
    )

    contents = []
    # Add system context turn
    contents.append({
        "role": "user",
        "parts": [{"text": f"System Context: {system_instruction}"}]
    })
    contents.append({
        "role": "model",
        "parts": [{"text": f"Understood. I am ready to coach {user_name} with direct, accurate, and disciplined guidance."}]
    })

    # Add historical multi-turn messages
    for msg in recent_history:
        role = "user" if msg["sender"] == "user" else "model"
        # Skip the prompt we just inserted if already in history
        if msg["content"] == user_message and role == "user":
            continue
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })

    # Append current user prompt
    contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 250
        }
    }

    # Fast model selection
    candidate_models = ["gemini-flash-latest", "gemini-2.0-flash"]
    reply_text = None
    used_model = None
    last_error = None

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
            if err.code in (404, 400, 429):
                continue
        except Exception as err:
            last_error = str(err)
            continue

    if not reply_text:
        reply_text = (
            f"Executing on '{user_message}', {user_name}! "
            f"Protocols completed today: {completed_missions}/{total_missions}. "
            f"Keep focusing on '{goals_text}' with relentless consistency."
        )

    # Save coach reply
    try:
        save_chat_message(user_id, "coach", reply_text)
    except Exception as err:
        raise RuntimeError(f"Database error saving coach reply: {err}")

    return {
        "reply": reply_text,
        "context_used": True,
        "live_llm": bool(used_model),
        "model": used_model or "fallback",
        "error": last_error if not used_model else None
    }
