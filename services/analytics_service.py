"""Analytics and monitoring service for system performance."""

from typing import Dict, Any
from datetime import datetime
from collections import deque

from config.logger import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Track system performance metrics."""

    def __init__(self, max_history: int = 1000) -> None:
        self.total_queries = 0
        self.total_errors = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.response_times: deque = deque(maxlen=max_history)
        self.query_history: deque = deque(maxlen=max_history)

    def record_query(
        self,
        question: str,
        response_time: float,
        success: bool,
        cache_hit: bool = False,
        model: str = "mistral",
    ) -> None:
        """Record a query execution."""
        self.total_queries += 1

        if not success:
            self.total_errors += 1

        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        self.response_times.append(response_time)
        self.query_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "question": question[:100],
                "response_time": response_time,
                "success": success,
                "cache_hit": cache_hit,
                "model": model,
            }
        )

        logger.info(
            f"Query recorded: {response_time:.3f}s, cache_hit={cache_hit}, success={success}"
        )

    def get_analytics(self) -> Dict[str, Any]:
        """Get current analytics snapshot."""
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times
            else 0.0
        )

        cache_total = self.cache_hits + self.cache_misses
        cache_hit_rate = (
            (self.cache_hits / cache_total * 100) if cache_total > 0 else 0.0
        )

        error_rate = (
            (self.total_errors / self.total_queries * 100)
            if self.total_queries > 0
            else 0.0
        )

        return {
            "total_queries": self.total_queries,
            "total_errors": self.total_errors,
            "error_rate_percent": round(error_rate, 2),
            "average_response_time_seconds": round(avg_response_time, 3),
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "timestamp": datetime.now().isoformat(),
        }

    def get_query_history(self, limit: int = 50) -> list:
        """Get recent query history."""
        return list(self.query_history)[-limit:]

    def reset(self) -> None:
        """Reset all metrics."""
        self.total_queries = 0
        self.total_errors = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.response_times.clear()
        self.query_history.clear()
        logger.info("Analytics reset")

    def get_summary(self) -> str:
        """Get human-readable summary."""
        stats = self.get_analytics()
        return (
            f"📊 System Performance:\n"
            f"• Total Queries: {stats['total_queries']}\n"
            f"• Avg Response: {stats['average_response_time_seconds']}s\n"
            f"• Cache Hit Rate: {stats['cache_hit_rate_percent']}%\n"
            f"• Error Rate: {stats['error_rate_percent']}%"
        )


_global_analytics = AnalyticsService()


def get_analytics_service() -> AnalyticsService:
    """Get global analytics service singleton."""
    return _global_analytics
