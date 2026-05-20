# api/schemas/chat.py
# This module defines Pydantic models for the chat API endpoints.
# It ensures data validation for incoming requests and outgoing responses.

from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

class ChatRequest(BaseModel):
    """
    Model for the incoming chat request.
    Contains the user's natural language question and optional session tracking.
    """
    question: str
    model: str = "mistral"
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """
    Model for the chat response.
    Includes the generated SQL, query results, insights, and session context.
    Supports both SQL responses (with sql_query and data list) and BI responses (with BI data dict).
    """
    sql_query: Optional[str] = None
    data: Union[List[Dict[str, Any]], Dict[str, Any]]
    insight: str
    deterministic_insight: Optional[str] = None
    rag_context: Optional[str] = None
    session_id: Optional[str] = None

class SessionRequest(BaseModel):
    """Request to create a new session."""
    pass

class SessionResponse(BaseModel):
    """Response with session ID."""
    session_id: str


class SessionRenameRequest(BaseModel):
    """Request to rename an existing session."""
    new_name: str


class SessionInfo(BaseModel):
    """Session metadata for session lists and sidebar navigation."""
    session_id: str
    session_name: str
    interaction_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_timestamp: Optional[str] = None
    last_question: Optional[str] = None


class SessionsResponse(BaseModel):
    """List of sessions."""
    sessions: List[SessionInfo]
    count: int


class SessionDetailResponse(BaseModel):
    """Session metadata plus history."""
    session_id: str
    session_name: str
    interactions: List[Dict[str, Any]]
    count: int

class AnalyticsResponse(BaseModel):
    """Analytics snapshot."""
    total_queries: int
    average_response_time_seconds: float
    cache_hit_rate_percent: float
    error_rate_percent: float
    timestamp: str