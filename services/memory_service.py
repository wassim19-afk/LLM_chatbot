"""Conversational memory service for session-based context tracking."""

import uuid
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

from config.logger import get_logger
from services.session_store import (
    save_session,
    load_session,
    list_all_sessions,
    session_exists,
    list_session_records,
    load_session_record,
    rename_session as rename_session_file,
)

logger = get_logger(__name__)


@dataclass
class Interaction:
    """Single user interaction entry."""
    timestamp: str
    question: str
    sql_generated: str
    result_summary: str
    row_count: int
    response: str = ""


class MemoryService:
    """Manages conversational memory per session with disk persistence."""

    def __init__(self, max_interactions: int = 10) -> None:
        self.sessions: Dict[str, List[Interaction]] = {}
        self.session_names: Dict[str, str] = {}
        self.session_users: Dict[str, str] = {}
        self.max_interactions = max_interactions
        self._load_all_sessions_from_disk()

    def _load_all_sessions_from_disk(self) -> None:
        """Load all existing sessions from disk on startup."""
        try:
            session_records = list_session_records()
            for session_record in session_records:
                session_id = session_record.get("session_id")
                if not session_id:
                    continue
                interactions_data = load_session(session_id)
                # Convert dicts back to Interaction objects
                interactions = [
                    Interaction(
                        timestamp=item.get("timestamp", ""),
                        question=item.get("question", ""),
                        sql_generated=item.get("sql_generated", ""),
                        result_summary=item.get("result_summary", ""),
                        row_count=item.get("row_count", 0),
                        response=item.get("response", ""),
                    )
                    for item in interactions_data
                ]
                self.sessions[session_id] = interactions
                self.session_names[session_id] = session_record.get("session_name", f"Session {session_id[:8]}")
                self.session_users[session_id] = session_record.get("user_id", "")
            if session_records:
                logger.info(f"Loaded {len(session_records)} sessions from disk")
        except Exception as e:
            logger.error(f"Failed to load sessions from disk: {e}")

    def create_session(self, user_id: str = "") -> str:
        """Generate new session ID and initialize memory."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = []
        self.session_names[session_id] = f"Session {session_id[:8]}"
        self.session_users[session_id] = user_id
        save_session(session_id, [], session_name=self.session_names[session_id], user_id=user_id)
        logger.info(f"Created session: {session_id} for user: {user_id or 'anonymous'}")
        return session_id

    def load_session_from_disk(self, session_id: str) -> bool:
        """Load a specific session from disk if not already in memory."""
        if session_id in self.sessions:
            return True  # Already loaded
        
        if not session_exists(session_id):
            return False  # Session doesn't exist
        
        session_record = load_session_record(session_id)
        interactions_data = load_session(session_id)
        interactions = [
            Interaction(
                timestamp=item.get("timestamp", ""),
                question=item.get("question", ""),
                sql_generated=item.get("sql_generated", ""),
                result_summary=item.get("result_summary", ""),
                row_count=item.get("row_count", 0),
                response=item.get("response", ""),
            )
            for item in interactions_data
        ]
        self.sessions[session_id] = interactions
        if session_record:
            self.session_names[session_id] = session_record.get("session_name", f"Session {session_id[:8]}")
            self.session_users[session_id] = session_record.get("user_id", "")
        logger.info(f"Loaded session {session_id} from disk ({len(interactions)} interactions)")
        return True

    def add_interaction(
        self,
        session_id: str,
        question: str,
        sql_generated: str,
        results: List[Dict[str, Any]],
        response: str = "",
        user_id: str = "",
    ) -> None:
        """Add interaction to session memory and save to disk."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        results_list = results if isinstance(results, list) else []
        result_summary = self._summarize_results(results_list)
        row_count = len(results_list)

        interaction = Interaction(
            timestamp=datetime.now().isoformat(),
            question=question,
            sql_generated=sql_generated,
            result_summary=result_summary,
            row_count=row_count,
            response=response,
        )

        self.sessions[session_id].append(interaction)

        if len(self.sessions[session_id]) > self.max_interactions:
            self.sessions[session_id].pop(0)

        # Auto-name session from first question
        is_first = len(self.sessions[session_id]) == 1
        if is_first:
            auto_name = question.strip()[:60]
            self.session_names[session_id] = auto_name
        if user_id:
            self.session_users[session_id] = user_id

        interactions_dict = [asdict(i) for i in self.sessions[session_id]]
        uid = user_id or self.session_users.get(session_id, "")
        save_session(session_id, interactions_dict, session_name=self.get_session_name(session_id), user_id=uid)

        logger.info(f"Added interaction to session {session_id}")

    def get_session_name(self, session_id: str) -> str:
        """Get a friendly name for a session."""
        if session_id in self.session_names and self.session_names[session_id]:
            return self.session_names[session_id]

        if session_exists(session_id):
            session_record = load_session_record(session_id)
            if session_record:
                session_name = session_record.get("session_name") or f"Session {session_id[:8]}"
                self.session_names[session_id] = session_name
                return session_name

        return f"Session {session_id[:8]}"

    def list_sessions(self, user_id: str = "") -> List[Dict[str, Any]]:
        """Return metadata for all saved sessions, filtered by user_id if provided."""
        records = list_session_records()
        sessions = []
        for record in records:
            session_id = record.get("session_id")
            if not session_id:
                continue
            if user_id and record.get("user_id", "") != user_id:
                continue
            sessions.append({
                "session_id": session_id,
                "session_name": record.get("session_name") or self.get_session_name(session_id),
                "interaction_count": record.get("interaction_count", 0),
                "created_at": record.get("created_at"),
                "updated_at": record.get("updated_at"),
                "last_timestamp": record.get("updated_at") or record.get("created_at"),
                "last_question": record.get("interactions", [{}])[-1].get("question") if record.get("interactions") else None,
                "user_id": record.get("user_id", ""),
            })
        return sessions

    def rename_session(self, session_id: str, session_name: str) -> bool:
        """Rename a session and persist the new display name."""
        if not session_name or not session_name.strip():
            return False

        cleaned_name = session_name.strip()
        if not session_exists(session_id):
            return False

        success = rename_session_file(session_id, cleaned_name)
        if success:
            self.session_names[session_id] = cleaned_name
        return success

    def get_context(self, session_id: str, max_chars: int = 1200) -> str:
        """Retrieve formatted context for a session."""
        # Try to load from disk if not in memory
        if session_id not in self.sessions:
            self.load_session_from_disk(session_id)
        
        if session_id not in self.sessions or not self.sessions[session_id]:
            return ""

        context_lines = ["Previous context from this session:\n"]
        for i, interaction in enumerate(self.sessions[session_id], 1):
            context_lines.append(
                f"{i}. Q: {interaction.question[:100]}\n"
                f"   SQL: {interaction.sql_generated[:100]}...\n"
                f"   Result: {interaction.result_summary}\n"
            )

        context_text = "".join(context_lines)
        if len(context_text) > max_chars:
            return context_text[-max_chars:]
        return context_text

    def detect_followup(self, question: str, session_id: str) -> bool:
        """
        Heuristic: detect if question is a follow-up.
        AGGRESSIVE approach: If session has history + question is short/ambiguous → follow-up
        
        Returns True if:
        1. Has follow-up keywords ("et", "and", "also", etc.)
        2. Is VERY short (≤5 words) AND session has history
        3. Looks like a year/number query (2024, 2023, etc.)
        4. Contains comparison patterns
        """
        # Try to load from disk if not in memory
        if session_id not in self.sessions:
            self.load_session_from_disk(session_id)
        
        if session_id not in self.sessions or not self.sessions[session_id]:
            return False

        current_lower = question.lower().strip().rstrip('?')

        # Check for follow-up keywords
        followup_keywords = ["et", "and", "also", "additionally", "what about", "compare",
                            "mais", "but", "donc", "then", "alors", "pareil", "similar"]
        has_keyword = any(kw in current_lower for kw in followup_keywords)

        # AGGRESSIVE: Very short questions with history = almost certainly follow-up
        short_followup = len(current_lower.split()) <= 5

        # Check if question looks like a year or number (common follow-up pattern)
        looks_like_year = current_lower.strip('?').isdigit() and (
            len(current_lower.strip('?')) == 4  # Year format: YYYY
            or len(current_lower.split()) == 1  # Single number
        )

        # Check for comparison patterns
        comparison_patterns = ["vs", "versus", "vs.", "compared", "comparé", "between"]
        has_comparison = any(p in current_lower for p in comparison_patterns)

        return has_keyword or short_followup or looks_like_year or has_comparison

    def get_session_interactions(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all interactions for a session as dicts."""
        # Try to load from disk if not in memory
        if session_id not in self.sessions:
            self.load_session_from_disk(session_id)
        
        if session_id not in self.sessions:
            return []
        return [asdict(i) for i in self.sessions[session_id]]

    def get_formatted_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get formatted history for chat display (role + content)."""
        # Try to load from disk if not in memory
        if session_id not in self.sessions:
            self.load_session_from_disk(session_id)
        
        if session_id not in self.sessions:
            return []
        
        messages = []
        for interaction in self.sessions[session_id]:
            messages.append({
                "role": "user",
                "content": interaction.question,
                "timestamp": interaction.timestamp,
            })
            messages.append({
                "role": "assistant",
                "content": interaction.response,
                "timestamp": interaction.timestamp,
                "sql": interaction.sql_generated,
                "summary": interaction.result_summary,
            })
        return messages

    def clear_session(self, session_id: str) -> None:
        """Clear session memory."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
        if session_id in self.session_names:
            del self.session_names[session_id]

    @staticmethod
    def _summarize_results(results: List[Dict[str, Any]], max_chars: int = 200) -> str:
        """Create brief summary of query results."""
        if not results:
            return "No results"

        if len(results) == 1:
            first_row = results[0]
            summary = ", ".join(f"{k}={v}" for k, v in list(first_row.items())[:3])
            return f"1 row: {summary[:max_chars]}"

        return f"{len(results)} rows"


_global_memory_service = MemoryService()


def get_memory_service() -> MemoryService:
    """Get global memory service singleton."""
    return _global_memory_service


def create_session() -> str:
    return _global_memory_service.create_session()


def add_interaction(session_id: str, question: str, sql: str, result: List[Dict[str, Any]], response: str = "") -> None:
    _global_memory_service.add_interaction(session_id, question, sql, result, response)


def get_context(session_id: str) -> str:
    return _global_memory_service.get_context(session_id)
