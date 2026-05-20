from data.db_connection import execute_query

sql = """
SELECT
    YEAR([Posting Date]) AS [year],
    [companyName],
    SUM(ABS([Sales Amount (Actual)])) AS total
FROM [dbo].[Fact_Sales]
WHERE YEAR([Posting Date]) BETWEEN 2023 AND 2026
GROUP BY YEAR([Posting Date]), [companyName]
ORDER BY [year], [companyName]
"""

rows = execute_query(sql)
print("\nYearly CA by company\n" + "=" * 80)
for row in rows:
    print(f"{row['year']} | {row['companyName']:5} -> {float(row['total'])/1e9:,.2f} bnF CFA")
