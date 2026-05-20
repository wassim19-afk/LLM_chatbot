# services/async_wrappers.py
# Async wrapper functions for I/O operations (Ollama calls, database queries).
# Allows FastAPI endpoints to use async/await without blocking.

import asyncio
from typing import Optional, Any
from concurrent.futures import ThreadPoolExecutor
import httpx

# Thread pool for running sync operations asynchronously
executor = ThreadPoolExecutor(max_workers=5)

async def call_ollama_async(prompt: str, model: str = "mistral", timeout: int = 30) -> Optional[str]:
    """
    Async wrapper for Ollama LLM calls.
    Uses httpx.AsyncClient for non-blocking HTTP requests.
    
    Args:
        prompt (str): Prompt to send to Ollama
        model (str): Model name (default: mistral)
        timeout (int): Request timeout in seconds
    
    Returns:
        Optional[str]: Model response or None on timeout/error
    """
    from config.settings import settings
    
    payload = {
        "model": model or settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "temperature": 0.3,  # Lower temperature for consistent SQL generation
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(settings.OLLAMA_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
    except asyncio.TimeoutError:
        return None
    except httpx.HTTPError:
        return None
    except Exception:
        return None


async def execute_query_async(sql_query: str, params: tuple = None) -> list:
    """
    Async wrapper for database query execution.
    Runs synchronous pyodbc call in thread pool to avoid blocking.
    
    Args:
        sql_query (str): SQL query to execute
        params (tuple, optional): Query parameters
    
    Returns:
        list: Query results as list of dicts
    """
    from data.db_connection import execute_query
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, execute_query, sql_query, params)


async def get_database_schema_async() -> list:
    """
    Async wrapper for fetching database schema.
    
    Returns:
        list: Database schema information
    """
    from data.db_connection import get_database_schema
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, get_database_schema)
