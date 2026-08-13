import pytest
from app.database import init_db, get_connection
from app.services.rag_service import extract_user_context_documents, search_relevant_context, build_rag_coaching_prompt
from app.services.ai_coach import generate_coaching_response
import asyncio

def setup_module(module):
    init_db()

def test_rag_context_extraction_and_vector_search():
    conn = get_connection()
    cursor = conn.cursor()

    # Clean test user
    cursor.execute("DELETE FROM users WHERE username = 'rag_test_user'")
    conn.commit()

    # 1. Create test user with Goals, Missions, Habits, and Reflections
    cursor.execute("INSERT INTO users (username, email, full_name) VALUES ('rag_test_user', 'rag@example.com', 'RAG Test User')")
    user_id = cursor.lastrowid
    conn.commit()

    cursor.execute("INSERT INTO goals (user_id, title, category, status) VALUES (?, 'Build AI Application', 'career', 'active')", (user_id,))
    cursor.execute("INSERT INTO missions (user_id, title, category, completed, xp_reward) VALUES (?, 'Implement Vector Embeddings', 'career', 1, 25)", (user_id,))
    cursor.execute("INSERT INTO habits (user_id, title, category, frequency) VALUES (?, 'Morning Deep Work', 'focus', 'daily')", (user_id,))
    cursor.execute("INSERT INTO journal_entries (user_id, entry_date, mood, energy_level, wins_text, challenges_text) VALUES (?, '2026-08-12', 'focused', 9, 'Vector similarity engine operational', 'Context token limits')", (user_id,))
    conn.commit()

    try:
        # 2. Extract documents
        docs = extract_user_context_documents(user_id)
        assert len(docs) >= 4
        doc_types = [d["doc_type"] for d in docs]
        assert "goal" in doc_types
        assert "mission" in doc_types
        assert "habit" in doc_types
        assert "journal" in doc_types

        # 3. Vector Similarity Search for "consistency and habits"
        relevant = search_relevant_context(user_id, "Why am I losing consistency in my habits?", top_k=3)
        assert len(relevant) >= 1
        relevant_types = [r["doc_type"] for r in relevant]
        assert "habit" in relevant_types or "journal" in relevant_types or "telemetry" in relevant_types

        # 4. Build RAG prompt
        rag_prompt = build_rag_coaching_prompt(user_id, "How can I improve my deep work consistency?")
        assert "RETRIEVED USER MKC CONTEXT" in rag_prompt["user_prompt"]
        assert len(rag_prompt["retrieved_passages"]) >= 1

        # 5. Generate RAG AI Coach Response
        res = asyncio.run(generate_coaching_response("How can I improve my deep work consistency?", user_id))
        assert "reply" in res
        assert isinstance(res["reply"], str) and len(res["reply"]) > 0
        # Verify no raw context leakage in output
        assert "Insights retrieved:" not in res["reply"]
        assert "User Identity & Profile:" not in res["reply"]
        assert "MKC ID:" not in res["reply"]

    finally:
        cursor.execute("DELETE FROM journal_entries WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM habits WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM missions WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()


def test_ai_coach_mocked_llm_response(monkeypatch):
    """
    Verifies that when LLM returns a live response, the coach returns the exact response
    without appending raw RAG context or hardcoded slogans.
    """
    from app.services import ai_coach

    def mock_gemini_api(url, payload):
        return {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"reply": "Absolutely. Let\'s break down Python step-by-step starting with variables.", "action": null}'
                    }]
                }
            }]
        }

    monkeypatch.setattr(ai_coach, "_call_gemini_rest_api", mock_gemini_api)
    monkeypatch.setattr(ai_coach.settings, "GEMINI_API_KEY", "mock_key_123")

    res = asyncio.run(ai_coach.generate_coaching_response("Can you teach me Python?", 1))
    assert res["live_llm"] is True
    assert res["reply"] == "Absolutely. Let's break down Python step-by-step starting with variables."
    assert "Insights retrieved" not in res["reply"]

