import os
import json
import sqlite3
import urllib.request
import urllib.error
import asyncio
import time
from typing import Dict, Any, List
from pathlib import Path

from ..config import settings
from .logger import logger

from ..database import get_connection as get_db_connection


def get_db_context(user_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch user details
    cursor.execute("SELECT id, full_name, username FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    user_name = (user_row["full_name"] if user_row and user_row["full_name"] else f"@{user_row['username']}") if user_row else "Member"

    # Fetch active goals for this user
    cursor.execute("SELECT title, category FROM goals WHERE user_id = ? AND status = 'active' LIMIT 5", (user_id,))
    goal_rows = cursor.fetchall()
    goals = [dict(r) for r in goal_rows]

    # Fetch fast mission summary for this user
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) FROM missions WHERE user_id = ?", (user_id,))
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
    """Fetch richer app data for data-aware questions (missions, habits, goals, journal, blueprint)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # All missions with status
    cursor.execute("SELECT id, title, completed FROM missions WHERE user_id = ? ORDER BY id ASC", (user_id,))
    missions = [dict(r) for r in cursor.fetchall()]

    # Active goals with details
    cursor.execute("SELECT id, title, category, status FROM goals WHERE user_id = ? AND status = 'active' ORDER BY id ASC LIMIT 10", (user_id,))
    goals = [dict(r) for r in cursor.fetchall()]

    # Habits with status
    cursor.execute("SELECT id, title, frequency, status FROM habits WHERE user_id = ? AND status = 'active' ORDER BY id ASC LIMIT 10", (user_id,))
    habits = [dict(r) for r in cursor.fetchall()]
    
    # Recent Habit Logs (last 7 days)
    cursor.execute(
        """
        SELECT habit_id, completed_date 
        FROM habit_logs 
        WHERE user_id = ? 
        ORDER BY completed_date DESC LIMIT 20
        """, (user_id,)
    )
    habit_logs_raw = cursor.fetchall()
    habit_logs = {}
    for r in habit_logs_raw:
        hid = r["habit_id"]
        if hid not in habit_logs:
            habit_logs[hid] = []
        habit_logs[hid].append(r["completed_date"])
    
    # Recent Journal Entries
    cursor.execute("SELECT entry_date, mood, energy_level, wins_text, challenges_text FROM journal_entries WHERE user_id = ? ORDER BY entry_date DESC LIMIT 3", (user_id,))
    journals = [dict(r) for r in cursor.fetchall()]
    
    # Active Blueprint Phases
    cursor.execute(
        """
        SELECT p.title, p.description, p.phase_number, p.status 
        FROM blueprint_phases p
        JOIN life_blueprints b ON p.blueprint_id = b.id
        WHERE b.user_id = ? AND b.status = 'active' AND p.status = 'active'
        ORDER BY p.phase_number ASC LIMIT 3
        """, (user_id,)
    )
    blueprints = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "missions": missions,
        "goals": goals,
        "habits": habits,
        "habit_logs": habit_logs,
        "journals": journals,
        "blueprints": blueprints,
    }


def _needs_app_data(message: str) -> bool:
    """Lightweight intent detection: does the question reference personal app data?"""
    lower = message.lower()
    data_keywords = [
        "task", "mission", "goal", "habit", "streak", "progress",
        "remaining", "pending", "incomplete", "completed", "done",
        "today", "focus", "priority", "what should i",
        "how many", "how much", "list my", "show my", "what are my",
        "what are they", "what is my", "tell me my", "journal", "mood",
        "energy", "win", "challenge", "blueprint", "phase", "plan",
        "do next", "recommend", "action"
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


def log_ai_activity(user_id: int, action_type: str, target_id: int, status: str, latency_ms: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO ai_activity_logs (user_id, action_type, target_id, status, latency_ms) VALUES (?, ?, ?, ?, ?)",
            (user_id, action_type, target_id, status, latency_ms)
        )
        conn.commit()
    except Exception as e:
        print(f"Error logging AI activity: {e}")
    finally:
        conn.close()


def validate_ai_action(action: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    if not action or action.get("type") == "NONE" or not action.get("type"):
        return None
    
    action_type = action.get("type")
    target_id = action.get("target_id")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if action_type in ["NAVIGATE_MISSION", "START_MISSION", "MARK_MISSION_COMPLETE"]:
            if target_id:
                cursor.execute("SELECT id FROM missions WHERE id = ? AND user_id = ?", (target_id, user_id))
                if not cursor.fetchone():
                    return None
            return action
        elif action_type in ["LOG_HABIT", "LOG_HABIT_COMPLETE"]:
            if target_id:
                cursor.execute("SELECT id FROM habits WHERE id = ? AND user_id = ?", (target_id, user_id))
                if not cursor.fetchone():
                    return None
            return action
        elif action_type in ["NAVIGATE_GOALS", "NAVIGATE_HABITS", "NAVIGATE_JOURNAL", "NAVIGATE_BLUEPRINT", "VIEW_PROGRESS"]:
            return action
        else:
            return None
    finally:
        conn.close()


def _call_gemini_rest_api(gemini_url: str, payload: dict) -> Dict[str, Any]:
    json_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        gemini_url,
        data=json_bytes,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30.0) as response:
        resp_bytes = response.read()
        return json.loads(resp_bytes.decode("utf-8"))


def _extract_reply_and_action(extracted_text: str) -> tuple[str, Optional[Dict[str, Any]]]:
    if not extracted_text:
        return "", None

    clean_text = extracted_text.strip()

    # Strip markdown code fences if present (e.g. ```json ... ``` or ``` ...)
    if clean_text.startswith("```"):
        lines = clean_text.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        clean_text = "\n".join(lines).strip()

    # Try parsing JSON
    try:
        data = json.loads(clean_text)
        if isinstance(data, dict):
            reply = (
                data.get("reply") or
                data.get("response") or
                data.get("answer") or
                data.get("text") or
                data.get("coaching_reply") or
                data.get("message") or
                ""
            )
            action = data.get("action")
            if isinstance(reply, str) and reply.strip():
                return reply.strip(), action if isinstance(action, dict) else None
    except json.JSONDecodeError:
        pass

    # Direct plain text fallback
    return clean_text, None


async def generate_coaching_response(user_message: str, user_id: int) -> Dict[str, Any]:
    from .rag_service import build_rag_coaching_prompt

    logger.info(f"[AI Coach] Received chat message for user_id={user_id}: '{user_message}'")

    # 1. Gather RAG Context & Passages
    rag_data = build_rag_coaching_prompt(user_id, user_message)
    retrieved_passages = rag_data.get("retrieved_passages", [])
    logger.info(f"[AI Coach] Context retrieved: {len(retrieved_passages)} RAG passages")
    
    # 2. Gather fast lightweight context in single DB call
    context = get_db_context(user_id)
    user_id = context["user_id"]
    user_name = context["user_name"]
    goals = context["goals"]
    goals_text = ", ".join([f"'{g['title']}'" for g in goals]) if goals else "Personal Growth"
    completed_missions = context["completed_missions"]
    total_missions = context["total_missions"]

    needs_app_data = _needs_app_data(user_message)
    logger.info(f"[AI Coach] App data requirement detected: {needs_app_data}")

    # Save user prompt
    try:
        save_chat_message(user_id, "user", user_message)
    except Exception as err:
        logger.error(f"[AI Coach] Database error saving prompt: {err}")
        raise RuntimeError(f"Database error saving prompt: {err}")

    start_time = time.time()
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")

    # Check API Key
    if not api_key or api_key.startswith("your_") or api_key == "placeholder":
        logger.warning(f"[AI Coach] AI_COACH_FALLBACK_TRIGGERED reason=GEMINI_API_KEY is not configured in environment")
        fallback_reply = "I'm having trouble connecting to my AI brain right now. Give me another try in a moment."
        try:
            save_chat_message(user_id, "coach", fallback_reply)
        except Exception as err:
            logger.error(f"[AI Coach] Database error saving fallback reply: {err}")

        return {
            "reply": fallback_reply,
            "context_used": True,
            "live_llm": False,
            "note": "Add GEMINI_API_KEY to backend/.env for live LLM response."
        }

    # Build RAG passages block for system prompt (internal context ONLY)
    rag_context_snippets = []
    for p in retrieved_passages[:5]:
        rag_context_snippets.append(f"  - [{p['doc_type'].upper()}] {p['title']}: {p['content']}")
    rag_block = "\n".join(rag_context_snippets) if rag_context_snippets else "None"

    # Build richer context if the question references app data
    detailed_context_block = ""
    if needs_app_data:
        detailed = get_detailed_context(user_id)
        if detailed["missions"]:
            pending = [m for m in detailed["missions"] if not m["completed"]]
            done = [m for m in detailed["missions"] if m["completed"]]
            detailed_context_block += f"\nUSER'S MISSIONS ({len(pending)} pending, {len(done)} completed):\n"
            for m in pending:
                detailed_context_block += f"  - ID: {m['id']} | [PENDING] {m['title']}\n"
            for m in done:
                detailed_context_block += f"  - ID: {m['id']} | [DONE] {m['title']}\n"
        if detailed["goals"]:
            detailed_context_block += f"\nUSER'S GOALS:\n"
            for g in detailed["goals"]:
                detailed_context_block += f"  - ID: {g['id']} | {g['title']} ({g['category']})\n"
        if detailed["habits"]:
            detailed_context_block += f"\nUSER'S HABITS:\n"
            for h in detailed["habits"]:
                detailed_context_block += f"  - ID: {h['id']} | {h['title']} ({h['frequency']})\n"

    # Fetch last 6 turns of conversation history
    recent_history = fetch_chat_history(user_id, limit=6)

    coach_style = context.get("coach_style", "strategic")
    # System Instructions for ChatGPT-Style Natural Conversational Mentor
    system_instruction = (
        f"You are AI Coach, a warm, highly intelligent, calm, and practical human mentor (like ChatGPT).\n"
        f"\n"
        f"USER BACKGROUND CONTEXT (Private background context ONLY. NEVER output or leak raw context, IDs, database names, or metadata):\n"
        f"- User Name: {user_name}\n"
        f"- Primary Goals: {goals_text}\n"
        f"- Task Progress Today: {completed_missions}/{total_missions} completed.\n"
        f"Retrieved Passages:\n{rag_block}\n"
        f"{detailed_context_block}\n"
        f"\n"
        f"CORE CONVERSATIONAL PRINCIPLES (THINK & ACT LIKE CHATGPT):\n"
        f"1. SITUATION-AWARE RESPONSE STYLE & LENGTH:\n"
        f"   - Casual / Greetings ('hey', 'what's up?', 'how's your day going?'): Respond naturally in 1-2 short, warm sentences (e.g. 'Hey! 👋 What's up?' or 'Hey! How's your day going?'). Never repeatedly say 'Great to see you today'.\n"
        f"   - Thanks / Acknowledgments ('thanks', 'okay', 'cool', 'goodbye'): Keep it very short and human (e.g. 'Anytime! 🙂' or 'You got it. Talk soon!'). Do NOT generate a long coaching essay.\n"
        f"   - Learning / Teaching ('can you teach me Python?', 'explain recursion'): Teach progressively and conversationally. Do not dump a massive course outline at once. Start with the core idea (like variables), use an intuitive analogy (like a labeled box), show a tiny code snippet, and explain naturally.\n"
        f"   - Follow-Ups / Continuation ('I don't understand variables', 'why?', 'give me another example'): Build seamlessly on the previous turn in the conversation. Do NOT restart the entire explanation or re-introduce yourself.\n"
        f"   - Technical / Coding ('why am I getting a CORS error?', 'reverse a string'): Answer the technical question directly with clean code and concise explanation. Do NOT insert motivational speeches or tell the user to 'stay consistent'.\n"
        f"   - Frustration / Emotional ('I'm tired', 'I failed my exam', 'I'm feeling lazy'): Acknowledge feelings with genuine human empathy. Do NOT automatically produce a 5-step productivity framework or use overly polished/robotic stock phrases like 'That's completely natural' or 'The engine doesn't want to turn over'. Talk like a real friend.\n"
        f"   - Motivation ('motivate me'): Give practical, grounded encouragement—avoid motivational-poster clichés.\n"
        f"   - Planning ('what should I focus on today?', 'make me a study plan'): Act as a coach using user's background goals, habits, and missions.\n"
        f"2. NO MANDATORY RESPONSE STRUCTURE: Never force every reply to contain an acknowledgement, insight, action plan, motivation, bullet points, or a question at the end. Use headings or bullet points ONLY when they genuinely clarify complex technical topics.\n"
        f"3. ELIMINATE REPETITIVE STOCK BUZZWORDS: Avoid habitual repetition of stock coaching phrases like 'That's completely natural', 'Let's break this down', 'Here's the thing', 'Absolutely', 'Great to see you', 'Take a small step', 'You've got this', 'Stay consistent', 'Focus on', 'Keep pushing', 'One step at a time', 'Protocol', 'Discipline'. Use varied, natural phrasing.\n"
        f"4. INVISIBLE RAG & PRIVATE CONTEXT: Never output 'Insights retrieved:', 'User Identity & Profile:', 'MKC ID:', or raw database metadata. Only refer to the user's goals or progress when directly relevant.\n"
        f"5. DO NOT OVERUSE NAME: Use {user_name}'s name only when naturally meaningful. Never start messages with '{user_name}!'.\n"
        f"6. OUTPUT FORMAT: Return a valid JSON object matching: {{ 'reply': '...', 'action': ... }}."
    )

    contents = []
    contents.append({
        "role": "user",
        "parts": [{"text": f"System Context: {system_instruction}"}]
    })
    contents.append({
        "role": "model",
        "parts": [{"text": f"Understood. I am ready to converse naturally, warmly, and accurately as a supportive mentor for {user_name}."}]
    })

    # Historical multi-turn turns
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

    # Append current user prompt
    if not contents or contents[-1].get("role") != "user" or contents[-1]["parts"][0]["text"] != user_message:
        contents.append({
            "role": "user",
            "parts": [{"text": user_message}]
        })

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.6,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "reply": {
                        "type": "STRING",
                        "description": "Your coaching response text to show the user."
                    },
                    "action": {
                        "type": "OBJECT",
                        "description": "Optional actionable command for the user interface.",
                        "properties": {
                            "type": {
                                "type": "STRING",
                                "enum": ["NAVIGATE_MISSION", "START_MISSION", "MARK_MISSION_COMPLETE", "NAVIGATE_GOALS", "LOG_HABIT", "LOG_HABIT_COMPLETE", "NAVIGATE_JOURNAL", "NAVIGATE_BLUEPRINT", "VIEW_PROGRESS", "NONE"],
                                "description": "The type of action. NONE if no action is needed."
                            },
                            "target_id": {
                                "type": "INTEGER",
                                "description": "The ID of the mission or habit if applicable."
                            }
                        }
                    }
                },
                "required": ["reply"]
            }
        }
    }

    # Dynamically build candidate models list with active config + fallback models
    configured_model = settings.GEMINI_MODEL or os.getenv("GEMINI_MODEL", "")
    candidate_models = []
    if configured_model:
        candidate_models.append(configured_model)
    
    for fallback in ["gemini-3.6-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest", "gemini-1.5-pro"]:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    reply_text = None
    action_payload = None
    used_model = None
    last_error = None
    action_status = "success"

    for model_name in candidate_models:
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        logger.info(f"[AI Coach] Sending LLM request to Gemini model '{model_name}'")
        try:
            data = await asyncio.to_thread(_call_gemini_rest_api, gemini_url, payload)
            candidates = data.get("candidates", [])
            if not candidates:
                last_error = f"No candidates returned by {model_name}"
                logger.warning(f"[AI Coach] {last_error}")
                continue

            candidate = candidates[0]
            content_obj = candidate.get("content", {})
            parts = content_obj.get("parts", [])
            full_text_parts = [p.get("text", "") for p in parts]
            extracted_text = "".join(full_text_parts).strip()

            if not extracted_text:
                last_error = f"Empty text response from {model_name}"
                logger.warning(f"[AI Coach] {last_error}")
                continue

            extracted_reply, extracted_action = _extract_reply_and_action(extracted_text)
            if extracted_reply:
                reply_text = extracted_reply
                action_payload = extracted_action
                used_model = model_name
                logger.info(f"[AI Coach] LLM success with '{used_model}'. Response length: {len(reply_text)} chars")
                break
            else:
                last_error = f"Could not extract valid reply string from {model_name} response"
                logger.warning(f"[AI Coach] {last_error}")
                continue

        except urllib.error.HTTPError as err:
            err_detail = ""
            try:
                err_detail = err.read().decode("utf-8")
            except Exception:
                pass
            last_error = f"HTTP {err.code}: {err.reason} - {err_detail}"
            logger.warning(f"[AI Coach] Model '{model_name}' HTTP error: {last_error}")
            continue
        except Exception as err:
            last_error = f"Exception: {err}"
            logger.warning(f"[AI Coach] Model '{model_name}' error: {last_error}")
            continue

    if action_payload:
        validated_action = validate_ai_action(action_payload, user_id)
        if not validated_action and action_payload.get("type") and action_payload.get("type") != "NONE":
            action_payload = None
            action_status = "rejected"
        else:
            action_payload = validated_action

    # If LLM failed, log explicit fallback trigger and return honest error
    if not reply_text:
        logger.warning(f"[AI Coach] AI_COACH_FALLBACK_TRIGGERED reason={last_error or 'All LLM candidate models failed'}")
        reply_text = "I'm having trouble connecting to my AI brain right now. Give me another try in a moment."

    # Save coach reply
    try:
        save_chat_message(user_id, "coach", reply_text)
    except Exception as err:
        logger.error(f"[AI Coach] Database error saving coach reply: {err}")
        raise RuntimeError(f"Database error saving coach reply: {err}")

    end_time = time.time()
    latency_ms = int((end_time - start_time) * 1000)

    act_type = action_payload.get("type") if action_payload else None
    act_target = action_payload.get("target_id") if action_payload else None

    try:
        log_ai_activity(user_id, act_type, act_target, action_status, latency_ms)
    except Exception as e:
        logger.warning(f"[AI Coach] Telemetry logging failed: {e}")

    return {
        "reply": reply_text,
        "action": action_payload,
        "context_used": True,
        "live_llm": bool(used_model),
        "model": used_model or "fallback",
        "error": last_error if not used_model else None
    }
