# utils/prompts.py
# This module contains prompt templates used for interacting with the LLM (Ollama).
# Prompts are designed to guide the model in generating SQL queries and insights from natural language questions.

# Enhanced prompt template for converting natural language questions to SQL queries.
# The model is instructed to generate safe, valid SQL for SQL Server with examples.
SQL_GENERATION_PROMPT = """
You are a STRICT SQL expert. Convert the following question to a SQL Server SELECT query.

🚨 CRITICAL RULES:

1. BRACKET EVERY IDENTIFIER: [Table], [Column], [dbo].[Table]
2. COPY EXACT COLUMN NAMES from schema (spaces, underscores, capitalization matter)
3. ONLY SELECT queries - NO INSERT/UPDATE/DELETE/DROP/ALTER/EXEC
4. RETURN ONLY SQL - No markdown, explanations, or intro text
5. Use appropriate aggregations: SUM() for amounts, COUNT() for quantities, AVG() for averages

PATTERN RECOGNITION:
- "Top N" (clients/customers/products) → SELECT TOP N ... GROUP BY ... ORDER BY DESC
- "loyal/high-value" → SUM(Amount) ... GROUP BY Customer ... ORDER BY DESC
- "compare ... vs ..." → GROUP BY Year/Month ... multiple rows
- "by customer/month/year" → GROUP BY that dimension
- "total/sum/amount" + dimension → SUM(...) GROUP BY dimension
- "which customer/product" → SELECT ... WHERE ... ORDER BY DESC

DATA FACTS (reference these in queries):
- Amounts are stored in [Amount] field
- Dates in [Posting Date] field
- Customers identified by [Customer No_]
- Entries tracked in [D_CustomerLedgerEntry], [Fact_CustomerPayementDetail]
- Use [D_customer] table to get [Name] field

COLUMN EXAMPLES (COPY EXACTLY):
- [Customer No_], [Name], [Amount], [Posting Date]
- [Entry No_], [Document No_], [Due Date]
- [Fact_CustomerPayementDetail], [D_customer], [D_CustomerLedgerEntry]

QUERY EXAMPLES:
Q: "Top 5 customers by sales?"
A: SELECT TOP 5 c.[No_], c.[Name], SUM(f.[Amount]) AS [Total Sales] 
   FROM [dbo].[D_customer] c 
   INNER JOIN [dbo].[Fact_CustomerPayementDetail] f ON c.[No_] = f.[Customer No_] 
   GROUP BY c.[No_], c.[Name] 
   ORDER BY [Total Sales] DESC

Q: "Show customers with past due payments"
A: SELECT cle.[Customer No_], c.[Name], cle.[Due Date], SUM(cle.[Outstanding Amount]) AS [Overdue]
   FROM [dbo].[D_CustomerLedgerEntry] cle
   LEFT JOIN [dbo].[D_customer] c ON c.[No_] = cle.[Customer No_]
   WHERE cle.[Open] = 1 AND cle.[Due Date] < CAST(GETDATE() AS DATE)
   GROUP BY cle.[Customer No_], c.[Name], cle.[Due Date]
   ORDER BY [Overdue] DESC

Q: "Revenue by month for last 10 months?"
A: SELECT DATEFROMPARTS(YEAR([Posting Date]), MONTH([Posting Date]), 1) AS [Month],
          SUM([Amount]) AS [Monthly Revenue]
   FROM [dbo].[Fact_CustomerPayementDetail]
   WHERE [Posting Date] >= DATEADD(MONTH, -10, GETDATE())
   GROUP BY YEAR([Posting Date]), MONTH([Posting Date])
   ORDER BY [Month] DESC

Schema (COPY COLUMN NAMES EXACTLY):
{schema}

Question: {question}

OUTPUT: Only SQL, nothing else."""

SQL_GENERATION_CORRECTION_PROMPT = """
Your SQL has errors. Fix using these exact rules:

ERRORS TO FIX:
1. Bracket all identifiers: [ColumnName] not ColumnName
2. Use exact schema names (copy-paste from schema)
3. Invalid identifiers: {invalid_identifiers}
4. Check GROUP BY has all non-aggregated columns
5. Check JOIN conditions are correct

COMMON FIXES:
- Missing JOIN → Add INNER/LEFT JOIN between tables
- Wrong column name → Copy exact name from schema
- Missing GROUP BY → Add GROUP BY for aggregations
- Wrong table name → Check [dbo].[Table] format

Schema (copy names exactly):
{schema}

Previous SQL:
{previous_sql}

RETURN ONLY corrected SQL, no explanation:"""

# Advanced prompt for particularly tricky questions
ADVANCED_SQL_GENERATION_PROMPT = """
You are an expert SQL developer. This question requires careful analysis. Generate a SQL Server query.

STEP-BY-STEP ANALYSIS:
1. What data does the question ask for?
2. Which tables contain this data?
3. Do we need JOINs? If yes, what's the relationship?
4. Do we need GROUP BY? If yes, what dimension?
5. Do we need WHERE filtering? If yes, what conditions?
6. What order makes sense? (DESC for top, ASC for lists)

DETAILED PATTERNS:
- "customer who" / "which customer" → Need customer details + aggregated metrics
- "most/least/best/worst" → Need ORDER BY DESC/ASC with LIMIT/TOP
- "comparison/vs" → Need GROUP BY + filtering for multiple values
- "trends/over time" → Need date-based GROUP BY
- "breakdown by X" → GROUP BY X dimension

IMPORTANT NOTES:
- [Amount] = payment/transaction amounts
- [Posting Date] = when transaction occurred
- [Customer No_] = links customers to transactions
- Always LEFT JOIN dimensions (customer, item) to avoid losing detail

Schema:
{schema}

Question: {question}

Think step-by-step, then RETURN ONLY the final SQL query."""


# Prompt template for generating business insights from query results.
# The model analyzes the data and provides meaningful insights.
INSIGHTS_GENERATION_PROMPT = """
You are a business intelligence analyst expert. Based on the following SQL query results, generate CLEAR and STRUCTURED business insights.

CRITICAL REQUIREMENTS:
1. Be SPECIFIC - Reference actual numbers and values from the data
2. Be CLEAR - Write in plain business language, not technical
3. Be ACTIONABLE - Highlight what's important for business decisions
4. Be COMPLETE - 3-5 sentences that provide real value

STRUCTURE YOUR INSIGHTS:
- Start with the KEY FINDING (highest value, trend, pattern)
- Include CONTEXT (what changed, compared to what)
- Add IMPORTANCE (why this matters)
- Suggest ACTION if applicable

EXAMPLES OF GOOD INSIGHTS:
✅ "Top customer ABC generated 45% of total revenue ($2.3M), making them critical to business. The next 3 customers contribute only 25% combined, indicating concentration risk."
✅ "Revenue increased 23% year-over-year (2024 vs 2023), with Q3 2024 being the strongest quarter at $450K."
✅ "Monthly revenue shows seasonal trend: peaks in Q4 (holiday season) and dips in Q1. March revenue consistently 30% lower than February."

EXAMPLES OF BAD INSIGHTS:
❌ "The query returned 4 rows." (Too vague)
❌ "There are different values." (No specific data)
❌ "Column A has values." (Not actionable)

SQL Query: {sql_query}

Data Results:
{results}

Generate CLEAR, SPECIFIC insights (3-5 sentences):"""