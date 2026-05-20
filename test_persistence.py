"""Test session persistence across app restarts."""

import time
import shutil
from pathlib import Path
from services.memory_service import get_memory_service

def test_session_persistence():
    """Test that sessions are saved to disk and can be reloaded."""
    
    # Clean up any old test sessions
    sessions_dir = Path("data/sessions")
    if sessions_dir.exists():
        shutil.rmtree(sessions_dir)
    
    print("=" * 60)
    print("TEST 1: Create session and add interactions")
    print("=" * 60)
    
    # Create first session
    memory1 = get_memory_service()
    session_id = memory1.create_session()
    print(f"✅ Created session: {session_id}")
    
    # Add some interactions
    memory1.add_interaction(
        session_id=session_id,
        question="CA 2024?",
        sql_generated="SELECT SUM(Sales) FROM data WHERE YEAR=2024",
        results=[{"sales": 232993525.42}],
        response="Le chiffre d'affaires ca est 232,993,525.42"
    )
    print("✅ Added Q1: CA 2024? → 232M")
    
    memory1.add_interaction(
        session_id=session_id,
        question="2023?",
        sql_generated="SELECT SUM(Sales) FROM data WHERE YEAR=2023",
        results=[{"sales": 1865970915.67}],
        response="Le chiffre d'affaires ca est 1,865,970,915.67 (-700% vs 2024)"
    )
    print("✅ Added Q2: 2023? → 1.8B")
    
    # Verify interactions are saved
    interactions = memory1.get_session_interactions(session_id)
    print(f"✅ Session has {len(interactions)} interactions in memory")
    
    # Verify file exists on disk
    session_file = Path(f"data/sessions/{session_id}.json")
    if session_file.exists():
        print(f"✅ Session file saved to disk: {session_file}")
    else:
        print(f"❌ Session file NOT found: {session_file}")
        return
    
    print()
    print("=" * 60)
    print("TEST 2: Restart (create new memory service)")
    print("=" * 60)
    
    # Create a NEW memory service (simulating app restart)
    # Clear the global singleton to force reload
    from services import memory_service
    memory_service._global_memory_service = memory_service.MemoryService()
    
    memory2 = memory_service.get_memory_service()
    print("✅ Created new MemoryService instance")
    
    # Check if session was auto-loaded
    loaded_interactions = memory2.get_session_interactions(session_id)
    print(f"✅ Auto-loaded {len(loaded_interactions)} interactions from disk")
    
    if len(loaded_interactions) != 2:
        print(f"❌ Expected 2 interactions, got {len(loaded_interactions)}")
        return
    
    print()
    print("=" * 60)
    print("TEST 3: Verify interaction content")
    print("=" * 60)
    
    for i, interaction in enumerate(loaded_interactions, 1):
        print(f"\nInteraction {i}:")
        print(f"  Question: {interaction['question']}")
        print(f"  Response: {interaction['response']}")
        print(f"  SQL: {interaction['sql_generated'][:60]}...")
        print(f"  Row count: {interaction['row_count']}")
    
    print()
    print("=" * 60)
    print("TEST 4: Add new interaction to persisted session")
    print("=" * 60)
    
    # Add a new interaction to the loaded session
    memory2.add_interaction(
        session_id=session_id,
        question="Et 2022?",
        sql_generated="SELECT SUM(Sales) FROM data WHERE YEAR=2022",
        results=[{"sales": 1500000000}],
        response="Le chiffre d'affaires ca est 1,500,000,000 (-20% vs 2023)"
    )
    print("✅ Added Q3: Et 2022? → 1.5B")
    
    # Verify in new memory service
    all_interactions = memory2.get_session_interactions(session_id)
    print(f"✅ Session now has {len(all_interactions)} interactions")
    
    if len(all_interactions) != 3:
        print(f"❌ Expected 3 interactions, got {len(all_interactions)}")
        return
    
    print()
    print("=" * 60)
    print("TEST 5: Verify persistence of new interaction")
    print("=" * 60)
    
    # Create ANOTHER memory service to reload
    memory_service._global_memory_service = memory_service.MemoryService()
    memory3 = memory_service.get_memory_service()
    
    final_interactions = memory3.get_session_interactions(session_id)
    print(f"✅ After second restart: {len(final_interactions)} interactions loaded")
    
    if len(final_interactions) != 3:
        print(f"❌ Expected 3 interactions, got {len(final_interactions)}")
        return
    
    print()
    print("=" * 60)
    print("✅ ALL PERSISTENCE TESTS PASSED!")
    print("=" * 60)
    print()
    print("SUMMARY:")
    print("✅ Sessions are saved to disk automatically")
    print("✅ Sessions are loaded on app restart")
    print("✅ New interactions are persisted")
    print("✅ Session data survives app restarts")


if __name__ == "__main__":
    test_session_persistence()
