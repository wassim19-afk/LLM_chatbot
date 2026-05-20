#!/usr/bin/env python
"""Debug test for question 3"""

import requests
import time

BASE_URL = "http://127.0.0.1:8000"

# Créer une session simple
resp = requests.post(f"{BASE_URL}/api/session")
session_id = resp.json()["session_id"]
print(f"Session: {session_id[:12]}...")

# Question 1
print("\n📌 Q1: CA 2024?")
start = time.time()
resp = requests.post(f"{BASE_URL}/api/chat", json={"question": "CA 2024?", "session_id": session_id})
elapsed = time.time() - start
print(f"  ✓ Réponse en {elapsed:.2f}s")
print(f"  {resp.json().get('insight', '')[:80]}...")

# Question 3
print("\n📌 Q3: 2023?")
print("  ⏳ Attente (timeout 30s)...")
start = time.time()
try:
    resp = requests.post(
        f"{BASE_URL}/api/chat", 
        json={"question": "2023?", "session_id": session_id},
        timeout=30
    )
    elapsed = time.time() - start
    data = resp.json()
    if "detail" in data:
        print(f"  ❌ Erreur: {data.get('detail')}")
    else:
        print(f"  ✓ Réponse en {elapsed:.2f}s")
        print(f"  {data.get('insight', '')[:80]}...")
except requests.exceptions.Timeout:
    print(f"  ❌ Timeout après 30s")
except Exception as e:
    print(f"  ❌ Erreur: {e}")
