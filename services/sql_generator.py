# services/sql_generator.py
# This module is responsible for generating SQL queries from natural language questions.
# It uses the LLM service to interpret the user's question and produce a valid SQL query.

import re
import logging
from typing import List, Optional

from services.llm_service import call_ollama
from utils.prompts import SQL_GENERATION_PROMPT, SQL_GENERATION_CORRECTION_PROMPT, ADVANCED_SQL_GENERATION_PROMPT
from data.db_connection import get_database_schema, get_database_identifiers
from services.fallback_sql_generator import generate_fallback_sql

logger = logging.getLogger("sql_generator")

def extract_sql_query(model_output: str) -> str:
    """
    Extract the first SQL Server query from the model output.
    This removes any explanation, code fences, or extra text before the SQL.statement.
    """
    output = model_output.strip()
    # Remove markdown code fences if present
    output = re.sub(r"```(?:sql)?\s*", "", output, flags=re.IGNORECASE)
    output = re.sub(r"\s*```$", "", output, flags=re.IGNORECASE)
    match = re.search(r"(^|\n)\s*(SELECT|WITH)\b", output, flags=re.IGNORECASE)
    if match:
        return output[match.start():].strip()
    return output

def normalize_sql(sql_query: str) -> str:
    """
    Normalize common SQL generation issues for SQL Server.
    """
    query = sql_query.strip()
    # Extract actual SQL if the model returned explanation text before it
    query = extract_sql_query(query)
    # Replace MySQL-style backticks with SQL Server bracket identifiers if present.
    query = re.sub(r"`([^`]*)`", r"[\1]", query)
    # Remove any remaining stray backticks.
    query = query.replace("`", "")
    # Normalize equality comparisons: use = for values, keep IS NULL / IS NOT NULL
    query = re.sub(r"\bIS\s+(?!NOT\s+NULL\b)(?!NULL\b)([^\s;]+)", r"= \1", query, flags=re.IGNORECASE)
    return query

def validate_sql(sql_query: str) -> None:
    """
    Validate the generated SQL query before execution.
    """
    normalized = sql_query.strip().upper()
    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        raise ValueError("Generated query must start with SELECT or WITH.")
    if any(keyword in normalized for keyword in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]):
        raise ValueError("Generated query contains prohibited commands.")
    if "`" in sql_query:
        raise ValueError("Generated query contains invalid backticks for SQL Server.")
    invalid_identifiers = find_invalid_identifiers(sql_query)
    if invalid_identifiers:
        raise ValueError(
            f"Generated query contains unknown identifiers: {', '.join(sorted(invalid_identifiers))}. "
            "Use only table and column names from the schema metadata."
        )

def _extract_tokens(sql_query: str) -> list[str]:
    sql_without_strings = re.sub(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"", " ", sql_query)
    tokens = []
    for match in re.finditer(r"\[([^\]]+)\]|\b[A-Za-z_][A-Za-z0-9_]*\b", sql_without_strings):
        token = match.group(1) if match.group(1) is not None else match.group(0)
        tokens.append(token)
    return tokens


def _extract_aliases(sql_query: str) -> set[str]:
    alias_patterns = [
        re.compile(r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)\b", flags=re.IGNORECASE),
        re.compile(
            r"\b(?:FROM|JOIN|INNER\s+JOIN|LEFT\s+(?:OUTER\s+)?JOIN|RIGHT\s+(?:OUTER\s+)?JOIN|FULL\s+(?:OUTER\s+)?JOIN|CROSS\s+JOIN)\s+"
            r"(?:\[[^\]]+\]|[A-Za-z_][A-Za-z0-9_]*)(?:\s*\.\s*(?:\[[^\]]+\]|[A-Za-z_][A-Za-z0-9_]*))*\s+([A-Za-z_][A-Za-z0-9_]*)\b",
            flags=re.IGNORECASE,
        ),
    ]
    aliases = set()
    for pattern in alias_patterns:
        for match in pattern.finditer(sql_query):
            aliases.add(match.group(1).upper())
    return aliases


def _extract_function_names(sql_query: str) -> set[str]:
    return {match.group(1).upper() for match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", sql_query)}


def find_invalid_identifiers(sql_query: str) -> List[str]:
    """
    Check query identifiers against actual database schema names.
    Enhanced to be smarter about what's actually invalid vs. acceptable.
    """
    allowed = set(get_database_identifiers())
    tokens = _extract_tokens(sql_query)
    aliases = _extract_aliases(sql_query)
    functions = _extract_function_names(sql_query)
    
    # SQL Server built-in functions
    sql_functions = {
        "SELECT", "FROM", "WHERE", "GROUP", "BY", "ORDER", "HAVING",
        "AND", "OR", "NOT", "NULL", "IS", "JOIN", "INNER", "LEFT",
        "RIGHT", "FULL", "ON", "AS", "IN", "BETWEEN", "LIKE",
        "SUM", "COUNT", "MIN", "MAX", "AVG", "DISTINCT", "TOP",
        "CASE", "WHEN", "THEN", "ELSE", "END", "CAST", "CONVERT",
        "WITH", "UNION", "ALL", "EXISTS", "OVER", "PARTITION",
        "CROSS", "OUTER", "VALUES", "LIMIT", "OFFSET", "FETCH", "NEXT",
        "ROWS", "ONLY", "ORDER", "BY", "ASC", "DESC",
        "DATEADD", "DATEDIFF", "GETDATE", "COALESCE", "YEAR", "MONTH", 
        "DAY", "DATEFROMPARTS", "DATETIMEFROMPARTS", "EOMONTH",
        "ISNULL", "IIF", "NULLIF", "REPLACE", "SUBSTRING", "LEN",
        "ROUND", "FLOOR", "CEILING", "ABS", "POWER", "SQRT",
        "LOWER", "UPPER", "LTRIM", "RTRIM", "REVERSE", "CHARINDEX",
        "GETUTCDATE", "SYSDATETIME", "CURRENT_TIMESTAMP",
    }
    
    invalid = set()
    for token in tokens:
        if not token:
            continue
        upper = token.upper()
        
        # Skip if it's a SQL keyword, alias, or function
        if upper in sql_functions or upper in aliases or upper in functions:
            continue
        
        # Skip if it's a number
        if upper.isdigit() or (upper.startswith('-') and upper[1:].isdigit()):
            continue
        
        # Skip if it's a string literal or boolean
        if upper in ['TRUE', 'FALSE', 'NULL']:
            continue
        
        # Skip if already bracketed correctly (shouldn't happen here but just in case)
        if token.startswith('[') and token.endswith(']'):
            continue
        
        # Check if lowercase (probably an alias assignment - valid)
        if token[0].islower():
            continue
        
        # If not in allowed identifiers, it's invalid
        if upper not in allowed:
            invalid.add(token)
    
    return sorted(invalid)


def _build_correction_prompt(question: str, schema_text: str, previous_sql: str, invalid_identifiers: List[str]) -> str:
    return SQL_GENERATION_CORRECTION_PROMPT.format(
        question=question,
        schema=schema_text,
        previous_sql=previous_sql,
        invalid_identifiers=", ".join(sorted(invalid_identifiers)),
    )


def is_complex_question(question: str) -> bool:
    """
    Detect if question is complex (requires aggregation, grouping, etc).
    
    Complex patterns:
    - Aggregations: "top", "best", "most", "average", "total", "sum"
    - Comparisons: "vs", "compare", "compared"
    - Time-based: "by month", "yearly", "2023 vs 2024", "trend"
    - Customer analysis: "customer who", "which customer", "client qui"
    - Filters: "where", "avec", "with condition"
    - Relationships: "loyalty", "overdue", "recent"
    """
    q_lower = question.lower()
    
    complex_keywords = [
        # Aggregations
        'top ', 'best ', 'most ', 'highest', 'lowest',
        'total', 'sum', 'average', 'count', 'how many',
        # Comparisons
        'vs', 'versus', 'compare', 'compared', 'comparison',
        # Time-based
        'by month', 'yearly', 'annual', 'trend', 'monthly',
        'last ', 'previous', 'prior', 'recent', 
        # Customer analysis
        'client qui', 'customer who', 'which client', 'which customer',
        'loyal', 'fidele', 'high value', 'best customer',
        # Relationships
        'overdue', 'late', 'past due', 'en retard', 'impaye',
        # Specific metrics
        'montant par', 'par client', 'by customer',
        'breakdown', 'distribution', 'split',
        # Query patterns
        'beaucoup', 'much', 'lot', 'many',
        'par', 'by', 'grouped', 'grouped by',
        'over time', 'trend', 'pattern',
    ]
    
    return any(keyword in q_lower for keyword in complex_keywords)


def generate_sql(question: str, model: Optional[str] = None) -> str:
    """
    Converts a natural language question into a SQL query using the LLM.
    
    For complex questions, tries template-based generation first, then falls back to LLM.
    Uses progressive improvement with better prompts on retry.

    Args:
        question (str): The user's natural language question.
        model (Optional[str]): Ollama model name override.

    Returns:
        str: The generated SQL query.
    """
    # For complex questions, try templates FIRST before LLM
    if is_complex_question(question):
        logger.warning(f"Detected complex question, trying template-based generation first")
        from services.fallback_sql_templates import generate_fallback_sql as gen_template
        template_sql = gen_template(question)
        if template_sql:
            logger.warning(f"Template-based SQL generated successfully")
            try:
                validate_sql(template_sql)
                return template_sql
            except ValueError as e:
                logger.warning(f"Template SQL validation failed: {e}, falling back to LLM")
    
    schema = get_database_schema()
    schema_text = "\n".join(schema) if schema else "No table metadata available."
    
    # Try with standard prompt first
    prompt = SQL_GENERATION_PROMPT.format(question=question, schema=schema_text)
    
    for attempt in range(3):  # Increased from 2 to 3 attempts
        if attempt == 0:
            # Standard prompt
            current_prompt = prompt
        elif attempt == 1:
            # Better prompt on second attempt (ADVANCED)
            logger.warning(f"Attempt {attempt + 1}: Using advanced prompt generation")
            current_prompt = ADVANCED_SQL_GENERATION_PROMPT.format(question=question, schema=schema_text)
        else:
            # Final attempt: even more detailed prompt
            logger.warning(f"Attempt {attempt + 1}: Using expert mode with step-by-step guidance")
            current_prompt = f"""{ADVANCED_SQL_GENERATION_PROMPT.format(question=question, schema=schema_text)}

REMEMBER:
- If you're unsure about a column, check if similar columns exist (e.g., [Amount], [Quantity])
- Always GROUP BY non-aggregated columns
- Always use TOP N for "top" queries
- Always LEFT JOIN to avoid losing rows"""
        
        sql_query = call_ollama(current_prompt, model=model)
        sql_query = normalize_sql(sql_query)
        
        try:
            validate_sql(sql_query)
            logger.warning(f"✓ SQL validated successfully on attempt {attempt + 1}")
            return sql_query
        except ValueError as error:
            error_message = str(error)
            logger.warning(f"Attempt {attempt + 1} failed: {error_message}")
            
            # Try to fix with correction prompt
            if "unknown identifiers" in error_message.lower():
                invalid_identifiers = find_invalid_identifiers(sql_query)
                if invalid_identifiers:
                    logger.warning(f"Attempting to fix invalid identifiers: {invalid_identifiers}")
                    correction_prompt = SQL_GENERATION_CORRECTION_PROMPT.format(
                        question=question,
                        schema=schema_text,
                        previous_sql=sql_query,
                        invalid_identifiers=", ".join(sorted(invalid_identifiers)),
                    )
                    corrected_sql = call_ollama(correction_prompt, model=model)
                    corrected_sql = normalize_sql(corrected_sql)
                    try:
                        validate_sql(corrected_sql)
                        logger.warning(f"✓ Corrected SQL validated successfully")
                        return corrected_sql
                    except ValueError:
                        logger.warning(f"Correction attempt failed, continuing to next attempt")
            
            # If this is the last attempt, raise
            if attempt == 2:
                raise
    
    return sql_query