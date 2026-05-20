from data.db_connection import execute_query

queries = {
    "By company (2024)": """
        SELECT TOP 20 [companyName], SUM(ABS([Sales Amount (Actual)])) AS total
        FROM [dbo].[Fact_Sales]
        WHERE YEAR([Posting Date]) = 2024
        GROUP BY [companyName]
        ORDER BY total DESC
    """,
    "By source system (2024)": """
        SELECT TOP 20 [SourceSystem], SUM(ABS([Sales Amount (Actual)])) AS total
        FROM [dbo].[Fact_Sales]
        WHERE YEAR([Posting Date]) = 2024
        GROUP BY [SourceSystem]
        ORDER BY total DESC
    """,
    "By instance (2024)": """
        SELECT TOP 20 [Instance], SUM(ABS([Sales Amount (Actual)])) AS total
        FROM [dbo].[Fact_Sales]
        WHERE YEAR([Posting Date]) = 2024
        GROUP BY [Instance]
        ORDER BY total DESC
    """,
}

for title, sql in queries.items():
    print(f"\n{title}\n" + "=" * 80)
    rows = execute_query(sql)
    for row in rows:
        key = list(row.keys())[0]
        total = float(row["total"] or 0)
        print(f"{str(row[key]):20} -> {total/1e9:,.2f} bnF CFA")
