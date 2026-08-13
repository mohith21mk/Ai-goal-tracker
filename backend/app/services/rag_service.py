import math
import re
from typing import List, Dict, Any, Optional
from ..database import get_connection

def extract_user_context_documents(user_id: int) -> List[Dict[str, Any]]:
    """
    Extracts structured user context documents across Goals, Missions, Habits,
    Journal reflections, Life Blueprint, and live Telemetry for RAG retrieval.
    """
    conn = get_connection()
    cursor = conn.cursor()
    docs: List[Dict[str, Any]] = []

    # 1. Fetch User Profile
    cursor.execute("SELECT id, full_name, username, mkc_id, bio FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    if user_row:
        user_name = user_row["full_name"] or user_row["username"] or "User"
        docs.append({
            "doc_id": f"user_profile_{user_id}",
            "doc_type": "profile",
            "title": "User Identity & Profile",
            "content": f"User: {user_name} (MKC ID: {user_row['mkc_id'] or 'N/A'}). Bio: {user_row['bio'] or 'None'}"
        })

    # 2. Fetch Active & Recent Goals
    cursor.execute(
        "SELECT id, title, description, category, status, target_date FROM goals WHERE user_id = ? ORDER BY id DESC LIMIT 15",
        (user_id,)
    )
    for g in cursor.fetchall():
        desc = f": {g['description']}" if g['description'] else ""
        docs.append({
            "doc_id": f"goal_{g['id']}",
            "doc_type": "goal",
            "title": f"Goal: {g['title']}",
            "content": f"Goal '{g['title']}' [Category: {g['category']}, Status: {g['status']}, Target: {g['target_date'] or 'N/A'}]{desc}"
        })

    # 3. Fetch Missions (Completed & Pending)
    cursor.execute(
        "SELECT id, title, description, category, time, difficulty, xp_reward, completed, completed_at FROM missions WHERE user_id = ? ORDER BY id DESC LIMIT 30",
        (user_id,)
    )
    for m in cursor.fetchall():
        status = "Completed" if m["completed"] else "Pending Protocol"
        completed_str = f" on {m['completed_at']}" if m["completed_at"] and m["completed"] else ""
        docs.append({
            "doc_id": f"mission_{m['id']}",
            "doc_type": "mission",
            "title": f"Mission: {m['title']}",
            "content": f"Mission '{m['title']}' [{status}{completed_str}]. Category: {m['category']}, XP: {m['xp_reward']}, Time: {m['time']}, Difficulty: {m['difficulty']}."
        })

    # 4. Fetch Habits & Habit Log History
    cursor.execute(
        "SELECT id, title, category, frequency, target_days_per_week, status FROM habits WHERE user_id = ? ORDER BY id DESC LIMIT 15",
        (user_id,)
    )
    for h in cursor.fetchall():
        cursor.execute("SELECT COUNT(*) FROM habit_logs WHERE habit_id = ? AND user_id = ?", (h["id"], user_id))
        logs_count = cursor.fetchone()[0]
        docs.append({
            "doc_id": f"habit_{h['id']}",
            "doc_type": "habit",
            "title": f"Habit: {h['title']}",
            "content": f"Habit '{h['title']}' [Category: {h['category']}, Frequency: {h['frequency']}, Target Days/Wk: {h['target_days_per_week']}]. Total Logs: {logs_count} completions."
        })

    # 5. Fetch Journal Entries & Daily Reflections
    cursor.execute(
        """
        SELECT id, entry_date, mood, energy_level, wins_text, challenges_text, learnings_text, growth_next_text
        FROM journal_entries WHERE user_id = ? ORDER BY entry_date DESC LIMIT 10
        """,
        (user_id,)
    )
    for j in cursor.fetchall():
        docs.append({
            "doc_id": f"journal_{j['id']}",
            "doc_type": "journal",
            "title": f"Mindset Reflection ({j['entry_date']})",
            "content": (
                f"Journal Reflection on {j['entry_date']}: Mood={j['mood']}, Energy Level={j['energy_level']}/10. "
                f"Wins: {j['wins_text'] or 'None'}. Challenges: {j['challenges_text'] or 'None'}. "
                f"Learnings: {j['learnings_text'] or 'None'}. Next Growth Step: {j['growth_next_text'] or 'None'}."
            )
        })

    # 6. Fetch Life Blueprint Vision & Milestones
    cursor.execute("SELECT id, title, vision, status FROM life_blueprints WHERE user_id = ?", (user_id,))
    for bp in cursor.fetchall():
        docs.append({
            "doc_id": f"blueprint_{bp['id']}",
            "doc_type": "blueprint",
            "title": f"Life Blueprint: {bp['title']}",
            "content": f"Life Blueprint '{bp['title']}' [Status: {bp['status']}]. Vision: {bp['vision'] or 'N/A'}."
        })

    conn.close()

    # Add Telemetry Summary Doc
    from ..api.progress import compute_telemetry_sync
    try:
        telem = compute_telemetry_sync(user_id)
        docs.append({
            "doc_id": f"telemetry_{user_id}",
            "doc_type": "telemetry",
            "title": "Current Telemetry & Performance Index",
            "content": (
                f"Live Telemetry: Discipline Score={telem.get('discipline_score', 0)}/100 (Change: {telem.get('discipline_score_change', 0)}), "
                f"Mindset Strength={telem.get('mindset_strength', 0)}/100 (Change: {telem.get('mindset_strength_change', 0)}), "
                f"Consistency={telem.get('consistency', 0)}/100 (Change: {telem.get('consistency_change', 0)}), "
                f"Growth Index={telem.get('growth_index', 0)}/100, Financial Freedom Goal={telem.get('financial_goal', 0)}%, "
                f"Discipline Streak={telem.get('streak_days', 0)} Days, XP Earned={telem.get('xp_earned', 0)} Total XP."
            )
        })
    except Exception:
        pass

    return docs


def tokenize(text: str) -> List[str]:
    """Tokenizes string into lowercase alphanumeric words."""
    return re.findall(r"\w+", text.lower())


def compute_vector_similarity(query_tokens: List[str], doc_content: str) -> float:
    """
    Computes keyword vector similarity score between query tokens and document passage.
    Includes term frequency, keyword weighting, and exact matching boost.
    """
    if not query_tokens or not doc_content:
        return 0.0

    doc_tokens = tokenize(doc_content)
    if not doc_tokens:
        return 0.0

    doc_token_counts: Dict[str, int] = {}
    for t in doc_tokens:
        doc_token_counts[t] = doc_token_counts.get(t, 0) + 1

    score = 0.0
    for q in set(query_tokens):
        if q in doc_token_counts:
            tf = doc_token_counts[q] / len(doc_tokens)
            # Add length-normalized TF boost
            score += tf * (1.0 + math.log(1.0 + len(q)))

    # Boost score if document contains key category tokens (e.g. consistency, habits, mindset)
    for q in query_tokens:
        if q in ("consistency", "habits", "habit", "journal", "reflection", "streak", "mindset", "goal", "mission"):
            if q in doc_content.lower():
                score += 0.5

    return score


def search_relevant_context(user_id: int, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieves the top_k most relevant user context passages using RAG similarity search.
    """
    docs = extract_user_context_documents(user_id)
    if not docs:
        return []

    query_tokens = tokenize(query)
    if not query_tokens:
        return docs[:top_k]

    scored_docs = []
    for doc in docs:
        sim_score = compute_vector_similarity(query_tokens, doc["content"])
        scored_docs.append({
            "doc": doc,
            "similarity_score": sim_score
        })

    # Sort descending by similarity score
    scored_docs.sort(key=lambda x: x["similarity_score"], reverse=True)

    # Return top_k docs
    return [item["doc"] for item in scored_docs[:top_k]]


def build_rag_coaching_prompt(user_id: int, query: str) -> Dict[str, Any]:
    """
    Assembles a high-context RAG prompt injecting retrieved user passages + live telemetry context.
    """
    relevant_passages = search_relevant_context(user_id, query, top_k=5)
    
    passage_texts = []
    for idx, p in enumerate(relevant_passages, 1):
        passage_texts.append(f"[{idx}] ({p['doc_type'].upper()}) {p['title']}: {p['content']}")

    retrieved_context_str = "\n".join(passage_texts) if passage_texts else "No specific user documents retrieved."

    system_prompt = (
        "You are MASTERY KEY COACH (MKC), an elite AI performance and mindset coach. "
        "Provide direct, high-leverage, personalized coaching advice grounded strictly in the user's actual MKC data. "
        "Never offer generic fluff. Analyze their goals, mission completions, habits, streak, energy levels, and reflections."
    )

    user_prompt = (
        f"USER QUESTION: \"{query}\"\n\n"
        f"RETRIEVED USER MKC CONTEXT (RAG Passages):\n"
        f"{retrieved_context_str}\n\n"
        f"INSTRUCTION: Answer the user's question specifically using their retrieved MKC data. "
        f"Point out exact metrics, habits, or reflection notes where applicable."
    )

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "retrieved_passages": relevant_passages
    }
