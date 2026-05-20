from data.db_connection import execute_query

measures = [
    "[Sales Amount (Actual)]",
    "[Sales Amt_ Incl_ VAT (Actual)]",
]

for measure in measures:
    print(f"\nMeasure: {measure}\n" + "=" * 80)
    for agg_name, agg_expr in [("SUM", f"SUM({measure})"), ("SUM_ABS", f"SUM(ABS({measure}))")]:
        sql = f"""
        SELECT
            YEAR([Posting Date]) AS [year],
            [companyName],
            ISNULL({agg_expr}, 0) AS total
        FROM [dbo].[Fact_Sales]
        WHERE YEAR([Posting Date]) BETWEEN 2023 AND 2026
        GROUP BY YEAR([Posting Date]), [companyName]
        ORDER BY [year], [companyName]
        """
        rows = execute_query(sql)
        print(f"\n{agg_name}:")
        for row in rows:
            print(f"{row['year']} | {row['companyName']:5} -> {float(row['total'])/1e9:,.2f} bnF CFA")
