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

        SQL: aggregate overdue amount per customer, sorted by most overdue amount.
        """
        sql = """
SELECT TOP 50
    cle.[Customer No_],
    c.[Name] AS [Customer Name],
    ROUND(SUM(cle.[Balance]), 0) AS [Montant Restant],
    COUNT(cle.[Entry No_]) AS [Nb Ecritures],
    MIN(cle.[Due Date]) AS [Echeance La Plus Ancienne]
FROM [dbo].[D_CustomerLedgerEntry] cle
LEFT JOIN [dbo].[D_customer] c
    ON c.[No_] = cle.[Customer No_]
WHERE cle.[Open] = 1
  AND cle.[Due Date] < CAST(GETDATE() AS DATE)
GROUP BY cle.[Customer No_], c.[Name]
ORDER BY [Montant Restant] DESC
        """.strip()

        return sql

    def _template_top_products(self, question: str) -> str:
        """
        Template: Top N products by sales or profit.
        Uses D_ValueEntries joined with D_item.
        """
        top_n = self._extract_top_n(question)
        normalized = self._normalize_question(question)

        is_profit = any(t in normalized for t in ["rentable", "profitable", "profit", "marge"])

        if is_profit:
            order_col = "[Total Profit]"
            extra_col = "    ROUND(SUM(v.[Sales Amount (Actual)]) - SUM(v.[Cost Amount (Actual)]), 0) AS [Total Profit],"
        else:
            order_col = "[Total Ventes]"
            extra_col = ""

        sql = f"""
SELECT TOP {top_n}
    i.[No_],
    i.[Description],
    ROUND(SUM(v.[Sales Amount (Actual)]), 0) AS [Total Ventes],
{extra_col}
    ROUND(SUM(v.[Valued Quantity]), 0) AS [Quantite Vendue]
FROM [dbo].[D_ValueEntries] v
INNER JOIN [dbo].[D_item] i
    ON i.[No_] = v.[Item No_]
WHERE v.[Sales Amount (Actual)] > 0
GROUP BY i.[No_], i.[Description]
ORDER BY {order_col} DESC
        """.strip()

        return sql

    def _template_top_vendors(self, question: str) -> str:
        """Top N fournisseurs par montant d'achat."""
        top_n = self._extract_top_n(question)
        sql = f"""
SELECT TOP {top_n}
    v.[Vendor No_],
    v.[Vendor Name],
    ROUND(SUM(v.[Purchase (LCY)]), 0) AS [Total Achats],
    COUNT(v.[Entry No_]) AS [Nb Factures]
FROM [dbo].[D_VendorLedgerEntry] v
WHERE v.[Document Type] IN (2, 4)
GROUP BY v.[Vendor No_], v.[Vendor Name]
ORDER BY [Total Achats] DESC
        """.strip()
        return sql

    def _template_vendor_overdue(self, question: str) -> str:
        """Fournisseurs avec paiements en retard."""
        sql = """
SELECT TOP 50
    v.[Vendor No_],
    v.[Vendor Name],
    ROUND(SUM(v.[Purchase (LCY)]), 0) AS [Montant Du],
    COUNT(v.[Entry No_]) AS [Nb Ecritures],
    MIN(v.[Due Date]) AS [Echeance La Plus Ancienne]
FROM [dbo].[D_VendorLedgerEntry] v
WHERE v.[Open] = 1
  AND v.[Due Date] < CAST(GETDATE() AS DATE)
GROUP BY v.[Vendor No_], v.[Vendor Name]
ORDER BY [Montant Du] DESC
        """.strip()
        return sql

    def _template_top_salespeople(self, question: str) -> str:
        """Top N vendeurs/commerciaux par CA depuis D_CustomerLedgerEntry."""
        top_n = self._extract_top_n(question)
        sql = f"""
SELECT TOP {top_n}
    e.[Salesperson Code] AS [Vendeur],
    ROUND(SUM(e.[Sales (LCY)]), 0) AS [Total CA],
    COUNT(e.[Entry No_]) AS [Nb Transactions],
    COUNT(DISTINCT e.[Customer No_]) AS [Nb Clients]
FROM [dbo].[D_CustomerLedgerEntry] e
WHERE e.[Salesperson Code] IS NOT NULL
  AND e.[Salesperson Code] <> ''
GROUP BY e.[Salesperson Code]
ORDER BY [Total CA] DESC
        """.strip()
        return sql

    def _template_payments_received(self, question: str) -> str:
        """Paiements / encaissements reçus (Credit Amount)."""
        sql = """
SELECT TOP 50
    f.[Customer No_],
    c.[Name] AS [Customer Name],
    ROUND(SUM(f.[Credit Amount]), 0) AS [Total Encaisse],
    COUNT(f.[Entry No_]) AS [Nb Paiements],
    MAX(f.[Posting Date]) AS [Dernier Paiement]
FROM [dbo].[Fact_CustomerPayementDetail] f
LEFT JOIN [dbo].[D_customer] c ON c.[No_] = f.[Customer No_]
WHERE f.[Document Type] = 2
  AND f.[Credit Amount] > 0
GROUP BY f.[Customer No_], c.[Name]
ORDER BY [Total Encaisse] DESC
        """.strip()
        return sql

    def _template_customer_balance(self, question: str) -> str:
        """Solde / encours ouvert par client via Detailed Customer Ledger Entries."""
        sql = """
SELECT TOP 50
    d.[Customer No_],
    c.[Name] AS [Customer Name],
    ROUND(SUM(d.[Amount]), 0) AS [Solde],
    COUNT(d.[Entry No_]) AS [Nb Ecritures]
FROM [dbo].[Detailed Customer Ledger Entries] d
LEFT JOIN [dbo].[D_customer] c ON c.[No_] = d.[Customer No_]
INNER JOIN [dbo].[D_CustomerLedgerEntry] cle
    ON cle.[Entry No_] = d.[Cust_ Ledger Entry No_] AND cle.[Open] = 1
GROUP BY d.[Customer No_], c.[Name]
HAVING ROUND(SUM(d.[Amount]), 0) <> 0
ORDER BY [Solde] DESC
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
        
        SQL: Show top customers by total amount + transaction count (loyalty metrics)
        """
        top_n = self._extract_top_n(question)
        
        sql = f"""
SELECT TOP {top_n}
    c.[No_],
    c.[Name],
    ROUND(SUM(f.[Amount]), 0) AS [Total Amount],
    COUNT(f.[Entry No_]) AS [Nb Transactions]
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
        Extracts the exact years mentioned and filters to only those.
        """
        years = re.findall(r'20\d{2}', question)
        years = sorted(set(int(y) for y in years))

        if len(years) >= 2:
            year_list = ', '.join(str(y) for y in years)
            where_clause = f"WHERE YEAR([Posting Date]) IN ({year_list})"
        elif len(years) == 1:
            where_clause = f"WHERE YEAR([Posting Date]) = {years[0]}"
        else:
            where_clause = "WHERE YEAR([Posting Date]) >= YEAR(GETDATE()) - 1"

        sql = f"""
SELECT
    YEAR([Posting Date]) AS [Year],
    SUM([Amount]) AS [CA Total]
FROM [dbo].[Fact_CustomerPayementDetail]
{where_clause}
GROUP BY YEAR([Posting Date])
ORDER BY [Year] ASC
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
    SUM([Amount]) AS [CA Total]
FROM [dbo].[Fact_CustomerPayementDetail]
WHERE YEAR([Posting Date]) = {year}
GROUP BY YEAR([Posting Date])
            """.strip()
        else:
            # Multi-year query - return all years
            sql = """
SELECT
    YEAR([Posting Date]) AS [Year],
    SUM([Amount]) AS [CA Total]
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

    def _template_sales_detail(self, question: str) -> str:
        """Top products/clients by sales amount from Fact_Sales."""
        top_n = self._extract_top_n(question) or 10
        return f"""
SELECT TOP {top_n}
    s.[Item No_],
    i.[Description] AS [Produit],
    SUM(s.[Sales Amount (Actual)]) AS [Montant Ventes],
    SUM(ABS(s.[Valued Quantity])) AS [Quantite Vendue]
FROM [dbo].[Fact_Sales] s
LEFT JOIN [dbo].[D_item] i ON s.[Item No_] = i.[No_]
WHERE s.[Sales Amount (Actual)] > 0
GROUP BY s.[Item No_], i.[Description]
ORDER BY [Montant Ventes] DESC
        """.strip()

    def _template_purchases(self, question: str) -> str:
        """Top vendors/purchases from Fact_Purshase."""
        top_n = self._extract_top_n(question) or 10
        return f"""
SELECT TOP {top_n}
    p.[Source No_] AS [Vendor No_],
    v.[Name] AS [Fournisseur],
    SUM(p.[Purchase Amount (Actual)]) AS [Montant Achats],
    YEAR(p.[Posting Date]) AS [Annee]
FROM [dbo].[Fact_Purshase] p
LEFT JOIN [dbo].[D_vendor] v ON p.[Source No_] = v.[No_]
WHERE p.[Purchase Amount (Actual)] > 0
GROUP BY p.[Source No_], v.[Name], YEAR(p.[Posting Date])
ORDER BY [Montant Achats] DESC
        """.strip()

    def _template_disbursements(self, question: str) -> str:
        """Disbursements / vendor payments from Fact_VendorPayementDetail."""
        top_n = self._extract_top_n(question) or 10
        return f"""
SELECT TOP {top_n}
    f.[Vendor No_],
    v.[Name] AS [Fournisseur],
    SUM(f.[Amount]) AS [Montant Decaissement],
    COUNT(*) AS [Nb Paiements]
FROM [dbo].[Fact_VendorPayementDetail] f
LEFT JOIN [dbo].[D_vendor] v ON f.[Vendor No_] = v.[No_]
WHERE f.[Amount] > 0
GROUP BY f.[Vendor No_], v.[Name]
ORDER BY [Montant Decaissement] DESC
        """.strip()

    def _template_stock(self, question: str) -> str:
        """Stock / inventory levels from Fact_StockManagement."""
        top_n = self._extract_top_n(question) or 20
        return f"""
SELECT TOP {top_n}
    s.[Item No_],
    i.[Description] AS [Produit],
    s.[Location Code],
    SUM(s.[Quantity]) AS [Stock Total],
    SUM(s.[Remaining Quantity]) AS [Stock Restant]
FROM [dbo].[Fact_StockManagement] s
LEFT JOIN [dbo].[D_item] i ON s.[Item No_] = i.[No_]
GROUP BY s.[Item No_], i.[Description], s.[Location Code]
HAVING SUM(s.[Quantity]) <> 0
ORDER BY [Stock Total] DESC
        """.strip()

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

        # STOCK — highest priority to avoid article/item confusion
        if any(token in normalized for token in ["stock", "inventaire", "inventory", "rupture"]):
            return self._template_stock(normalized)

        # DECAISSEMENT — before CA/vendor patterns
        if any(token in normalized for token in ["decaissement", "decaissements", "cash out", "sortie caisse"]):
            return self._template_disbursements(normalized)

        # SALES DETAIL by product — before top_customers/top_products patterns
        if any(token in normalized for token in ["vente", "ventes"]) and any(
            token in normalized for token in ["produit", "article", "item", "top", "detail", "liste"]
        ):
            return self._template_sales_detail(normalized)

        # ACHATS — before fournisseur/vendor patterns
        if any(token in normalized for token in ["achat", "achats"]) and not any(
            token in normalized for token in ["retard", "impaye", "overdue"]
        ):
            return self._template_purchases(normalized)

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

        # YEAR COMPARISON - must come BEFORE general CA check
        if any(token in normalized for token in ["vs", "versus", "compare"]):
            return self._template_year_comparison(normalized)

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

        # STOCK queries — before item/article checks
        if any(token in normalized for token in ["stock", "inventaire", "inventory", "rupture"]):
            return self._template_stock(normalized)

        # DECAISSEMENT / vendor payments
        if any(token in normalized for token in ["decaissement", "decaissements", "paiement fournisseur", "vendor payment", "cash out", "sortie caisse"]):
            return self._template_disbursements(normalized)

        # ACHAT / purchases (distinct from fournisseur queries)
        if any(token in normalized for token in ["achat", "achats", "purchase", "purchases"]):
            if not any(token in normalized for token in ["retard", "impaye", "overdue"]):
                return self._template_purchases(normalized)

        # VENTES détaillées par produit — before top_products
        if any(token in normalized for token in ["vente", "ventes"]):
            if any(token in normalized for token in ["produit", "article", "item", "top", "detail", "liste"]):
                return self._template_sales_detail(normalized)

        if any(token in normalized for token in ["produit", "product", "article", "item"]) and any(
            token in normalized for token in ["top", "plus vendu", "vendu", "best", "populaire", "rentable", "profitable", "marge", "profit"]
        ):
            return self._template_top_products(normalized)

        if any(token in normalized for token in ["item", "article", "location", "warehouse", "store"]):
            return self._template_item_locations(normalized)

        if any(token in normalized for token in ["fournisseur", "vendor", "supplier"]):
            if any(token in normalized for token in ["retard", "impaye", "overdue", "late"]):
                return self._template_vendor_overdue(normalized)
            return self._template_top_vendors(normalized)

        if any(token in normalized for token in ["vendeur", "commercial", "salesperson", "salesrep", "representant"]):
            return self._template_top_salespeople(normalized)

        if any(token in normalized for token in ["paiement", "payment", "encaissement", "recouvrement", "recu", "credit"]):
            return self._template_payments_received(normalized)

        if any(token in normalized for token in ["balance", "solde", "encours"]):
            return self._template_customer_balance(normalized)

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
