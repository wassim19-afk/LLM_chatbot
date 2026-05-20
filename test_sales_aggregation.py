from data.db_connection import execute_query

# Test different aggregation approaches
queries = [
    ("All rows SUM", "SELECT ISNULL(SUM([Sales Amount (Actual)]), 0) as total FROM [dbo].[Fact_Sales] WHERE YEAR([Posting Date]) = 2024"),
    
    ("Positive only", "SELECT ISNULL(SUM([Sales Amount (Actual)]), 0) as total FROM [dbo].[Fact_Sales] WHERE YEAR([Posting Date]) = 2024 AND [Positive] = 1"),
    
    ("Absolute value", "SELECT ISNULL(SUM(ABS([Sales Amount (Actual)])), 0) as total FROM [dbo].[Fact_Sales] WHERE YEAR([Posting Date]) = 2024"),
    
    ("Entry Type filter", "SELECT ISNULL(SUM([Sales Amount (Actual)]), 0) as total FROM [dbo].[Fact_Sales] WHERE YEAR([Posting Date]) = 2024 AND [Entry Type] IN (0, 1)"),
    
    ("Invoiced qty", "SELECT ISNULL(SUM([Sales Amount (Actual)]), 0) as total FROM [dbo].[Fact_Sales] WHERE YEAR([Posting Date]) = 2024 AND [Invoiced Quantity] > 0"),
]

print('\n🔍 TESTING DIFFERENT AGGREGATION METHODS:')
print('='*80)

for description, sql in queries:
    try:
        results = execute_query(sql)
        if results and len(results) > 0:
            value = results[0].get('total', 0)
            value_bn = value / 1e9 if value > 1e9 else value / 1e6
            unit = 'bnF' if value > 1e9 else 'MF'
            print(f'{description:30} → {value_bn:>10,.2f} {unit} CFA')
    except Exception as e:
        print(f'{description:30} → ERROR: {str(e)[:50]}')

print('\n' + '='*80)
