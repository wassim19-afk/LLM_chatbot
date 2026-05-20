import requests
import json

API_URL = "http://localhost:8000/api/chat"

test_queries = [
    ("ca 2024", "Revenue 2024"),
    ("ca 2025", "Revenue 2025"),
    ("ca janvier 2024", "Revenue Jan 2024"),
    ("ca janvier 2024 PEM", "Revenue Jan 2024 PEM"),
    ("ca janvier 2024 SAPEC", "Revenue Jan 2024 SAPEC"),
    ("encaissement février 2024", "Cash In Feb 2024"),
    ("achat mars 2024", "Purchase Mar 2024"),
]

print('\n📊 DATABASE KPI VALUES:')
print('='*80)

for question, description in test_queries:
    try:
        payload = {"question": question, "session_id": "db_test", "model": "mistral"}
        response = requests.post(API_URL, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            insight = data.get("insight", "").split("\n")[0]
            print(f'{description:25} → {insight}')
        else:
            print(f'{description:25} → ERROR {response.status_code}')
    except Exception as e:
        print(f'{description:25} → ERROR: {str(e)[:50]}')

print('='*80)
