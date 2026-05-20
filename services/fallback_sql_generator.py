# services/fallback_sql_generator.py
# Fallback SQL generator for when Ollama fails to generate SQL.
# Provides template-based SQL generation for common business intelligence queries.

import unicodedata
from typing import Optional


def _normalize_question(question: str) -> str:
    """
    Lowercase the question and strip accents so French and English keywords
    can be matched reliably.
    """
    normalized = unicodedata.normalize("NFKD", question)
    normalized = "".join(character for character in normalized if not unicodedata.combining(character))
    return normalized.lower()

def generate_fallback_sql(question: str) -> Optional[str]:
    """
    Generate SQL using templates for common question patterns.
    Returns None if no matching pattern is found.
    
    Args:
        question: Natural language question from the user
        
    Returns:
        SQL query string or None if no pattern matches
    """
    question_lower = _normalize_question(question)

    # Pattern 0: Explicit customer payment detail totals / sums
    if any(keyword in question_lower for keyword in ['fact_customerpayementdetail', 'fact_customerpaymentdetail', 'paymentdetail', 'payment detail']) and any(
        keyword in question_lower for keyword in ['sum', 'somme', 'total', 'combien']
    ):
        return """
SELECT 
    DATEFROMPARTS(YEAR([Posting Date]), MONTH([Posting Date]), 1) AS [Month],
    SUM([Amount]) AS [Total Amount]
FROM [dbo].[Fact_CustomerPayementDetail]
GROUP BY DATEFROMPARTS(YEAR([Posting Date]), MONTH([Posting Date]), 1)
ORDER BY [Month]
        """.strip()
    
    # Pattern 1: Total sales / revenue / customer info
    if any(keyword in question_lower for keyword in ['total', 'sales', 'revenue', 'show', 'sum', 'somme', 'combien']):
        if 'customer' in question_lower:
            return """
SELECT TOP 20
    [Customer No_],
    COUNT(*) AS [Transaction Count],
    COUNT(DISTINCT [Document No_]) AS [Document Count]
FROM [dbo].[D_CustomerLedgerEntry]
GROUP BY [Customer No_]
ORDER BY [Transaction Count] DESC
            """.strip()
        else:
            # For sales, use D_ValueEntries which has Sales Amount and dates
            return """
SELECT 
    DATEFROMPARTS(YEAR([Posting Date]), MONTH([Posting Date]), 1) AS [Month],
    SUM([Sales Amount (Actual)]) AS [Total Sales]
FROM [dbo].[D_ValueEntries]
WHERE [Sales Amount (Actual)] IS NOT NULL
GROUP BY DATEFROMPARTS(YEAR([Posting Date]), MONTH([Posting Date]), 1)
ORDER BY [Month]
            """.strip()
    
    # Pattern 2: Top customers / items / vendors
    if any(keyword in question_lower for keyword in ['top', 'best', 'highest', 'most']):
        if 'customer' in question_lower:
            return """
SELECT TOP 10
    [Customer No_],
    COUNT(*) AS [Number of Transactions],
    COUNT(DISTINCT [Document No_]) AS [Number of Documents]
FROM [dbo].[D_CustomerLedgerEntry]
GROUP BY [Customer No_]
ORDER BY [Number of Transactions] DESC
            """.strip()
        elif 'vendor' in question_lower:
            return """
SELECT TOP 10
    [Entry No_],
    [Posting Date],
    [Document No_],
    [Description]
FROM [dbo].[D_VendorLedgerEntry]
ORDER BY [Posting Date] DESC
            """.strip()
        else:  # items
            return """
SELECT TOP 10
    [Item No_],
    COUNT(*) AS [Transaction Count],
    SUM([Sales Amount (Actual)]) AS [Total Sales]
FROM [dbo].[D_ValueEntries]
WHERE [Sales Amount (Actual)] IS NOT NULL
GROUP BY [Item No_]
ORDER BY [Total Sales] DESC
            """.strip()
    
    # Pattern 3: Recent transactions / entries / latest data
    if any(keyword in question_lower for keyword in ['recent', 'latest', 'last', 'entries', 'list', 'dernier', 'derniere', 'derniers', 'dernieres']):
        return """
SELECT TOP 50
    [Entry No_],
    [Posting Date],
    [Document No_],
    [Description]
FROM [dbo].[D_CustomerLedgerEntry]
ORDER BY [Posting Date] DESC
        """.strip()
    
    # Pattern 4: Ledger entries (all types)
    if 'ledger' in question_lower or 'ecriture' in question_lower or 'ecritures' in question_lower:
        if 'vendor' in question_lower:
            return """
SELECT TOP 100
    [Entry No_],
    [Posting Date],
    [Document No_],
    [Description]
FROM [dbo].[D_VendorLedgerEntry]
ORDER BY [Entry No_] DESC
            """.strip()
        elif 'item' in question_lower:
            return """
SELECT TOP 100
    [Entry No_],
    [Posting Date],
    [Item No_],
    [Source No_],
    [Document No_]
FROM [dbo].[D_ItemLedgerEntry]
ORDER BY [Entry No_] DESC
            """.strip()
        else:  # Default to customer ledger
            return """
SELECT TOP 100
    [Entry No_],
    [Posting Date],
    [Document No_],
    [Description]
FROM [dbo].[D_CustomerLedgerEntry]
ORDER BY [Entry No_] DESC
            """.strip()
    
    # Pattern 5: Item/locations
    if 'item' in question_lower or 'article' in question_lower or 'location' in question_lower or 'warehouse' in question_lower or 'store' in question_lower:
        return """
SELECT TOP 100
    [Item No_],
    [Location Code],
    COUNT(*) AS [Entry Count],
    SUM([Valued Quantity]) AS [Total Quantity Valued]
FROM [dbo].[D_ValueEntries]
WHERE [Location Code] IS NOT NULL
GROUP BY [Item No_], [Location Code]
ORDER BY [Total Quantity Valued] DESC
        """.strip()
    
    # Default pattern: Show entries from main table
    if any(keyword in question_lower for keyword in ['show', 'display', 'list', 'see', 'get', 'what', 'how', 'afficher', 'montre', 'donne', 'obtenir']):
        return """
SELECT TOP 50
    [Entry No_],
    [Posting Date],
    [Document No_],
    [Description]
FROM [dbo].[D_CustomerLedgerEntry]
ORDER BY [Entry No_] DESC
        """.strip()
    
    # No matching pattern found
    return """
SELECT TOP 50
    [Entry No_],
    [Posting Date],
    [Document No_],
    [Description]
FROM [dbo].[D_CustomerLedgerEntry]
ORDER BY [Entry No_] DESC
    """.strip()
