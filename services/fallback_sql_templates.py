# services/fallback_sql_templates.py
# Rule-based SQL template system for common BI questions.
# Uses regex pattern matching and keyword detection (FR + EN) to select appropriate templates.

import re
import unicodedata
from typing import Optional

class FallbackSQLTemplates:
    """
    Rule-based SQL template system with 8 core templates:
    1. TOP CUSTOMERS: "top 10 clients" → Top customers by sales amount
    2. LOYAL CUSTOMERS: "client fidèle" → Loyal/high-value customers
    3. MONTHLY AMOUNTS: "montant par mois" → Monthly aggregation of amounts
    4. BY CUSTOMER: "par client" → Breakdown by customer
    5. YEAR COMPARISON: "CA 2023 VS 2024" → Compare revenue by year
    6. YEARLY TOTAL: "total par an" → Aggregation by year
    7. LAST N MONTHS: "last 12 months" → Recent period aggregation
    8. MONTHLY COMPARISON: "janvier vs février" → Compare specific months
    
    Supports both French and English keywords.
    """
    
    def __init__(self):
        """Initialize template patterns."""
        self.patterns = [
            {
                'name': 'overdue_customers',
                'keywords_en': ['overdue', 'late', 'past due', 'unpaid', 'arrears'],
                'keywords_fr': ['retard', 'en retard', 'impaye', 'impayé', 'echeance depassee'],
                'pattern': r'(client|customer).*?(retard|impaye|impaye|overdue|late)|'
                           r'(retard|impaye|impaye|overdue|late).*?(client|customer)',
                'template': self._template_overdue_customers
            },
            {
                'name': 'loyalty_customers',
                'keywords_en': ['loyal', 'best', 'top', 'major', 'key', 'high-value'],
                'keywords_fr': ['fidèle', 'fidele', 'loyal', 'meilleur', 'principal', 'majeur', 'valeur'],
                'pattern': r'(fidele|loyal|meilleur|top).{0,40}(client|customer|clients|customers)|'
                           r'(client|customer|clients|customers).{0,40}(fidele|loyal|meilleur|top)',
                'template': self._template_loyalty_customers
            },
            {
                'name': 'year_comparison',
                'keywords_en': ['vs', 'versus', 'compare', 'year', 'ca', 'revenue', '2023', '2024', '2025'],
                'keywords_fr': ['vs', 'versus', 'comparer', 'an', 'ca', 'année', 'revenu'],
                'pattern': r'(vs|versus|vs\.|\bca\b|revenu).*?(20\d{2}|an|ann|year)',
                'template': self._template_year_comparison
            },
            {
                'name': 'top_customers',
                'keywords_en': ['top', 'best', 'leading'],
                'keywords_fr': ['top', 'meilleur', 'principal'],
                'pattern': r'top\s*(\d+)?\s*(client|customer|vente|sale)',
                'template': self._template_top_customers
            },
            {
                'name': 'monthly_amounts',
                'keywords_en': ['monthly', 'month', 'per month', 'amount', 'total'],
                'keywords_fr': ['mois', 'montant', 'somme', 'total', 'par mois'],
                'pattern': r'(montant|amount|somme|total).*?(par.*mois|monthly|month)',
                'template': self._template_monthly_amounts
            },
            {
                'name': 'by_customer',
                'keywords_en': ['customer', 'per customer', 'by customer'],
                'keywords_fr': ['client', 'par client'],
                'pattern': r'(par\s*client|by\s*customer)',
                'template': self._template_by_customer
            },
            {
                'name': 'yearly_total',
                'keywords_en': ['by year', 'per year', 'annual', 'yearly'],
                'keywords_fr': ['par an', 'par annee', 'annuel', 'annuelle'],
                'pattern': r'(par\s*an|par\s*annee|annual|yearly|by\s*year)',
                'template': self._template_yearly_total
            },
            {
                'name': 'last_n_months',
                'keywords_en': ['last', 'months', 'recent', 'past'],
                'keywords_fr': ['dernier', 'mois', 'recent', 'pass'],
                'pattern': r'(last|dernier|past|recent)\s*(\d+)?\s*(month|mois)',
                'template': self._template_last_n_months
            },
        ]
    
    def _normalize_question(self, question: str) -> str:
        """
        Normalize question for pattern matching.
        Converts to lowercase and removes accents.
        
        Args:
            question (str): User's question
        
        Returns:
            str: Normalized question
        """
        # Lowercase
        question = question.lower()

        # Remove wrapping quotes and punctuation noise around the question.
        question = question.replace('"', ' ').replace("'", ' ')
        
        # Remove accents
        nfd = unicodedata.normalize('NFD', question)
        without_accents = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')

        # Collapse repeated spaces for more stable regex matching.
        without_accents = re.sub(r'\s+', ' ', without_accents).strip()
        
        return without_accents

    def _template_overdue_customers(self, question: str) -> str:
        """
        Template: overdue clients (e.g., "clients en retard").

        SQL: open customer ledger entries with due date before today.
        """
        sql = """
SELECT TOP 50
    cle.[Customer No_],
    c.[Name] AS [Customer Name],
    cle.[Document No_],
    cle.[Due Date],
    cle.[Posting Date],
    cle.[Entry No_]
FROM [dbo].[D_CustomerLedgerEntry] cle
LEFT JOIN [dbo].[D_customer] c
    ON c.[No_] = cle.[Customer No_]
WHERE cle.[Open] = 1
  AND cle.[Due Date] < CAST(GETDATE() AS DATE)
ORDER BY cle.[Due Date] ASC
        """.strip()

        return sql
    
    def _extract_top_n(self, question: str) -> int:
        """Extract TOP N value from question (default: 10)."""
        match = re.search(r'top\s*(\d+)', question, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 10
    
    def _extract_month_count(self, question: str) -> int:
        """Extract month count from 'last N months' (default: 12)."""
        match = re.search(r'(\d+)\s*(month|mois)', question, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 12
    
    def _template_loyalty_customers(self, question: str) -> str:
        """
        Template: Loyal/high-value customers (e.g., "top 5 fidèle clients").
        
        SQL: Show top customers by total amount (loyalty metric)
        """
        top_n = self._extract_top_n(question)
        
        sql = f"""
SELECT TOP {top_n}
    c.[No_],
    c.[Name],
    SUM(f.[Amount]) AS [Total Amount] 
FROM [dbo].[D_customer] c
INNER JOIN [dbo].[Fact_CustomerPayementDetail] f
    ON c.[No_] = f.[Customer No_]
GROUP BY c.[No_], c.[Name]
ORDER BY [Total Amount] DESC
        """.strip()
        
        return sql
    
    def _template_year_comparison(self, question: str) -> str:
        """
        Template: Compare revenue/CA by year (e.g., "CA 2023 VS 2024").
        
        SQL: GROUP BY year, compare consecutive years
        """
        sql = """
SELECT
    YEAR([Posting Date]) AS [Year],
    SUM([Amount]) AS [Revenue CA]
FROM [dbo].[Fact_CustomerPayementDetail]
WHERE YEAR([Posting Date]) >= 2022
GROUP BY YEAR([Posting Date])
ORDER BY [Year] DESC
        """.strip()
        
        return sql
    
    def _template_yearly_total(self, question: str) -> str:
        """
        Template: Annual/yearly aggregation.
        
        SQL: GROUP BY year, show yearly totals
        """
        # Check if this is asking for a specific year only (like "CA 2024?")
        import re
        year_match = re.search(r'20\d{2}', question)
        if year_match and len(question.split()) <= 3:
            year = year_match.group()
            # Single year query - return CA for that year only
            sql = f"""
SELECT
    YEAR([Posting Date]) AS [Year],
    SUM([Amount]) AS [Chiffre d'affaires CA]
FROM [dbo].[Fact_CustomerPayementDetail]
WHERE YEAR([Posting Date]) = {year}
GROUP BY YEAR([Posting Date])
            """.strip()
        else:
            # Multi-year query - return all years
            sql = """
SELECT
    YEAR([Posting Date]) AS [Year],
    SUM([Amount]) AS [Chiffre d'affaires CA]
FROM [dbo].[Fact_CustomerPayementDetail]
GROUP BY YEAR([Posting Date])
ORDER BY [Year] DESC
            """.strip()
        
        return sql
    
    def _template_last_n_months(self, question: str) -> str:
        """
        Template: Last N months of data (e.g., "last 12 months").
        
        SQL: Show recent period aggregated by month
        """
        months = self._extract_month_count(question)
        
        sql = f"""
SELECT
    DATEFROMPARTS(YEAR([Posting Date]), MONTH([Posting Date]), 1) AS [Month],
    SUM([Amount]) AS [Total Amount]
FROM [dbo].[Fact_CustomerPayementDetail]
WHERE [Posting Date] >= DATEADD(MONTH, -{months}, GETDATE())
GROUP BY DATEFROMPARTS(YEAR([Posting Date]), MONTH([Posting Date]), 1)
ORDER BY [Month] DESC
        """.strip()
        
        return sql
    
    def _template_top_customers(self, question: str) -> str:
        """
        Template: Top N customers by sales amount.
        
        SQL: SELECT TOP N customer with highest amount from fact table
        """
        top_n = self._extract_top_n(question)
        
        sql = f"""
SELECT TOP {top_n}
    c.[No_],
    c.[Name],
    SUM(f.[Amount]) AS [Total Sales Amount]
FROM [dbo].[D_customer] c
INNER JOIN [dbo].[Fact_CustomerPayementDetail] f
    ON c.[No_] = f.[Customer No_]
GROUP BY c.[No_], c.[Name]
ORDER BY [Total Sales Amount] DESC
        """.strip()
        
        return sql
    
    def _template_monthly_amounts(self, question: str) -> str:
        """
        Template: Monthly aggregation of amounts (time-series).
        
        SQL: GROUP BY month, SUM amounts → good for Plotly line charts
        """
        sql = """
SELECT
    DATEFROMPARTS(YEAR([Posting Date]), MONTH([Posting Date]), 1) AS [Month],
    SUM([Amount]) AS [Total Amount]
FROM [dbo].[Fact_CustomerPayementDetail]
GROUP BY DATEFROMPARTS(YEAR([Posting Date]), MONTH([Posting Date]), 1)
ORDER BY [Month] ASC
        """.strip()
        
        return sql
    
    def _template_by_customer(self, question: str) -> str:
        """
        Template: Breakdown of amounts by customer.
        
        SQL: GROUP BY customer, SUM amounts → good for Plotly bar charts
        """
        sql = """
SELECT
    c.[No_],
    c.[Name] AS [Customer Name],
    SUM(f.[Amount]) AS [Total Amount]
FROM [dbo].[D_customer] c
INNER JOIN [dbo].[Fact_CustomerPayementDetail] f
    ON c.[No_] = f.[Customer No_]
GROUP BY c.[No_], c.[Name]
ORDER BY [Total Amount] DESC
        """.strip()
        
        return sql

    def _template_ledger_entries(self, question: str) -> str:
        """
        Template: Latest customer ledger entries.

        SQL: Show a simple list of entries for auditing or exploration.
        """
        sql = """
SELECT TOP 50
    [Entry No_],
    [Posting Date],
    [Document No_],
    [Description]
FROM [dbo].[D_CustomerLedgerEntry]
ORDER BY [Entry No_] DESC
        """.strip()

        return sql

    def _template_item_locations(self, question: str) -> str:
        """
        Template: Item and location summary.

        SQL: Aggregate item movements by item and location.
        """
        sql = """
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

        return sql
    
    def generate_fallback_sql(self, question: str) -> Optional[str]:
        """
        Generate SQL from question using pattern matching.
        
        Args:
            question (str): User's natural language question
        
        Returns:
            str: Generated SQL query, or None if no pattern matched
        """
        if not question or not isinstance(question, str):
            return None
        
        normalized = self._normalize_question(question)

        # Explicit deterministic dispatch for critical BI intents.
        if any(token in normalized for token in ["retard", "overdue", "late", "impaye", "impay"]) and any(
            token in normalized for token in ["client", "customer"]
        ):
            return self._template_overdue_customers(normalized)

        # STANDALONE YEAR QUERY (e.g., "2023?" or "2024?") - Must come BEFORE other CA patterns
        # This catches pure year queries and converts them to CA queries
        import re
        year_match = re.search(r'^.*?20\d{2}.*?$', normalized)
        if year_match and len(normalized.split()) <= 3 and normalized.rstrip('?').isdigit():
            # Pure year query like "2023?"
            return self._template_yearly_total(normalized)

        # "le client qui fait beaucoup" pattern - customer who buys/does the most
        if any(phrase in normalized for phrase in ["client qui fait", "customer who", "client qui", "beaucoup achat"]) or (
            "client" in normalized and "beaucoup" in normalized
        ):
            return self._template_by_customer(normalized)

        # MONTHLY/YEARLY BREAKDOWN queries - MUST come BEFORE general CA queries
        # Check for monthly queries first
        if any(token in normalized for token in ["montant", "amount", "somme", "total"]) and any(
            token in normalized for token in ["mois", "month", "par mois", "monthly"]
        ):
            return self._template_monthly_amounts(normalized)
        
        # Check for "CA par mois" specifically
        if "ca" in normalized and any(token in normalized for token in ["mois", "month", "par mois", "monthly"]):
            return self._template_monthly_amounts(normalized)

        # "CA / Revenue" queries - MUST check before general patterns
        if any(token in normalized for token in ["ca", "revenue", "chiffre", "affaires"]):
            # If it looks like a year or simple "ca" query, use yearly template
            if any(token in normalized for token in ["2023", "2024", "2025", "2022"]) or (
                len(normalized.split()) <= 3  # Very short query like "ca 2023?"
            ):
                return self._template_yearly_total(normalized)

        if any(token in normalized for token in ["fidele", "fideles", "loyal", "best", "high value"]) and any(
            token in normalized for token in ["client", "customer"]
        ):
            return self._template_loyalty_customers(normalized)

        if "top" in normalized and any(token in normalized for token in ["client", "customer", "vente", "sale"]):
            return self._template_top_customers(normalized)

        if any(token in normalized for token in ["par client", "by customer"]):
            return self._template_by_customer(normalized)

        if any(token in normalized for token in ["ledger", "ecriture", "entries", "entry", "show", "list", "display"]) and not any(
            token in normalized for token in ["vendor", "item"]
        ):
            return self._template_ledger_entries(normalized)

        if any(token in normalized for token in ["vs", "versus", "compare", "annee", "année", "year"]):
            if any(token in normalized for token in ["2023", "2024", "2025", "vs", "versus", "compare"]):
                return self._template_year_comparison(normalized)

        if any(token in normalized for token in ["par an", "annual", "yearly", "par annee", "par année"]):
            return self._template_yearly_total(normalized)

        if any(token in normalized for token in ["last", "dernier", "derniers", "recent", "past", "12 mois"]) and any(
            token in normalized for token in ["month", "mois"]
        ):
            return self._template_last_n_months(normalized)

        if any(token in normalized for token in ["item", "article", "location", "warehouse", "store"]):
            return self._template_item_locations(normalized)
        
        # Try each pattern in order
        for pattern_config in self.patterns:
            pattern = pattern_config['pattern']
            
            # Case-insensitive regex match
            if re.search(pattern, normalized, re.IGNORECASE):
                template_func = pattern_config['template']
                return template_func(normalized)
        
        # No pattern matched
        return None


# Global instance
_templates = FallbackSQLTemplates()

def generate_fallback_sql(question: str) -> Optional[str]:
    """
    Generate fallback SQL from question using rule-based templates.
    
    Args:
        question (str): User's question
    
    Returns:
        Optional[str]: Generated SQL or None if no pattern matched
    """
    return _templates.generate_fallback_sql(question)
