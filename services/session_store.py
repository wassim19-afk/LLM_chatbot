"""Persistent session storage using JSON files."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from config.logger import get_logger

logger = get_logger(__name__)

SESSIONS_DIR = Path(__file__).resolve().parent.parent / "data" / "sessions"


def ensure_sessions_dir():
    """Create sessions directory if it doesn't exist."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _get_session_file(session_id: str) -> Path:
    """Get the file path for a session."""
    return SESSIONS_DIR / f"{session_id}.json"


def _default_session_name(session_id: str, interactions: Optional[List[Dict[str, Any]]] = None) -> str:
    return f"Session {session_id[:8]}"


def load_session_record(session_id: str) -> Dict[str, Any]:
    """Load the full session record from disk."""
    session_file = _get_session_file(session_id)

    if not session_file.exists():
        return {}

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        if not isinstance(session_data, dict):
            return {}

        interactions = session_data.get("interactions", [])
        if not isinstance(interactions, list):
            interactions = []

        session_name = session_data.get("session_name") or _default_session_name(session_id, interactions)

        return {
            "session_id": session_id,
            "session_name": session_name,
            "created_at": session_data.get("created_at"),
            "updated_at": session_data.get("updated_at", session_data.get("created_at")),
            "interactions": interactions,
            "interaction_count": session_data.get("interaction_count", len(interactions)),
        }
    except Exception as e:
        logger.error(f"Failed to load session record {session_id}: {e}")
        return {}


def save_session(session_id: str, interactions: List[Dict[str, Any]], session_name: Optional[str] = None) -> None:
    """Save session interactions to JSON file."""
    ensure_sessions_dir()
    
    session_file = _get_session_file(session_id)
    existing_record = load_session_record(session_id)
    session_data = {
        "session_id": session_id,
        "session_name": session_name or existing_record.get("session_name") or _default_session_name(session_id, interactions),
        "created_at": existing_record.get("created_at") or datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "interactions": interactions,
        "interaction_count": len(interactions),
    }
    
    try:
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2, default=str)
        logger.info(f"Saved session {session_id} to disk ({len(interactions)} interactions)")
    except Exception as e:
        logger.error(f"Failed to save session {session_id}: {e}")


def load_session(session_id: str) -> List[Dict[str, Any]]:
    """Load session interactions from JSON file."""
    session_data = load_session_record(session_id)
    if not session_data:
        return []

    logger.info(
        f"Loaded session {session_id} from disk ({session_data.get('interaction_count', 0)} interactions)"
    )
    return session_data.get("interactions", [])


def list_session_records() -> List[Dict[str, Any]]:
    """List all saved sessions with metadata."""
    ensure_sessions_dir()

    sessions = []
    try:
        for file in SESSIONS_DIR.glob("*.json"):
            record = load_session_record(file.stem)
            if record:
                sessions.append(record)
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")

    sessions.sort(key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
    return sessions


def list_all_sessions() -> List[str]:
    """List all saved session IDs."""
    return [record["session_id"] for record in list_session_records()]


def delete_session(session_id: str) -> bool:
    """Delete a session file."""
    session_file = _get_session_file(session_id)
    
    try:
        if session_file.exists():
            session_file.unlink()
            logger.info(f"Deleted session {session_id}")
            return True
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
    
    return False


def rename_session(session_id: str, session_name: str) -> bool:
    """Rename a session while preserving its interactions."""
    session_data = load_session_record(session_id)
    if not session_data:
        return False

    try:
        save_session(session_id, session_data.get("interactions", []), session_name=session_name)
        logger.info(f"Renamed session {session_id} to '{session_name}'")
        return True
    except Exception as e:
        logger.error(f"Failed to rename session {session_id}: {e}")
        return False


def session_exists(session_id: str) -> bool:
    """Check if a session file exists."""
    return _get_session_file(session_id).exists()
