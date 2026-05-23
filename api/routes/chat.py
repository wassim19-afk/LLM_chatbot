# api/routes/chat.py
# This module defines the chat route for the FastAPI application.
# It handles the POST /chat endpoint, orchestrating the process from question to response with caching.

import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from api.schemas.chat_schema import (
    ChatRequest,
    ChatResponse,
    SessionRequest,
    SessionResponse,
    SessionRenameRequest,
    SessionInfo,
    SessionsResponse,
    SessionDetailResponse,
    AnalyticsResponse,
)
from services.sql_generator import generate_sql
from services.fallback_sql_generator import generate_fallback_sql
from services.fallback_sql_templates import generate_fallback_sql as generate_fallback_sql_templates
from services.insights_service import generate_simple_response
from services.memory_service import get_memory_service
from services.rag_service import get_rag_service
from services.analytics_service import get_analytics_service
from data.db_connection import execute_query, get_database_schema
from services.cache_service import get_cache_service
from services.response_guard import has_template_for_question, sql_matches_intent
from services.bi_assistant import get_bi_assistant
from services.llm_service import inject_conversation_context, reformulate_question_with_context, rewrite_question_for_clarity
from config.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)
router = APIRouter()

# Initialize services
cache_service = get_cache_service(
    ttl_seconds=settings.CACHE_TTL_SECONDS,
    max_size=settings.CACHE_MAX_SIZE
)
memory_service = get_memory_service()
rag_service = get_rag_service()
analytics_service = get_analytics_service()
bi_assistant = get_bi_assistant()


@router.post("/session", response_model=SessionResponse)
async def create_session(request: Optional[SessionRequest] = None):
    """Create a new conversation session."""
    user_id = (request.user_id or "") if request else ""
    session_id = memory_service.create_session(user_id=user_id)
    return SessionResponse(session_id=session_id)


@router.get("/sessions", response_model=SessionsResponse)
async def list_sessions(user_id: str = ""):
    """Return all saved sessions with metadata, optionally filtered by user_id."""
    sessions = memory_service.list_sessions(user_id=user_id)
    return SessionsResponse(sessions=sessions, count=len(sessions))


@router.post("/sessions/{session_id}/rename", response_model=SessionInfo)
async def rename_session(session_id: str, request: SessionRenameRequest):
    """Rename a saved session."""
    if not request.new_name or not request.new_name.strip():
        raise HTTPException(status_code=400, detail="Session name cannot be empty")

    success = memory_service.rename_session(session_id, request.new_name)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionInfo(
        session_id=session_id,
        session_name=memory_service.get_session_name(session_id),
        interaction_count=len(memory_service.get_session_interactions(session_id)),
        created_at=None,
        updated_at=None,
        last_timestamp=None,
        last_question=None,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint to handle user chat requests for BI queries.
    Processes the question: checks cache, generates SQL, executes it, generates insights, and returns the response.
    """
    start_time = time.time()
    success = False

    try:
        model_name = settings.OLLAMA_MODEL
        user_id = request.user_id or ""
        session_id = request.session_id or memory_service.create_session(user_id=user_id)
        cache_key = f"simple-v1::{model_name}::{request.question.strip()}"

        # Retrieve conversation history early (needed for cache hit insights too)
        conversation_history = memory_service.get_session_interactions(session_id)

        # Step 0: Check cache first
        cached_response = cache_service.get(cache_key)
        if cached_response:
            cached_response.insight = generate_simple_response(cached_response.data, question=request.question, conversation_history=conversation_history)
            cached_response.deterministic_insight = None
            logger.warning(f"Cache HIT for model={model_name}, question: {request.question[:50]}...")
            elapsed = time.time() - start_time
            analytics_service.record_query(
                question=request.question,
                response_time=elapsed,
                success=True,
                cache_hit=True,
                model=model_name,
            )
            return cached_response

        logger.warning(f"Cache MISS - Processing model={model_name}, question: {request.question[:50]}...")

        # Step 0.5: Retrieve RAG context for all questions to improve SQL generation
        rag_context = ""
        try:
            rag_context = rag_service.retrieve_context(request.question, top_k=3)
            if rag_context:
                logger.info("RAG context retrieved for question")
        except Exception as _rag_err:
            logger.warning(f"RAG retrieval skipped: {_rag_err}")

        # Step 0.6: Retrieve conversation context
        is_followup = memory_service.detect_followup(request.question, session_id)
        conv_context = ""
        reformulated_question = request.question  # Default: use original question
        
        if is_followup and conversation_history:
            # Try to reformulate ambiguous short questions using previous context
            last_question = conversation_history[-1].get("question", "")
            if last_question and len(request.question.split()) <= 3:  # Very short question
                reformulated_question = reformulate_question_with_context(request.question, last_question)
                logger.warning(f"Reformulated '{request.question}' → '{reformulated_question}'")
            
            conv_context = inject_conversation_context(
                reformulated_question,  # Use reformulated question
                conversation_history
            )
        
        # Step 0.7: Normalize question for clarity (improves SQL generation)
        normalized_question = rewrite_question_for_clarity(reformulated_question)
        if normalized_question != reformulated_question:
            logger.warning(f"Normalized question: '{reformulated_question}' → '{normalized_question}'")
            reformulated_question = normalized_question

        # Step 0.8: Check if this is a BI (Business Intelligence) question
        if bi_assistant.is_bi_question(request.question):
            logger.warning(f"Detected BI question: {request.question[:50]}...")
            try:
                bi_response, bi_link = bi_assistant.process_bi_question(request.question)
            except ValueError as bi_err:
                raise HTTPException(status_code=422, detail=str(bi_err))
            
            # Create BI-specific response
            response = ChatResponse(
                sql_query=None,  # BI queries don't generate SQL
                data={"type": "bi_result", "kpi_result": bi_response, "dashboard_link": bi_link},
                insight=f"{bi_response}\nDashboard: {bi_link}",
                deterministic_insight=bi_response,
                rag_context=None,
                session_id=session_id,
            )
            
            # Cache the BI response
            cache_service.set(cache_key, response)
            
            # Add to memory
            memory_service.add_interaction(
                session_id, 
                request.question, 
                "BI_QUERY", 
                {"kpi": bi_response, "link": bi_link}, 
                bi_response
            )
            
            elapsed = time.time() - start_time
            logger.warning(f"BI query completed in {elapsed:.2f}s")
            
            # Record analytics
            analytics_service.record_query(
                question=request.question,
                response_time=elapsed,
                success=True,
                cache_hit=False,
                model="BI_ASSISTANT",
            )
            
            return response

        # Deterministic first-pass for recognized BI intents
        template_sql = generate_fallback_sql_templates(request.question)

        # Step 1: Generate SQL from question
        if template_sql:
            sql_query = template_sql
            logger.warning("Using deterministic template SQL for recognized intent.")
        else:
            try:
                # Enrich prompt with context - use reformulated question
                enriched_prompt = reformulated_question
                if conv_context:
                    enriched_prompt = f"{conv_context}\n\nFollow-up: {reformulated_question}"
                if rag_context:
                    enriched_prompt = f"{rag_context}\n\nQuestion: {enriched_prompt}"

                sql_query = generate_sql(enriched_prompt, model=model_name)
            except Exception as e:
                logger.warning(f"LLM-based SQL generation failed ({type(e).__name__}), trying fallback templates")

                sql_query = generate_fallback_sql_templates(request.question)

                if not sql_query:
                    logger.warning(f"Template-based fallback also failed, trying generic fallback")
                    sql_query = generate_fallback_sql(request.question)

                if not sql_query:
                    # No SQL possible - use RAG to provide a helpful response
                    logger.warning("No SQL template matched, using RAG fallback response")
                    rag_answer = rag_service.answer_question(request.question, conversation_history)
                    response = ChatResponse(
                        sql_query=None,
                        data={"type": "rag_response", "answer": rag_answer},
                        insight=rag_answer,
                        deterministic_insight=None,
                        rag_context=rag_answer if rag_answer else None,
                        session_id=session_id,
                    )
                    cache_service.set(cache_key, response)
                    memory_service.add_interaction(session_id, request.question, "", [{"response": rag_answer}], rag_answer, user_id=user_id)
                    elapsed = time.time() - start_time
                    analytics_service.record_query(
                        question=request.question,
                        response_time=elapsed,
                        success=True,
                        cache_hit=False,
                        model="RAG_FALLBACK",
                    )
                    return response

                logger.warning("Using fallback SQL generation")

        # Step 1.1: Relevance guard — skip if we already have a deterministic template SQL
        if sql_query == template_sql and template_sql:
            matches_intent = True
            intent_error = ""
        else:
            matches_intent, intent_error = sql_matches_intent(sql_query, request.question)
            if not matches_intent:
                logger.warning(intent_error)
                if template_sql:
                    sql_query = template_sql
                    matches_intent = True
                    intent_error = ""

        if has_template_for_question(request.question) and not matches_intent:
            # Guard rejected SQL but we detected an intent - use RAG for helpful response
            logger.warning(f"Intent guard failed: {intent_error}, switching to RAG")
            rag_answer = rag_service.answer_question(request.question, conversation_history)
            response = ChatResponse(
                sql_query=None,
                data={"type": "rag_response", "answer": rag_answer},
                insight=rag_answer,
                deterministic_insight=None,
                rag_context=rag_answer if rag_answer else None,
                session_id=session_id,
            )
            cache_service.set(cache_key, response)
            memory_service.add_interaction(session_id, request.question, "", [{"response": rag_answer}], rag_answer, user_id=user_id)
            elapsed = time.time() - start_time
            analytics_service.record_query(
                question=request.question,
                response_time=elapsed,
                success=True,
                cache_hit=False,
                model="RAG_FALLBACK",
            )
            return response

        logger.warning(f"Generated SQL: {sql_query[:100]}...")

        # Step 2: Execute SQL query safely (includes validation)
        data = execute_query(sql_query)
        success = True

        # Step 3: Generate concise one-sentence business response with conversation context
        insight = generate_simple_response(data, question=request.question, conversation_history=conversation_history)

        # Step 4: Create response
        response = ChatResponse(
            sql_query=sql_query,
            data=data,
            insight=insight,
            deterministic_insight=None,
            rag_context=rag_context if rag_context else None,
            session_id=session_id,
        )

        # Step 5: Cache the response
        cache_service.set(cache_key, response)

        # Step 5.5: Add to memory
        memory_service.add_interaction(session_id, request.question, sql_query, data, insight, user_id=user_id)

        elapsed = time.time() - start_time
        logger.warning(f"Chat request completed in {elapsed:.2f}s")

        # Step 6: Record analytics
        analytics_service.record_query(
            question=request.question,
            response_time=elapsed,
            success=True,
            cache_hit=False,
            model=model_name,
        )

        # Step 7: Return response
        return response

    except ValueError as e:
        logger.warning("SQL generation error: %s", str(e), exc_info=True)
        elapsed = time.time() - start_time
        analytics_service.record_query(
            question=request.question,
            response_time=elapsed,
            success=False,
        )
        raise HTTPException(status_code=400, detail=f"SQL generation error: {str(e)}")
    except Exception as e:
        logger.warning("Unhandled server error: %s", str(e), exc_info=True)
        elapsed = time.time() - start_time
        analytics_service.record_query(
            question=request.question,
            response_time=elapsed,
            success=False,
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/history/{session_id}", response_model=SessionDetailResponse)
async def get_session_history(session_id: str):
    """
    GET endpoint to retrieve full session conversation history.
    Returns all Q&A pairs with timestamps and SQL queries.
    """
    try:
        interactions = memory_service.get_session_interactions(session_id)
        if not interactions:
            return SessionDetailResponse(
                session_id=session_id,
                session_name=memory_service.get_session_name(session_id),
                interactions=[],
                count=0,
            )
        
        # Format for frontend display
        formatted_history = []
        for interaction in interactions:
            formatted_history.append({
                "timestamp": interaction.get("timestamp"),
                "question": interaction.get("question"),
                "response": interaction.get("response"),
                "sql": interaction.get("sql_generated"),
                "row_count": interaction.get("row_count"),
            })
        
        logger.warning(f"Retrieved {len(formatted_history)} interactions for session {session_id}")
        return SessionDetailResponse(
            session_id=session_id,
            session_name=memory_service.get_session_name(session_id),
            interactions=formatted_history,
            count=len(formatted_history),
        )
    except Exception as e:
        logger.warning(f"Error retrieving session history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@router.get("/schema", response_model=List[str])
async def schema():
    """
    Returns the available database table and column schema metadata.
    """
    try:
        return get_database_schema()
    except Exception as e:
        logger.warning("Schema metadata error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unable to load schema metadata: {str(e)}")


@router.get("/analytics", response_model=AnalyticsResponse)
async def analytics():
    """
    Returns system analytics and performance metrics.
    """
    try:
        stats = analytics_service.get_analytics()
        return AnalyticsResponse(**stats)
    except Exception as e:
        logger.warning("Analytics error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analytics unavailable: {str(e)}")


@router.post("/bi/query")
async def bi_query(request: ChatRequest):
    """
    Dedicated Business Intelligence endpoint for KPI and Power BI dashboard queries.
    
    Handles queries like:
    - "ca 2024" → Chiffre d'affaires for 2024
    - "ca janvier 2025 SAPEC" → January 2025 revenue for SAPEC
    - "encaissement février 2023 PEM" → Cash in for February 2023, PEM
    
    Returns:
    {
        "kpi_result": "Chiffre d'affaires: 1,200,000 BnFCFA",
        "dashboard_link": "https://app.powerbi.com/...?filter=...",
        "parsed_filters": {
            "kpi_type": "Chiffre d'affaires",
            "year": 2024,
            "month": 1,
            "company": "SAPEC"
        }
    }
    """
    start_time = time.time()
    
    try:
        session_id = request.session_id or memory_service.create_session()
        
        # Parse the BI question
        parsed = bi_assistant.parse_query(request.question)
        
        # Generate response
        kpi_result, dashboard_link = bi_assistant.process_bi_question(request.question)
        
        # Prepare response
        response_data = {
            "kpi_result": kpi_result,
            "dashboard_link": dashboard_link,
            "parsed_filters": {
                "kpi_type": parsed['kpi_type'].value,
                "year": parsed['year'],
                "month": parsed['month'],
                "company": parsed['company'],
                "filter_expression": parsed['filters']
            },
            "session_id": session_id,
        }
        
        # Add to memory
        memory_service.add_interaction(
            session_id,
            request.question,
            "BI_QUERY",
            response_data,
            kpi_result
        )
        
        elapsed = time.time() - start_time
        logger.warning(f"BI query completed in {elapsed:.2f}s")
        
        # Record analytics
        analytics_service.record_query(
            question=request.question,
            response_time=elapsed,
            success=True,
            cache_hit=False,
            model="BI_ASSISTANT",
        )
        
        return response_data
        
    except Exception as e:
        logger.warning(f"BI query error: {str(e)}", exc_info=True)
        elapsed = time.time() - start_time
        analytics_service.record_query(
            question=request.question,
            response_time=elapsed,
            success=False,
        )
        raise HTTPException(status_code=500, detail=f"BI query error: {str(e)}")


@router.get("/bi/is-bi-question")
async def check_bi_question(question: str):
    """
    Check if a question is recognized as a BI query.
    
    Query params:
    - question: The question to analyze
    
    Returns:
    {
        "is_bi_question": true/false,
        "parsed_details": {...}
    }
    """
    try:
        is_bi = bi_assistant.is_bi_question(question)
        parsed = bi_assistant.parse_query(question) if is_bi else None
        
        return {
            "is_bi_question": is_bi,
            "question": question,
            "parsed_details": {
                "kpi_type": parsed['kpi_type'].value if parsed else None,
                "year": parsed['year'] if parsed else None,
                "month": parsed['month'] if parsed else None,
                "company": parsed['company'] if parsed else None,
            } if parsed else None
        }
    except Exception as e:
        logger.warning(f"BI question check error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking question: {str(e)}")

