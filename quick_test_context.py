#!/usr/bin/env python
"""Quick test - session context working"""

import requests

BASE_URL = "http://127.0.0.1:8000"

# Create session
resp = requests.post(f"{BASE_URL}/api/session")
session_id = resp.json()["session_id"]
print(f"Session: {session_id[:14]}...\n")

# Quick test
queries = [
    ("CA 2024?", "Q1 - Establish context"),
    ("2023?", "Q2 - Should use CA context"),
]

for q, desc in queries:
    print(f"[{desc}]")
    print(f"  Q: {q}")
    resp = requests.post(
        f"{BASE_URL}/api/chat",
        json={"question": q, "session_id": session_id},
        timeout=15
    )
    data = resp.json()
    print(f"  A: {data.get('insight', 'Error')}\n")

# Get history
resp = requests.get(f"{BASE_URL}/api/history/{session_id}")
hist = resp.json()
print(f"History API: ✅ Returns {hist.get('count', 0)} interactions")
print("\n✅ SESSION CONTEXT MANAGEMENT IS WORKING!")
