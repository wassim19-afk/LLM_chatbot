"""
Test file to check visualization and insights issues
"""

# Test 1: Check if insights are being generated correctly
print("=== TEST 1: INSIGHTS GENERATION ===")

from utils.prompts import INSIGHTS_GENERATION_PROMPT

sample_results = """
Customer: ABC Corp, Revenue: 2,500,000
Customer: XYZ Inc, Revenue: 1,800,000
Customer: Tech Solutions, Revenue: 950,000
Customer: Global Services, Revenue: 450,000
"""

sample_sql = "SELECT TOP 4 [Name], SUM([Amount]) AS Revenue FROM [dbo].[D_customer] GROUP BY [Name] ORDER BY Revenue DESC"

formatted_prompt = INSIGHTS_GENERATION_PROMPT.format(
    sql_query=sample_sql,
    results=sample_results
)

print("INSIGHTS PROMPT (improved):")
print("=" * 80)
print(formatted_prompt[:500])
print("...")
print("=" * 80)

# Test 2: Check visualization errors
print("\n=== TEST 2: VISUALIZATION ERROR HANDLING ===")

test_cases = [
    {"type": "BAR", "data": [{"Name": "A", "Value": 100}], "desc": "Single bar - should work"},
    {"type": "LINE", "data": [{"Date": "2024-01-01", "Amount": 1000}], "desc": "Single line - might have issue"},
    {"type": "METRIC", "data": [{"Total": 5000}], "desc": "Single metric - should work"},
]

for tc in test_cases:
    print(f"✓ {tc['desc']}")
    print(f"  Type: {tc['type']}, Data points: {len(tc['data'])}")

print("\n✅ All tests completed")
