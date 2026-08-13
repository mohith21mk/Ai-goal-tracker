import os
import sys
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
    "can you teach me python?",
    "I don't understand variables",
    "give me another example",
    "why am I getting a CORS error?",
    "I'm tired today",
    "I failed my exam",
    "motivate me",
    "what should I study today?",
    "thanks",
    "okay",
    "I don't understand",
    "what did you mean by that?",
    "help me plan tomorrow",
    "write a Python program to reverse a string",
    "explain that code",
    "I'm feeling lazy"
]

print("\n==================================================")
print("VERIFYING AI COACH 18-PROMPT TEST MATRIX")
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
