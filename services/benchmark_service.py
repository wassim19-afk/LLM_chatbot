"""Benchmarking service for evaluating Ollama models on BI questions."""

import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
import requests

from config.logger import get_logger


logger = get_logger(__name__)


@dataclass
class BenchmarkResult:
    """Structured benchmark result for one model/question pair."""

    model: str
    question: str
    response_time: float
    sql_valid: int
    keyword_score: int
    response_length: int
    final_score: float
    response_text: str


class BenchmarkService:
    """Runs benchmark experiments for one or more Ollama models."""

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434/api/generate",
        output_dir: str = "benchmark_results",
        timeout: int = 60,
    ) -> None:
        self.ollama_url = ollama_url
        self.output_dir = output_dir
        self.timeout = timeout
        os.makedirs(self.output_dir, exist_ok=True)

    def run_benchmark(self, models: List[str], questions: List[str]) -> List[Dict]:
        """Run all model/question combinations and return structured results."""
        results: List[Dict] = []

        for model in models:
            logger.warning("Benchmarking model: %s", model)
            for question in questions:
                result = self._evaluate_single(model=model, question=question)
                results.append(asdict(result))

        return results

    def export_results(self, results: List[Dict]) -> Dict[str, str]:
        """Export benchmark results to CSV and Excel files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df = pd.DataFrame(results)

        csv_path = os.path.join(self.output_dir, f"benchmark_results_{timestamp}.csv")
        excel_path = os.path.join(self.output_dir, f"benchmark_results_{timestamp}.xlsx")

        df.to_csv(csv_path, index=False, encoding="utf-8")
        df.to_excel(excel_path, index=False)

        logger.warning("Benchmark CSV saved: %s", csv_path)
        logger.warning("Benchmark Excel saved: %s", excel_path)

        return {"csv": csv_path, "excel": excel_path}

    def export_model_comparison_chart(self, results: List[Dict]) -> str:
        """Create a bar chart for average score per model if matplotlib is available."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.warning("matplotlib not installed. Skipping chart export.")
            return ""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_path = os.path.join(self.output_dir, f"benchmark_chart_{timestamp}.png")

        df = pd.DataFrame(results)
        avg_df = (
            df.groupby("model", as_index=False)["final_score"]
            .mean()
            .sort_values("final_score", ascending=False)
        )

        plt.figure(figsize=(8, 5))
        plt.bar(avg_df["model"], avg_df["final_score"])
        plt.title("Average Final Score by Model")
        plt.xlabel("Model")
        plt.ylabel("Average Final Score")
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150)
        plt.close()

        logger.warning("Benchmark chart saved: %s", chart_path)
        return chart_path

    def _evaluate_single(self, model: str, question: str) -> BenchmarkResult:
        """Evaluate one model response for one question."""
        response_text, response_time = self._call_ollama(model=model, question=question)

        sql_valid = self._sql_quality_detection(response_text)
        keyword_score = self._keyword_score(response_text)
        response_length = len(response_text)

        # Protect against division by zero in case of near-instant response.
        safe_response_time = max(response_time, 1e-6)
        final_score = (sql_valid * 5) + (keyword_score * 2) + (1 / safe_response_time)

        return BenchmarkResult(
            model=model,
            question=question,
            response_time=round(response_time, 4),
            sql_valid=sql_valid,
            keyword_score=keyword_score,
            response_length=response_length,
            final_score=round(final_score, 4),
            response_text=response_text,
        )

    def _call_ollama(self, model: str, question: str) -> Tuple[str, float]:
        """Call Ollama /api/generate and measure elapsed response time."""
        payload = {
            "model": model,
            "prompt": self._build_prompt(question),
            "stream": False,
        }

        start_time = time.perf_counter()
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            text = str(data.get("response", "")).strip()
        except requests.RequestException as exc:
            elapsed = time.perf_counter() - start_time
            logger.warning(
                "Ollama call failed for model=%s question=%s error=%s",
                model,
                question,
                exc,
            )
            # Keep benchmark run resilient by returning an empty response with measured time.
            return "", elapsed

        elapsed = time.perf_counter() - start_time
        return text, elapsed

    @staticmethod
    def _build_prompt(question: str) -> str:
        """Prompt tuned for SQL-like BI answer generation."""
        return (
            "Generate a SQL Server query only. "
            "No explanation, no markdown, no comments. "
            f"Business question: {question}"
        )

    @staticmethod
    def _sql_quality_detection(text: str) -> int:
        """Return 1 if SELECT exists, otherwise 0."""
        return int("SELECT" in text.upper())

    @staticmethod
    def _keyword_score(text: str) -> int:
        """Return count of required SQL keywords: SUM, GROUP BY, ORDER BY."""
        upper_text = text.upper()
        keywords = ["SUM", "GROUP BY", "ORDER BY"]
        return sum(1 for keyword in keywords if keyword in upper_text)
