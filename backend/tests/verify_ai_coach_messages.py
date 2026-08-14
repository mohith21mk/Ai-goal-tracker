import os
import sys

# Ensure UTF-8 output encoding for emojis
sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from app.main import app
from app.services.auth import create_session

client = TestClient(app)
user_id = 1
session_token = create_session(user_id)
client.cookies.set("mkc_session", session_token)

test_prompts = [
    "hey",
    "how are you?",
    "thanks",
    "okay",
    "can you teach me Python?",
    "I don't understand variables",
    "give me another example",
    "why am I getting a CORS error?",
    "I'm tired",
    "I failed my exam",
    "motivate me",
    "how do I build consistency?",
    "what should I focus on today?",
    "analyze my current progress",
    "make me a study plan",
    "I feel like I'm wasting my time",
    "what should I do next?",
    "goodbye"
]

print("\n==================================================")
print("VERIFYING AI COACH 18-PROMPT TEST MATRIX (LIVE GEMINI)")
print("==================================================\n")

for idx, p in enumerate(test_prompts, 1):
    res = client.post("/api/coach/chat", json={"message": p})
    data = res.json()
    model_used = data.get("model", "fallback")
    reply = data.get("reply", "")
    status = res.status_code
    print(f"[{idx}] USER: '{p}' | STATUS: {status} | MODEL: {model_used}")
    print(f"    REPLY: {reply}")
    print("-" * 60)
