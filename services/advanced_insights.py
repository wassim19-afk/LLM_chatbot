"""Advanced deterministic insights generation engine."""

from typing import List, Dict, Any, Tuple
import statistics

from config.logger import get_logger

logger = get_logger(__name__)


class AdvancedInsightsEngine:
    """Generate deterministic business insights from query results."""

    @staticmethod
    def detect_trends(df: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect trend (increase/decrease) in numeric columns."""
        if len(df) < 2:
            return {}

        trends = {}
        numeric_columns = AdvancedInsightsEngine._get_numeric_columns(df)

        for col in numeric_columns:
            values = [
                float(row[col]) for row in df if row.get(col) is not None
            ]
            if len(values) < 2:
                continue

            first, last = values[0], values[-1]
            if first == 0:
                continue

            pct_change = ((last - first) / abs(first)) * 100

            trend = "📈 increase" if pct_change > 5 else "📉 decrease" if pct_change < -5 else "➡️ stable"
            trends[col] = {
                "trend": trend,
                "pct_change": round(pct_change, 2),
                "first": first,
                "last": last,
            }

        return trends

    @staticmethod
    def detect_anomalies(df: List[Dict[str, Any]]) -> Dict[str, List[int]]:
        """Detect spike or drop anomalies in numeric data."""
        if len(df) < 3:
            return {}

        anomalies = {}
        numeric_columns = AdvancedInsightsEngine._get_numeric_columns(df)

        for col in numeric_columns:
            values = [
                float(row[col]) for row in df if row.get(col) is not None
            ]
            if len(values) < 3:
                continue

            try:
                mean = statistics.mean(values)
                stdev = statistics.stdev(values)
            except (ValueError, statistics.StatisticsError):
                continue

            if stdev == 0:
                continue

            anomaly_indices = []
            for i, val in enumerate(values):
                z_score = abs((val - mean) / stdev)
                if z_score > 2.5:
                    anomaly_indices.append(i)

            if anomaly_indices:
                anomalies[col] = anomaly_indices

        return anomalies

    @staticmethod
    def top_contributors(
        df: List[Dict[str, Any]], value_col: str = None, top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """Identify top contributors (Pareto 80/20)."""
        if not df:
            return []

        numeric_columns = AdvancedInsightsEngine._get_numeric_columns(df)
        if value_col not in numeric_columns:
            value_col = numeric_columns[0] if numeric_columns else None

        if not value_col:
            return []

        summarized = {}
        for row in df:
            label_parts = [
                str(row.get(col, ""))
                for col in row.keys()
                if col != value_col
                and col.lower()
                not in ["id", "entry", "no_", "no", "number", "code"]
            ]
            label = " | ".join(label_parts[:2]) if label_parts else str(row.get(value_col))

            val = row.get(value_col)
            if val is not None:
                try:
                    summarized[label] = summarized.get(label, 0) + float(val)
                except (ValueError, TypeError):
                    pass

        sorted_contributors = sorted(
            summarized.items(), key=lambda x: x[1], reverse=True
        )
        return sorted_contributors[:top_n]

    @staticmethod
    def generate_insight(df: List[Dict[str, Any]], question: str = "") -> str:
        """Generate deterministic insight from data analysis."""
        if not df:
            return "No data to analyze."

        insights = []
        insights.append(f"📊 Result: {len(df)} rows")

        trends = AdvancedInsightsEngine.detect_trends(df)
        for col, trend_info in trends.items():
            insights.append(
                f"{trend_info['trend']}: {col} changed by {trend_info['pct_change']}%"
            )

        anomalies = AdvancedInsightsEngine.detect_anomalies(df)
        for col, indices in anomalies.items():
            insights.append(f"⚠️ Anomaly in {col} at {len(indices)} point(s)")

        value_col = AdvancedInsightsEngine._get_numeric_columns(df)[0] if AdvancedInsightsEngine._get_numeric_columns(df) else None
        if value_col:
            top = AdvancedInsightsEngine.top_contributors(df, value_col, 3)
            if top:
                insights.append("🔝 Top contributors:")
                for label, val in top:
                    insights.append(f"  • {label}: {val:.2f}")

        return " | ".join(insights) if insights else "Analysis complete."

    @staticmethod
    def _get_numeric_columns(df: List[Dict[str, Any]]) -> List[str]:
        """Identify numeric columns in dataframe."""
        if not df:
            return []

        numeric_cols = []
        for key in df[0].keys():
            try:
                float(df[0][key])
                numeric_cols.append(key)
            except (ValueError, TypeError):
                pass

        return numeric_cols


def get_advanced_insights(df: List[Dict[str, Any]], question: str = "") -> str:
    """Generate deterministic insights."""
    engine = AdvancedInsightsEngine()
    return engine.generate_insight(df, question)


def detect_trends(df: List[Dict[str, Any]]) -> Dict[str, Any]:
    return AdvancedInsightsEngine.detect_trends(df)


def detect_anomalies(df: List[Dict[str, Any]]) -> Dict[str, List[int]]:
    return AdvancedInsightsEngine.detect_anomalies(df)


def top_contributors(df: List[Dict[str, Any]], value_col: str = None, top_n: int = 5) -> List[Tuple[str, float]]:
    return AdvancedInsightsEngine.top_contributors(df, value_col=value_col, top_n=top_n)


def generate_insight(df: List[Dict[str, Any]], question: str = "") -> str:
    return AdvancedInsightsEngine.generate_insight(df, question=question)
