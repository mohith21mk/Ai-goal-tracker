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
    cursor.execute("SELECT title, category FROM goals WHERE status = 'active' LIMIT 5")
    goal_rows = cursor.fetchall()
    goals = [dict(r) for r in goal_rows]

    # Fetch fast mission summary
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) FROM missions")
    m_row = cursor.fetchone()
    total_missions = m_row[0] if m_row else 0
    completed_missions = m_row[1] if m_row and m_row[1] else 0

    # Fetch coach style from user settings
    cursor.execute("SELECT coach_style FROM user_settings WHERE user_id = ?", (user_id,))
    s_row = cursor.fetchone()
    coach_style = s_row["coach_style"] if s_row and s_row["coach_style"] else "strategic"

    conn.close()
    return {
        "user_id": user_id,
        "user_name": user_name,
        "goals": goals,
        "total_missions": total_missions,
        "completed_missions": completed_missions,
        "coach_style": coach_style,
    }


def get_detailed_context(user_id: int) -> Dict[str, Any]:
    """Fetch richer app data for data-aware questions (missions, habits, goals)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # All missions with status
    cursor.execute("SELECT title, completed FROM missions ORDER BY id ASC")
    missions = [dict(r) for r in cursor.fetchall()]

    # Active goals with details
    cursor.execute("SELECT title, category, status FROM goals ORDER BY id ASC LIMIT 10")
    goals = [dict(r) for r in cursor.fetchall()]

    # Habits with status
    cursor.execute("SELECT title, frequency, status FROM habits ORDER BY id ASC LIMIT 10")
    habits = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "missions": missions,
        "goals": goals,
        "habits": habits,
    }


def _needs_app_data(message: str) -> bool:
    """Lightweight intent detection: does the question reference personal app data?"""
    lower = message.lower()
    data_keywords = [
        "task", "mission", "goal", "habit", "streak", "progress",
        "remaining", "pending", "incomplete", "completed", "done",
        "today", "focus", "priority", "what should i",
        "how many", "how much", "list my", "show my", "what are my",
        "what are they", "what is my", "tell me my",
    ]
    return any(kw in lower for kw in data_keywords)


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
    with urllib.request.urlopen(req, timeout=25.0) as response:
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

    # 2. Build richer context if the question references app data
    detailed_context_block = ""
    if _needs_app_data(user_message):
        detailed = get_detailed_context(user_id)
        # Format missions
        if detailed["missions"]:
            pending = [m["title"] for m in detailed["missions"] if not m["completed"]]
            done = [m["title"] for m in detailed["missions"] if m["completed"]]
            detailed_context_block += f"\n\nUSER'S CURRENT MISSIONS ({len(pending)} pending, {len(done)} completed):\n"
            for i, t in enumerate(pending, 1):
                detailed_context_block += f"  {i}. [PENDING] {t}\n"
            for i, t in enumerate(done, len(pending) + 1):
                detailed_context_block += f"  {i}. [DONE] {t}\n"
        # Format goals
        if detailed["goals"]:
            detailed_context_block += f"\nUSER'S GOALS:\n"
            for g in detailed["goals"]:
                detailed_context_block += f"  - {g['title']} ({g['category']}, {g['status']})\n"
        # Format habits
        if detailed["habits"]:
            detailed_context_block += f"\nUSER'S HABITS:\n"
            for h in detailed["habits"]:
                detailed_context_block += f"  - {h['title']} ({h['frequency']}, status: {h['status']})\n"

    # 3. Fetch last 6 turns of conversation history for multi-turn context
    recent_history = fetch_chat_history(user_id, limit=6)

    coach_style = context.get("coach_style", "strategic")
    style_directives = {
        "strategic": "Tone & Style: Strategic, direct, analytical, data-driven, precise.",
        "empathetic": "Tone & Style: Empathetic, supportive, encouraging, understanding, emotionally intelligent.",
        "relentless": "Tone & Style: Relentless, high-intensity, non-negotiable execution, demanding peak performance, zero excuses."
    }
    tone_directive = style_directives.get(str(coach_style).lower(), style_directives["strategic"])

    # 4. Construct System Instructions & Multi-Turn Contents Payload
    system_instruction = (
        f"You are AI Coach, an elite, highly intelligent, disciplined personal growth and engineering mentor for {user_name}.\n"
        f"User Active Goals: {goals_text}\n"
        f"Today's Protocol Progress: {completed_missions}/{total_missions} completed.\n"
        f"{detailed_context_block}\n"
        f"GROUNDING INSTRUCTIONS:\n"
        f"1. Answer the user's explicit question FIRST, directly, accurately, and completely.\n"
        f"2. When the user asks about their tasks, missions, goals, habits, or progress, use the EXACT data provided above. List them by name. Never invent data.\n"
        f"3. If the user asks a general knowledge or technical question, answer it clearly without forcing personal data mentions.\n"
        f"4. Always finish your sentences completely. Never stop mid-sentence.\n"
        f"5. {tone_directive}"
    )

    contents = []
    # Add system context turn
    contents.append({
        "role": "user",
        "parts": [{"text": f"System Context: {system_instruction}"}]
    })
    contents.append({
        "role": "model",
        "parts": [{"text": f"Understood. I am ready to coach {user_name} with direct, accurate, and disciplined guidance using your real data."}]
    })

    # Add historical multi-turn messages — use ID-based dedup, not content matching
    current_msg_ids = set()
    for msg in recent_history:
        role = "user" if msg["sender"] == "user" else "model"
        msg_id = msg.get("id")
        if msg_id in current_msg_ids:
            continue
        current_msg_ids.add(msg_id)
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })

    # Append current user prompt (the one we just saved is in history,
    # but we add it explicitly to ensure it's the final turn)
    # Check if the last content entry is already this exact user message
    if not contents or contents[-1].get("role") != "user" or contents[-1]["parts"][0]["text"] != user_message:
        contents.append({
            "role": "user",
            "parts": [{"text": user_message}]
        })

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 2048
        }
    }

    # Fast model selection
    candidate_models = ["gemini-2.0-flash", "gemini-flash-latest"]
    reply_text = None
    used_model = None
    last_error = None

    for model_name in candidate_models:
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            data = await asyncio.to_thread(_call_gemini_rest_api, gemini_url, payload)
            candidates = data.get("candidates", [])
            if not candidates:
                last_error = "No candidates returned by model"
                continue

            candidate = candidates[0]
            finish_reason = candidate.get("finishReason", "")

            # Extract full text from all parts
            content_obj = candidate.get("content", {})
            parts = content_obj.get("parts", [])
            full_text_parts = [p["text"] for p in parts if "text" in p]
            extracted_text = "".join(full_text_parts).strip()

            if not extracted_text:
                last_error = f"Empty response from {model_name}"
                continue

            # Handle responses that hit MAX_TOKENS — trim to last complete sentence
            if finish_reason == "MAX_TOKENS":
                if extracted_text and extracted_text[-1] not in ".!?)\"'":
                    # Trim to last punctuation mark
                    last_punct = max(
                        extracted_text.rfind('.'),
                        extracted_text.rfind('!'),
                        extracted_text.rfind('?'),
                    )
                    if last_punct > 50:
                        extracted_text = extracted_text[:last_punct + 1].strip()

            reply_text = extracted_text
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
