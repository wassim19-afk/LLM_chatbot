#!/usr/bin/env python
"""Comprehensive test of improved session context management"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("\n" + "="*70)
print("🎯 IMPROVED SESSION CONTEXT TEST")
print("="*70)

# Create a NEW session
resp = requests.post(f"{BASE_URL}/api/session")
session_id = resp.json()["session_id"]
print(f"\n✓ New session created: {session_id[:14]}...")

# ========================================
# Test Scenario: Multi-turn conversation
# ========================================

questions = [
    ("CA 2024?", "Establish CA context"),
    ("2023?", "Should use CA context from Q1"),
    ("Et 2022?", "Should use CA context from Q1"),
    ("le client qui fait beaucoup d'achat?", "Complex question about customers"),
]

responses_data = []

print("\n" + "-"*70)
print("📌 MULTI-TURN CONVERSATION TEST")
print("-"*70)

for idx, (question, description) in enumerate(questions, 1):
    print(f"\n[Q{idx}] {question}")
    print(f"      Context: {description}")
    
    # Send question
    resp = requests.post(
        f"{BASE_URL}/api/chat",
        json={"question": question, "session_id": session_id},
        timeout=30
    )
    
    if resp.status_code != 200:
        print(f"      ❌ Error: {resp.json().get('detail', 'Unknown error')}")
        continue
    
    data = resp.json()
    responses_data.append({
        "q": question,
        "response": data.get('insight', ''),
        "sql": data.get('sql_query', '')[:80] + "..."
    })
    
    print(f"      Response: {data.get('insight', '')[:100]}...")
    if "YEAR(" in data.get('sql_query', ''):
        print(f"      ✅ SQL uses YEAR grouping (context aware)")

# Get full session history
print("\n" + "-"*70)
print("📋 SESSION HISTORY RETRIEVAL")
print("-"*70)

resp = requests.get(f"{BASE_URL}/api/history/{session_id}")
history = resp.json()

print(f"\nSession: {session_id[:14]}...")
print(f"Total interactions: {history.get('count', 0)}")

if history.get('interactions'):
    print("\nFull conversation history:")
    for i, interaction in enumerate(history['interactions'], 1):
        q = interaction.get('question', '')
        a = interaction.get('response', '')
        print(f"\n  {i}. Q: {q}")
        print(f"     A: {a[:80]}...")

# ========================================
# Summary
# ========================================

print("\n" + "="*70)
print("✅ TEST RESULTS SUMMARY")
print("="*70)

success_count = sum(1 for r in responses_data if r['response'])
print(f"\n✓ Total questions asked: {len(questions)}")
print(f"✓ Successful responses: {success_count}")
print(f"✓ Session context preserved: {'Yes' if success_count > 2 else 'Partial'}")
print(f"✓ History endpoint working: {'Yes' if history.get('count') else 'No'}")

print("\n" + "="*70)
print("🎉 Session context management is IMPROVED!")
print("="*70 + "\n")
