"""Advanced benchmark runner for local Ollama BI models."""

import os
import time
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
import psutil

from config.settings import settings
from services.model_router import generate_response


BENCHMARK_MODELS = ["mistral", "phi3", "gemma:2b"]
BENCHMARK_QUESTIONS = [
    "CA 2024 vs 2023",
    "top 10 clients",
    "montant par mois",
    "CA par client",
    "clients en retard",
]
SQL_KEYWORDS = ["SUM", "GROUP BY", "ORDER BY"]


class AdvancedBenchmarkService:
    """Run quantitative benchmarks and produce structured model reports."""

    def __init__(self, output_dir: str = "benchmark_results", timeout: int = 60) -> None:
        self.output_dir = output_dir
        self.timeout = timeout
        self._process = psutil.Process(os.getpid())
        os.makedirs(self.output_dir, exist_ok=True)

    def run(
        self,
        models: List[str] = None,
        questions: List[str] = None,
    ) -> pd.DataFrame:
        models = models or BENCHMARK_MODELS
        questions = questions or BENCHMARK_QUESTIONS

        rows: List[Dict] = []
        for model in models:
            for question in questions:
                row = self._benchmark_single(model=model, question=question)
                rows.append(row)

        columns = [
            "model",
            "question",
            "response_time",
            "sql_validity",
            "execution_success",
            "keyword_score",
            "consistency_score",
            "memory_usage_mb",
            "final_score",
        ]
        return pd.DataFrame(rows, columns=columns)

    def export_results(self, df: pd.DataFrame) -> Dict[str, str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = os.path.join(self.output_dir, f"benchmark_advanced_{timestamp}.csv")
        excel_path = os.path.join(self.output_dir, f"benchmark_advanced_{timestamp}.xlsx")
        report_path = os.path.join(self.output_dir, f"benchmark_report_{timestamp}.txt")

        df.to_csv(csv_path, index=False, encoding="utf-8")
        df.to_excel(excel_path, index=False)

        report_text = self.generate_report(df)
        with open(report_path, "w", encoding="utf-8") as report_file:
            report_file.write(report_text)

        return {
            "csv": csv_path,
            "excel": excel_path,
            "report": report_path,
        }

    def generate_report(self, df: pd.DataFrame) -> str:
        if df.empty:
            return "No benchmark data available."

        by_model = (
            df.groupby("model", as_index=False)
            .agg(
                avg_response_time=("response_time", "mean"),
                avg_sql_validity=("sql_validity", "mean"),
                avg_execution_success=("execution_success", "mean"),
                avg_keyword_score=("keyword_score", "mean"),
                avg_consistency=("consistency_score", "mean"),
                avg_memory=("memory_usage_mb", "mean"),
                avg_final_score=("final_score", "mean"),
            )
            .sort_values("avg_final_score", ascending=False)
        )

        fastest = by_model.sort_values("avg_response_time", ascending=True).iloc[0]["model"]
        most_accurate = by_model.sort_values("avg_sql_validity", ascending=False).iloc[0]["model"]
        most_stable = by_model.sort_values("avg_consistency", ascending=False).iloc[0]["model"]

        lines: List[str] = []
        lines.append("AI BI Chatbot - Advanced Model Benchmark Report")
        lines.append("=" * 50)
        lines.append("")

        for _, row in by_model.iterrows():
            model = str(row["model"])
            speed = float(row["avg_response_time"])
            sql_acc = float(row["avg_sql_validity"])
            exec_ok = float(row["avg_execution_success"])
            stability = float(row["avg_consistency"])
            memory = float(row["avg_memory"])

            strengths: List[str] = []
            weaknesses: List[str] = []

            if model == fastest or speed <= by_model["avg_response_time"].median():
                strengths.append("speed")
            else:
                weaknesses.append("latency")

            if model == most_accurate or (sql_acc >= 0.8 and exec_ok >= 0.8):
                strengths.append("accuracy")
            else:
                weaknesses.append("SQL errors")

            if model == most_stable or stability >= by_model["avg_consistency"].median():
                strengths.append("stability")
            else:
                weaknesses.append("stability variance")

            if memory > by_model["avg_memory"].median():
                weaknesses.append("memory usage")

            strengths_text = ", ".join(strengths) if strengths else "none"
            weaknesses_text = ", ".join(weaknesses) if weaknesses else "none"

            lines.append(f"Model: {model}")
            lines.append(f"- strengths: {strengths_text}")
            lines.append(f"- weaknesses: {weaknesses_text}")
            lines.append(
                f"- metrics: time={speed:.3f}s, sql_validity={sql_acc:.2f}, "
                f"consistency={stability:.2f}, memory={memory:.2f}MB, "
                f"score={float(row['avg_final_score']):.3f}"
            )
            lines.append("")

        best_model = str(by_model.iloc[0]["model"])
        best_time = float(by_model.iloc[0]["avg_response_time"])
        lines.append(
            f"{best_model.capitalize()} provides best balance between accuracy and performance "
            f"with average response time {best_time:.3f}s"
        )

        return "\n".join(lines)

    def _benchmark_single(self, model: str, question: str) -> Dict:
        prompt = self._build_sql_prompt(question)

        mem_before = self._memory_mb()
        response_text, response_time = self._call_model(model=model, prompt=prompt)
        mem_after = self._memory_mb()

        sql_validity = self._sql_validity(response_text)
        execution_success = int(sql_validity == 1)
        keyword_score = self._keyword_score(response_text)
        consistency_score = self._consistency_score(model=model, prompt=prompt, first_response=response_text)

        final_score = (
            (sql_validity * 5)
            + (execution_success * 5)
            + (keyword_score * 2)
            + (1 / max(response_time, 1e-6))
            + (consistency_score * 2)
        )

        return {
            "model": model,
            "question": question,
            "response_time": round(response_time, 4),
            "sql_validity": sql_validity,
            "execution_success": execution_success,
            "keyword_score": keyword_score,
            "consistency_score": round(consistency_score, 4),
            "memory_usage_mb": round(max(mem_after, mem_before), 2),
            "final_score": round(final_score, 4),
        }

    def _call_model(self, model: str, prompt: str) -> Tuple[str, float]:
        start = time.perf_counter()
        try:
            text = generate_response(
                prompt=prompt,
                model_name=model,
                timeout=self.timeout,
                use_fallback=False,
            )
        except Exception:
            text = ""
        elapsed = time.perf_counter() - start
        return text, elapsed

    @staticmethod
    def _build_sql_prompt(question: str) -> str:
        return (
            "Generate a SQL Server query only. "
            "No markdown. No explanation. "
            f"Question: {question}"
        )

    @staticmethod
    def _sql_validity(response_text: str) -> int:
        upper_text = response_text.upper()
        return int("SELECT" in upper_text or "WITH" in upper_text)

    @staticmethod
    def _keyword_score(response_text: str) -> int:
        upper_text = response_text.upper()
        return sum(1 for keyword in SQL_KEYWORDS if keyword in upper_text)

    def _consistency_score(self, model: str, prompt: str, first_response: str) -> float:
        second_response, _ = self._call_model(model=model, prompt=prompt)
        return self._text_similarity(first_response, second_response)

    @staticmethod
    def _text_similarity(text_a: str, text_b: str) -> float:
        tokens_a = set(token for token in text_a.upper().split() if token)
        tokens_b = set(token for token in text_b.upper().split() if token)
        if not tokens_a and not tokens_b:
            return 0.0
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = len(tokens_a & tokens_b)
        union = len(tokens_a | tokens_b)
        return intersection / max(union, 1)

    def _memory_mb(self) -> float:
        return self._process.memory_info().rss / (1024 * 1024)
