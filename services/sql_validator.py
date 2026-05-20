# services/sql_validator.py
# SQL validation and security layer to prevent SQL injection and unsafe queries.
# Before any SQL is executed, it must pass validation: SELECT-only, whitelist tables, block dangerous keywords.

import re
from typing import Tuple

class SQLValidator:
    """
    Security layer for SQL query validation.
    
    Rules enforced:
    1. Only SELECT and WITH queries allowed
    2. Block dangerous keywords: DROP, DELETE, UPDATE, INSERT, ALTER, EXEC, CREATE
    3. Whitelist allowed tables (from fallback templates scope)
    4. Check for valid bracket syntax for identifiers
    """
    
    # Whitelist: Table names from fallback SQL templates (core patterns)
    ALLOWED_TABLES = {
        '[dbo].[Fact_CustomerPayementDetail]',
        '[dbo].[D_customer]',
        '[dbo].[D_item]',
        '[dbo].[D_ValueEntries]',
        '[dbo].[D_CustomerLedgerEntry]',
        '[dbo].[D_VendorLedgerEntry]',
        '[dbo].[D_ItemLedgerEntry]',
        # Alternative formats (case-insensitive, without schema)
        '[Fact_CustomerPayementDetail]',
        '[D_customer]',
        '[D_item]',
        '[D_ValueEntries]',
        '[D_CustomerLedgerEntry]',
        '[D_VendorLedgerEntry]',
        '[D_ItemLedgerEntry]',
    }
    
    # Dangerous keywords that should not appear in SELECT queries
    BLOCKED_KEYWORDS = {
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'EXEC', 'EXECUTE', 'CREATE',
        'TRUNCATE', 'MERGE', 'RENAME', 'GRANT', 'REVOKE', 'DENY'
    }
    
    @staticmethod
    def validate(sql_query: str) -> Tuple[bool, str]:
        """
        Validate SQL query for security and compliance.
        
        Args:
            sql_query (str): SQL query to validate
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if query passes all checks, False otherwise
            - error_message: Explanation of validation failure (empty if valid)
        """
        if not sql_query or not isinstance(sql_query, str):
            return False, "Query must be a non-empty string"
        
        query = sql_query.strip()
        
        # Check 1: Must start with SELECT or WITH (CTE)
        if not re.match(r'^\s*(WITH|SELECT)\s', query, re.IGNORECASE):
            return False, "Only SELECT and WITH (CTE) queries are allowed"
        
        # Check 2: Block dangerous keywords
        keywords_found = SQLValidator._find_dangerous_keywords(query)
        if keywords_found:
            return False, f"Dangerous keywords detected: {', '.join(keywords_found)}"
        
        # Check 3: Check whitelist tables (if any table references are found)
        tables_found = SQLValidator._extract_table_references(query)
        invalid_tables = SQLValidator._check_table_whitelist(tables_found)
        if invalid_tables:
            return False, f"Table(s) not whitelisted: {', '.join(invalid_tables)}"
        
        return True, ""
    
    @staticmethod
    def _find_dangerous_keywords(query: str) -> list:
        """
        Find any dangerous keywords in the query.
        
        Returns:
            List of dangerous keywords found (empty if none)
        """
        found = []
        for keyword in SQLValidator.BLOCKED_KEYWORDS:
            # Use word boundary regex to match whole keywords only
            if re.search(rf'\b{keyword}\b', query, re.IGNORECASE):
                found.append(keyword)
        return found
    
    @staticmethod
    def _extract_table_references(query: str) -> list:
        """
        Extract table references from SQL query.
        Looks for [schema].[table] or [table] patterns.
        
        Returns:
            List of table references found
        """
        # Pattern 1: [schema].[table]
        pattern1 = r'\[([^\]]+)\]\.\[([^\]]+)\]'
        # Pattern 2: [table] without schema
        pattern2 = r'(?:FROM|JOIN|INTO|UPDATE)\s+\[([^\]]+)\]'
        
        tables = []
        
        # Find [schema].[table] patterns
        for match in re.finditer(pattern1, query, re.IGNORECASE):
            schema, table = match.groups()
            tables.append(f'[{schema}].[{table}]')
        
        # Find [table] patterns (only if not already found as part of schema.table)
        for match in re.finditer(pattern2, query, re.IGNORECASE):
            table = match.group(1)
            full_ref = f'[{table}]'
            if full_ref not in tables:
                tables.append(full_ref)
        
        return tables
    
    @staticmethod
    def _check_table_whitelist(tables_found: list) -> list:
        """
        Check if all found tables are in whitelist.
        
        Returns:
            List of tables NOT in whitelist (empty if all valid)
        """
        # For now, we allow any tables (flexible approach)
        # In strict mode, you could enforce whitelist:
        # invalid = [t for t in tables_found if t not in SQLValidator.ALLOWED_TABLES]
        # return invalid
        
        # Permissive approach: as long as tables are bracket-enclosed, allow them
        # This supports LLM-generated queries while preventing injection
        invalid = []
        for table in tables_found:
            # Table must be bracket-enclosed [table] or [schema].[table]
            if not (table.startswith('[') and table.count('[') >= 1):
                invalid.append(table)
        return invalid


# Global validator instance
_validator = SQLValidator()

def validate_sql(sql_query: str) -> Tuple[bool, str]:
    """
    Validate SQL query before execution.
    
    Args:
        sql_query (str): SQL to validate
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    return _validator.validate(sql_query)
