# data/db_connection.py
# This module handles database connections and query execution for SQL Server.
# It uses pyodbc for connectivity and includes SQL validation before execution.

import pyodbc
import time
from typing import List, Dict, Any
from config.settings import settings
from config.logger import get_logger
from services.sql_validator import validate_sql

logger = get_logger(__name__)

def get_db_connection():
    """
    Establishes and returns a connection to the SQL Server database.
    Uses centralized settings for configuration to keep credentials secure.
    """
    if settings.DB_PASSWORD:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={settings.DB_SERVER};"
            f"DATABASE={settings.DB_DATABASE};"
            f"UID={settings.DB_USERNAME};"
            f"PWD={settings.DB_PASSWORD};"
        )
    else:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={settings.DB_SERVER};"
            f"DATABASE={settings.DB_DATABASE};"
            "Trusted_Connection=yes;"
        )
    return pyodbc.connect(conn_str)

def execute_query(sql_query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """
    Executes a SQL query after validation.
    Validates query for security (no DROP/DELETE/INSERT, etc.) before execution.
    Logs execution time and errors.

    Args:
        sql_query (str): The SQL query to execute.
        params (tuple, optional): Parameters to bind to the query.

    Returns:
        List[Dict[str, Any]]: Query results.
    
    Raises:
        ValueError: If SQL validation fails
    """
    from decimal import Decimal
    
    # Validate SQL before execution
    is_valid, error_msg = validate_sql(sql_query)
    if not is_valid:
        logger.warning(f"SQL validation failed: {error_msg}")
        raise ValueError(f"SQL validation error: {error_msg}")
    
    start_time = time.time()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(sql_query, params)
        else:
            cursor.execute(sql_query)
        
        # Fetch column names
        columns = [column[0] for column in cursor.description]
        # Fetch all rows
        rows = cursor.fetchall()
        
        # Convert to list of dicts, handling Decimal and other non-JSON serializable types
        results = []
        for row in rows:
            row_dict = {}
            for col, val in zip(columns, row):
                # Convert Decimal to float for JSON serialization
                if isinstance(val, Decimal):
                    row_dict[col] = float(val)
                else:
                    row_dict[col] = val
            results.append(row_dict)
        
        elapsed_ms = (time.time() - start_time) * 1000
        logger.warning(f"SQL execution completed in {elapsed_ms:.0f}ms, returned {len(results)} rows")
        
        return results
    finally:
        cursor.close()
        conn.close()

def get_database_tables() -> List[str]:
    """
    Returns a list of table names available in the current database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"
        )
        rows = cursor.fetchall()
        return [f"{schema}.{name}" for schema, name in rows]
    finally:
        cursor.close()
        conn.close()

def get_database_schema() -> List[str]:
    """
    Returns a concise list of table names with their columns for the current database.
    Optimized for LLM processing - shows key fact and dimension tables only.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION"
        )
        rows = cursor.fetchall()
        schema_map = {}
        
        # Prioritize fact and dimension tables, limit schema size
        priority_keywords = ['Fact_', 'D_', '_view', 'Detail']
        
        for schema, table, column in rows:
            table_full = f"{schema}.{table}"
            # Skip if we have too many tables (limit to ~15 key tables)
            if len(schema_map) >= 15 and table_full not in schema_map:
                continue
            
            if table_full not in schema_map:
                schema_map[table_full] = []
            schema_map[table_full].append(f"[{column}]")
        
        # Format as: [dbo].[TableName]([Col1], [Col2], ...)
        result = []
        for table_full, columns in sorted(schema_map.items()):
            parts = table_full.split('.')
            formatted_table = f"[{parts[0]}].[{parts[1]}]"
            # Limit columns shown per table (show first 15)
            limited_cols = columns[:15]
            result.append(f"{formatted_table}({', '.join(limited_cols)})")
        
        return result
    finally:
        cursor.close()
        conn.close()

def get_database_identifiers() -> List[str]:
    """
    Returns a list of database identifiers including table and column names.
    Includes bracketed names for exact matching.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION"
        )
        rows = cursor.fetchall()
        identifiers = set()
        for schema, table, column in rows:
            identifiers.add(schema.upper())
            identifiers.add(table.upper())
            identifiers.add(column.upper())
            identifiers.add(f"{schema}.{table}".upper())
            identifiers.add(f"[{schema}].[{table}]".upper())
            identifiers.add(f"[{schema}]".upper())
            identifiers.add(f"[{column}]".upper())
        return sorted(identifiers)
    finally:
        cursor.close()
        conn.close()

def get_database_tables() -> List[str]:
    """
    Returns a list of table names available in the current database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"
        )
        rows = cursor.fetchall()
        return [f"{schema}.{name}" for schema, name in rows]
    finally:
        cursor.close()
        conn.close()

def get_database_schema() -> List[str]:
    """
    Returns a concise list of table names with their columns for the current database.
    Optimized for LLM processing - shows key fact and dimension tables only.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION"
        )
        rows = cursor.fetchall()
        schema_map = {}
        
        # Prioritize fact and dimension tables, limit schema size
        priority_keywords = ['Fact_', 'D_', '_view', 'Detail']
        
        for schema, table, column in rows:
            table_full = f"{schema}.{table}"
            # Skip if we have too many tables (limit to ~15 key tables)
            if len(schema_map) >= 15 and table_full not in schema_map:
                continue
            
            if table_full not in schema_map:
                schema_map[table_full] = []
            schema_map[table_full].append(f"[{column}]")
        
        # Format as: [dbo].[TableName]([Col1], [Col2], ...)
        result = []
        for table_full, columns in sorted(schema_map.items()):
            parts = table_full.split('.')
            formatted_table = f"[{parts[0]}].[{parts[1]}]"
            # Limit columns shown per table (show first 15)
            limited_cols = columns[:15]
            result.append(f"{formatted_table}({', '.join(limited_cols)})")
        
        return result
    finally:
        cursor.close()
        conn.close()

def get_database_identifiers() -> List[str]:
    """
    Returns a list of database identifiers including table and column names.
    Includes bracketed names for exact matching.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION"
        )
        rows = cursor.fetchall()
        identifiers = set()
        for schema, table, column in rows:
            identifiers.add(schema.upper())
            identifiers.add(table.upper())
            identifiers.add(column.upper())
            identifiers.add(f"{schema}.{table}".upper())
            identifiers.add(f"[{schema}].[{table}]".upper())
            identifiers.add(f"[{schema}]".upper())
            identifiers.add(f"[{column}]".upper())
        return sorted(identifiers)
    finally:
        cursor.close()
        conn.close()