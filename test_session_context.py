#!/usr/bin/env python
"""Test if context is being used across session"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("\n🧪 Testing Session Context Management\n" + "="*60)

# Create session
resp = requests.post(f"{BASE_URL}/api/session")
session_id = resp.json()["session_id"]
print(f"\n✓ Session créée: {session_id[:12]}...")

# Q1: Establish a metric context
q1 = "CA 2024?"
print(f"\n📌 Q1: {q1}")
resp = requests.post(f"{BASE_URL}/api/chat", json={"question": q1, "session_id": session_id})
data = resp.json()
sql_q1 = data.get('sql_query', '')
print(f"   SQL: {sql_q1[:100]}...")
print(f"   Response: {data.get('insight', '')[:80]}...")

# Q2: Simple follow-up - should use CA context
q2 = "2023?"
print(f"\n📌 Q2: {q2} (should get CA 2023, not something else)")
resp = requests.post(f"{BASE_URL}/api/chat", json={"question": q2, "session_id": session_id})
data = resp.json()
sql_q2 = data.get('sql_query', '')
print(f"   SQL: {sql_q2[:100]}...")
print(f"   Response: {data.get('insight', '')[:80]}...")

# Check if the SQL looks like it's grouping by year (suggesting CA context was used)
if "YEAR(" in sql_q2 and "SUM(" in sql_q2:
    print("   ✅ CA context detected (has YEAR + SUM)")
else:
    print("   ⚠️  Context may not be used properly")

# Q3: Another follow-up
q3 = "et 2022?"
print(f"\n📌 Q3: {q3} (comparing years)")
resp = requests.post(f"{BASE_URL}/api/chat", json={"question": q3, "session_id": session_id})
data = resp.json()
sql_q3 = data.get('sql_query', '')
print(f"   SQL: {sql_q3[:100]}...")
print(f"   Response: {data.get('insight', '')[:80]}...")

print("\n" + "="*60)
print("Test completed!")
