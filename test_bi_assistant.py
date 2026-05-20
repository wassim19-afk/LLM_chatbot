"""
Test Business Intelligence Assistant
Demonstrates BI query parsing and Power BI link generation
"""

from services.bi_assistant import get_bi_assistant

def test_bi_assistant():
    """Test BI Assistant with various queries"""
    
    bi = get_bi_assistant()
    
    test_cases = [
        "ca 2024",
        "ca janvier 2025 SAPEC",
        "encaissement février 2023 PEM",
        "chiffre d'affaires 2024",
        "achat mars 2025",
        "revenue january 2024",
        "cash in april 2023 PEM",
        "decaissement mai 2024 SAPEC",
    ]
    
    print("=" * 80)
    print("BUSINESS INTELLIGENCE ASSISTANT TEST")
    print("=" * 80)
    
    for question in test_cases:
        print(f"\n📝 Query: {question}")
        print("-" * 80)
        
        # Parse query
        parsed = bi.parse_query(question)
        print(f"  KPI Type: {parsed['kpi_type'].value}")
        print(f"  Year: {parsed['year']}")
        print(f"  Month: {parsed['month']}")
        print(f"  Company: {parsed['company']}")
        print(f"  Filters: {parsed['filters'] if parsed['filters'] else 'None'}")
        
        # Process question and get response
        response, link = bi.process_bi_question(question)
        print(f"\n✅ RESPONSE:")
        print(f"  {response}")
        print(f"\n🔗 DASHBOARD:")
        print(f"  {link}")
    
    print("\n" + "=" * 80)
    print("IS_BI_QUESTION TESTS")
    print("=" * 80)
    
    test_questions = [
        ("ca 2024", True),
        ("top 10 clients", False),
        ("montant par mois", False),
        ("encaissement janvier", True),
        ("revenue for PEM", True),
        ("Can you list the customers?", False),
        ("quel est le CA du mois de janvier", True),
    ]
    
    for question, expected in test_questions:
        result = bi.is_bi_question(question)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{question}' → {result} (expected: {expected})")


def test_filter_extraction():
    """Test individual filter extraction"""
    
    bi = get_bi_assistant()
    
    print("\n" + "=" * 80)
    print("FILTER EXTRACTION DETAILED TESTS")
    print("=" * 80)
    
    # Year extraction
    print("\n📅 YEAR EXTRACTION:")
    year_tests = [
        ("2024", 2024),
        ("ca 2025", 2025),
        ("janvier 2023", 2023),
        ("from 2020 to 2024", 2024),  # Returns last year
    ]
    
    for question, expected in year_tests:
        result = bi._extract_year(question.lower())
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{question}' → {result} (expected: {expected})")
    
    # Month extraction
    print("\n📆 MONTH EXTRACTION:")
    month_tests = [
        ("janvier", 1),
        ("février 2025", 2),
        ("mars", 3),
        ("avril", 4),
        ("mai", 5),
        ("juin", 6),
        ("juillet", 7),
        ("août", 8),
        ("septembre", 9),
        ("octobre", 10),
        ("novembre", 11),
        ("décembre", 12),
        ("janv", 1),
        ("mars", 3),
    ]
    
    for question, expected in month_tests:
        result = bi._extract_month(question.lower())
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{question}' → {result} (expected: {expected})")
    
    # Company extraction
    print("\n🏢 COMPANY EXTRACTION:")
    company_tests = [
        ("PEM", "PEM"),
        ("pem", "PEM"),
        ("SAPEC", "SAPEC"),
        ("sapec", "SAPEC"),
        ("ca janvier PEM", "PEM"),
        ("encaissement SAPEC", "SAPEC"),
        ("aucune entreprise", None),
    ]
    
    for question, expected in company_tests:
        result = bi._extract_company(question.lower())
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{question}' → {result} (expected: {expected})")


if __name__ == "__main__":
    test_bi_assistant()
    test_filter_extraction()
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 80)
