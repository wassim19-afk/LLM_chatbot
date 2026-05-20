# services/cache_service.py
# Response caching service with LRU eviction and TTL (time-to-live).
# Caches full chat responses to avoid repeated LLM calls for identical questions.

import hashlib
import time
from typing import Optional, Dict, Any
from threading import Lock
from collections import OrderedDict
from api.schemas.chat_schema import ChatResponse

class CacheService:
    """
    Thread-safe in-memory cache with LRU eviction and TTL.
    
    Key: MD5 hash of normalized question (lowercase)
    Value: Tuple of (ChatResponse, timestamp)
    
    Attributes:
        ttl_seconds (int): Time-to-live for cache entries (default: 7 minutes = 420 seconds)
        max_size (int): Maximum number of cached responses (default: 100)
    """
    
    def __init__(self, ttl_seconds: int = 420, max_size: int = 100):
        """
        Initialize the cache service.
        
        Args:
            ttl_seconds (int): Time-to-live in seconds (default: 420 = 7 minutes)
            max_size (int): Maximum cached responses (default: 100)
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.cache: OrderedDict[str, tuple] = OrderedDict()  # {hash: (response, timestamp)}
        self.lock = Lock()
    
    def _hash_question(self, question: str) -> str:
        """
        Create consistent hash of normalized question.
        Normalization: lowercase, strip whitespace.
        """
        normalized = question.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get(self, question: str) -> Optional[ChatResponse]:
        """
        Retrieve cached response if exists and not expired.
        
        Args:
            question (str): User's original question
        
        Returns:
            ChatResponse or None if not in cache or expired
        """
        cache_key = self._hash_question(question)
        
        with self.lock:
            if cache_key not in self.cache:
                return None
            
            response, timestamp = self.cache[cache_key]
            elapsed = time.time() - timestamp
            
            # Check if expired
            if elapsed > self.ttl_seconds:
                del self.cache[cache_key]
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(cache_key)
            return response
    
    def set(self, question: str, response: ChatResponse) -> None:
        """
        Store response in cache with current timestamp.
        If cache full, evict least recently used entry.
        
        Args:
            question (str): User's question
            response (ChatResponse): Generated response to cache
        """
        cache_key = self._hash_question(question)
        timestamp = time.time()
        
        with self.lock:
            # If key exists, remove it first to re-add at end
            if cache_key in self.cache:
                del self.cache[cache_key]
            
            # Add to cache
            self.cache[cache_key] = (response, timestamp)
            self.cache.move_to_end(cache_key)
            
            # Evict LRU if over max size
            if len(self.cache) > self.max_size:
                lru_key = next(iter(self.cache))  # First item (oldest)
                del self.cache[lru_key]
    
    def clear_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            int: Number of entries removed
        """
        current_time = time.time()
        keys_to_delete = []
        
        with self.lock:
            for cache_key, (response, timestamp) in self.cache.items():
                if current_time - timestamp > self.ttl_seconds:
                    keys_to_delete.append(cache_key)
            
            for key in keys_to_delete:
                del self.cache[key]
        
        return len(keys_to_delete)
    
    def clear_all(self) -> None:
        """Clear entire cache."""
        with self.lock:
            self.cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with size, max_size, ttl_seconds
        """
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds
            }


# Global cache instance
_cache_instance: Optional[CacheService] = None

def get_cache_service(ttl_seconds: int = 420, max_size: int = 100) -> CacheService:
    """
    Get or create singleton cache service instance.
    
    Args:
        ttl_seconds (int): Cache TTL in seconds
        max_size (int): Maximum cache entries
    
    Returns:
        CacheService: Singleton instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService(ttl_seconds=ttl_seconds, max_size=max_size)
    return _cache_instance
