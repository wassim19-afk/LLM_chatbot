#!/usr/bin/env python
"""Test fallback template matching"""

from services.fallback_sql_templates import generate_fallback_sql

questions = [
    "CA 2024?",
    "ca 2023?",
    "2023?",
    "le client qui fait beaucoup d'achat?",
]

for q in questions:
    sql = generate_fallback_sql(q)
    if sql:
        # Show first 100 chars of SQL
        print(f"\nQ: {q}")
        print(f"SQL: {sql[:120]}...")
    else:
        print(f"\nQ: {q}")
        print("SQL: None (no template matched)")
