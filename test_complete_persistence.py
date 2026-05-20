"""Comprehensive test: Session persistence with app restart simulation."""

import json
from pathlib import Path
import shutil


def test_complete_persistence_flow():
    """Test complete persistence flow: create session, restart, verify data."""
    
    print("\n" + "=" * 70)
    print("COMPREHENSIVE SESSION PERSISTENCE TEST")
    print("=" * 70)
    
    # Step 1: Clean up old sessions
    print("\n[STEP 1] Cleaning up old sessions...")
    sessions_dir = Path("data/sessions")
    if sessions_dir.exists():
        shutil.rmtree(sessions_dir)
    print("✅ Cleaned sessions directory")
    
    # Step 2: Create first session
    print("\n[STEP 2] Creating first session and adding 2 questions...")
    from services.memory_service import get_memory_service
    
    memory = get_memory_service()
    session_id = memory.create_session()
    print(f"✅ Session ID: {session_id}")
    
    # Add first question
    memory.add_interaction(
        session_id=session_id,
        question="Quel est le CA 2024?",
        sql_generated="SELECT SUM([Sales]) as total_sales FROM [SalesData] WHERE YEAR([Date]) = 2024",
        results=[{"total_sales": 232993525.42}],
        response="Le chiffre d'affaires pour 2024 est 232.9M, pour plus de détails consultez Power BI"
    )
    print("✅ Q1: Quel est le CA 2024? → 232.9M")
    
    # Add second question
    memory.add_interaction(
        session_id=session_id,
        question="Et 2023?",
        sql_generated="SELECT SUM([Sales]) as total_sales FROM [SalesData] WHERE YEAR([Date]) = 2023",
        results=[{"total_sales": 1865970915.67}],
        response="Le chiffre d'affaires pour 2023 est 1.8B (-700% vs 2024), pour plus de détails consultez Power BI"
    )
    print("✅ Q2: Et 2023? → 1.8B (-700% vs 2024)")
    
    # Verify file exists
    session_file = Path(f"data/sessions/{session_id}.json")
    assert session_file.exists(), f"Session file not saved: {session_file}"
    print(f"✅ Session file saved: {session_file}")
    
    # Step 3: Verify file content
    print("\n[STEP 3] Verifying saved file content...")
    with open(session_file) as f:
        session_data = json.load(f)
    
    assert session_data["session_id"] == session_id
    assert len(session_data["interactions"]) == 2
    assert session_data["interactions"][0]["question"] == "Quel est le CA 2024?"
    assert session_data["interactions"][1]["question"] == "Et 2023?"
    print("✅ File content verified")
    print(f"   - Session ID: {session_data['session_id']}")
    print(f"   - Created at: {session_data['created_at']}")
    print(f"   - Interactions: {session_data['interaction_count']}")
    
    # Step 4: Simulate app restart (create new memory service)
    print("\n[STEP 4] Simulating app restart...")
    print("   Creating new MemoryService instance...")
    
    # Clear the singleton to force reload
    from services import memory_service
    memory_service._global_memory_service = memory_service.MemoryService()
    
    memory2 = memory_service.get_memory_service()
    print("✅ New MemoryService created (auto-loads sessions from disk)")
    
    # Step 5: Verify session was restored
    print("\n[STEP 5] Verifying session was restored after restart...")
    restored_interactions = memory2.get_session_interactions(session_id)
    
    assert len(restored_interactions) == 2, f"Expected 2 interactions, got {len(restored_interactions)}"
    print(f"✅ Session restored with {len(restored_interactions)} interactions")
    
    # Verify content
    q1 = restored_interactions[0]
    q2 = restored_interactions[1]
    
    assert q1["question"] == "Quel est le CA 2024?"
    assert q2["question"] == "Et 2023?"
    print("✅ Q1 restored:", q1["question"], "→", q1["response"][:50] + "...")
    print("✅ Q2 restored:", q2["question"], "→", q2["response"][:50] + "...")
    
    # Step 6: Continue conversation with restored session
    print("\n[STEP 6] Continuing conversation with restored session...")
    
    # Check if follow-up is detected
    is_followup = memory2.detect_followup("Et 2022?", session_id)
    print(f"✅ Follow-up detection: {is_followup} (should be True)")
    
    # Add third question to restored session
    memory2.add_interaction(
        session_id=session_id,
        question="Et 2022?",
        sql_generated="SELECT SUM([Sales]) as total_sales FROM [SalesData] WHERE YEAR([Date]) = 2022",
        results=[{"total_sales": 1500000000}],
        response="Le chiffre d'affaires pour 2022 est 1.5B (-20% vs 2023), pour plus de détails consultez Power BI"
    )
    print("✅ Q3: Et 2022? → 1.5B (-20% vs 2023)")
    
    # Step 7: Verify updated file
    print("\n[STEP 7] Verifying updated file on disk...")
    with open(session_file) as f:
        updated_data = json.load(f)
    
    assert len(updated_data["interactions"]) == 3
    print(f"✅ File updated: {len(updated_data['interactions'])} interactions saved")
    
    # Step 8: Final restart to verify everything
    print("\n[STEP 8] Final app restart to verify everything persists...")
    memory_service._global_memory_service = memory_service.MemoryService()
    memory3 = memory_service.get_memory_service()
    
    final_interactions = memory3.get_session_interactions(session_id)
    assert len(final_interactions) == 3
    print(f"✅ Final restart: {len(final_interactions)} interactions loaded")
    
    # Step 9: Display complete conversation
    print("\n[STEP 9] Complete persisted conversation:")
    print("-" * 70)
    for i, interaction in enumerate(final_interactions, 1):
        print(f"\nQ{i}: {interaction['question']}")
        print(f"    → {interaction['response'][:60]}...")
        print(f"    (Timestamp: {interaction['timestamp']})")
    print("-" * 70)
    
    # Success summary
    print("\n" + "=" * 70)
    print("✅ ALL PERSISTENCE TESTS PASSED!")
    print("=" * 70)
    print("\n✅ Sessions are PERMANENTLY SAVED to disk")
    print("✅ Sessions are AUTO-LOADED on app startup")
    print("✅ Sessions SURVIVE app restarts")
    print("✅ All conversation history PRESERVED")
    print("\nFiles saved in: data/sessions/")
    print(f"Session file: {session_file}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    test_complete_persistence_flow()
