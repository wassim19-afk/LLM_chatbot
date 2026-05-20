# utils/visualization_helper.py
# Helper functions for intelligent chart type selection based on data characteristics.
# Analyzes result shape and suggests appropriate visualization type.

from typing import List, Dict, Any, Optional
from enum import Enum
import pandas as pd


MEASURE_KEYWORDS = [
    "amount",
    "total",
    "sales",
    "revenue",
    "ca",
    "sum",
    "count",
    "balance",
    "quantity",
    "qty",
    "value",
]

IDENTIFIER_KEYWORDS = [
    "id",
    "no_",
    "no",
    "entry",
    "document",
    "code",
    "ref",
    "number",
]

class ChartType(Enum):
    """Supported chart types."""
    METRIC = "metric"  # Single value
    LINE = "line"  # Time-series (date + numeric)
    BAR = "bar"  # Categorical (labels + values)
    PIE = "pie"  # Proportions (categories sum to 100%)
    TABLE = "table"  # Generic table (no special format)


class VisualizationHelper:
    """
    Intelligent visualization analyzer.
    Detects data patterns and recommends chart type.
    """
    
    @staticmethod
    def detect_chart_type(columns: List[str], data: List[Dict[str, Any]]) -> ChartType:
        """
        Analyze data and recommend chart type.
        
        Args:
            columns (List[str]): Column names from query result
            data (List[Dict[str, Any]]): Query result rows
        
        Returns:
            ChartType: Recommended chart type
        """
        if not data or len(data) == 0:
            return ChartType.TABLE
        
        # Pattern 1: Single row with single numeric value → METRIC
        if len(data) == 1 and len(columns) == 1:
            return ChartType.METRIC
        
        # Pattern 2: Single row with multiple values → METRIC (show first numeric)
        if len(data) == 1:
            return ChartType.METRIC
        
        # Analyze column types
        date_column = VisualizationHelper._find_date_column(columns, data)
        numeric_columns = VisualizationHelper._find_numeric_columns(columns, data)
        
        # Pattern 3: Time-series (date + numeric) → LINE
        if date_column and numeric_columns:
            return ChartType.LINE
        
        # Pattern 4: Multiple rows with numeric values → BAR (categorical)
        if numeric_columns and len(data) > 1:
            return ChartType.BAR
        
        # Default: Generic table
        return ChartType.TABLE
    
    @staticmethod
    def _find_date_column(columns: List[str], data: List[Dict[str, Any]]) -> Optional[str]:
        """
        Find date/time column in data.
        Looks for column names with date, month, posting, time keywords.
        """
        date_keywords = ['date', 'month', 'posting', 'time', 'year', 'day', 'created', 'modified']
        
        for col in columns:
            col_lower = col.lower()
            
            # Check keywords in column name
            if any(keyword in col_lower for keyword in date_keywords):
                # Verify at least one value is date-like
                for row in data:
                    val = row.get(col)
                    if val and VisualizationHelper._is_date_value(val):
                        return col
        
        return None
    
    @staticmethod
    def _find_numeric_columns(columns: List[str], data: List[Dict[str, Any]]) -> List[str]:
        """Find numeric (int, float) columns in data."""
        numeric_cols = []
        
        for col in columns:
            col_lower = col.lower()

            # Ignore identifier-like numeric columns to avoid misleading charts.
            if any(keyword in col_lower for keyword in IDENTIFIER_KEYWORDS):
                continue

            # Check first non-null value
            for row in data:
                val = row.get(col)
                if val is not None:
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        # Prefer true measures over raw technical numbers.
                        if not any(keyword in col_lower for keyword in MEASURE_KEYWORDS) and len(data) > 1:
                            break
                        numeric_cols.append(col)
                    break
        
        return numeric_cols
    
    @staticmethod
    def _is_date_value(val: Any) -> bool:
        """Check if value is a date."""
        import datetime
        return isinstance(val, (datetime.date, datetime.datetime)) or (
            isinstance(val, str) and ('-' in val or '/' in val)
        )
    
    @staticmethod
    def prepare_data_for_line_chart(columns: List[str], data: List[Dict[str, Any]]) -> Optional[pd.DataFrame]:
        """
        Prepare data for line chart (time-series).
        Converts date column to datetime, sorts by date.
        
        Returns:
            DataFrame or None if date column not found
        """
        date_col = VisualizationHelper._find_date_column(columns, data)
        if not date_col:
            return None
        
        try:
            df = pd.DataFrame(data)
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.sort_values(by=date_col)
            return df
        except Exception:
            return None
    
    @staticmethod
    def prepare_data_for_bar_chart(columns: List[str], data: List[Dict[str, Any]], top_n: int = 10) -> pd.DataFrame:
        """
        Prepare data for bar chart (categorical).
        Limits to top N rows by first numeric column.
        
        Args:
            columns: Column names
            data: Query results
            top_n: Limit to top N rows (default: 10)
        
        Returns:
            Prepared DataFrame for bar chart
        """
        df = pd.DataFrame(data)
        
        # Find first numeric column to sort by
        numeric_cols = VisualizationHelper._find_numeric_columns(columns, data)
        if numeric_cols:
            sort_col = numeric_cols[0] if numeric_cols else None
            if sort_col:
                df = df.sort_values(by=sort_col, ascending=False)
        
        # Limit to top N
        return df.head(top_n)
    
    @staticmethod
    def extract_metric_value(data: List[Dict[str, Any]]) -> Optional[Any]:
        """Extract single metric value from single-row result."""
        if len(data) != 1:
            return None
        
        row = data[0]
        # Return first numeric or non-null value
        for val in row.values():
            if val is not None:
                return val
        
        return None


# Convenience functions
def detect_chart_type(columns: List[str], data: List[Dict[str, Any]]) -> ChartType:
    """Detect recommended chart type for data."""
    return VisualizationHelper.detect_chart_type(columns, data)


def prepare_line_chart_data(columns: List[str], data: List[Dict[str, Any]]) -> Optional[pd.DataFrame]:
    """Prepare data for line chart."""
    return VisualizationHelper.prepare_data_for_line_chart(columns, data)


def prepare_bar_chart_data(columns: List[str], data: List[Dict[str, Any]], top_n: int = 10) -> pd.DataFrame:
    """Prepare data for bar chart."""
    return VisualizationHelper.prepare_data_for_bar_chart(columns, data, top_n)


def get_metric_value(data: List[Dict[str, Any]]) -> Optional[Any]:
    """Extract metric value."""
    return VisualizationHelper.extract_metric_value(data)
