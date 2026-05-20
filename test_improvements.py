#!/usr/bin/env python
"""Test script for improved system"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("\n🧪 Testing Improved System\n" + "="*50)

# Create a session
resp = requests.post(f"{BASE_URL}/api/session")
session_data = resp.json()
session_id = session_data["session_id"]
print(f"\n✓ Session created: {session_id[:12]}...")

# Test 1: Simple question
q1 = "CA 2024?"
print(f"\n📌 Test 1: Simple question")
print(f"   Question: {q1}")
resp = requests.post(f"{BASE_URL}/api/chat", json={"question": q1, "session_id": session_id})
data = resp.json()
if "detail" in data:
    print(f"   ❌ Error: {data.get('detail')}")
else:
    print(f"   ✓ Response: {data.get('insight', '')[:100]}...")

# Test 2: Complex question
q2 = "le client qui fait beaucoup d'achat?"
print(f"\n📌 Test 2: Complex question")
print(f"   Question: {q2}")
resp = requests.post(f"{BASE_URL}/api/chat", json={"question": q2, "session_id": session_id})
data = resp.json()
if "detail" in data:
    print(f"   ❌ Error: {data.get('detail')}")
else:
    print(f"   ✓ Response: {data.get('insight', '')[:100]}...")

# Test 3: Follow-up question
q3 = "2023?"
print(f"\n📌 Test 3: Follow-up question")
print(f"   Question: {q3}")
resp = requests.post(f"{BASE_URL}/api/chat", json={"question": q3, "session_id": session_id})
data = resp.json()
if "detail" in data:
    print(f"   ❌ Error: {data.get('detail')}")
else:
    print(f"   ✓ Response: {data.get('insight', '')[:100]}...")

print("\n" + "="*50)
print("✅ All tests completed!")
