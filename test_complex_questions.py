import httpx
import json

test_queries = [
    'quel est le CA 2023 VS 2024',
    'total par an',
    'montant par mois',
    'top 10 clients'
]

print('=== TESTING COMPLEX QUESTIONS ===\n')
for q in test_queries:
    try:
        response = httpx.post('http://localhost:8000/api/chat', json={'question': q}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            sql = data['sql_query']
            insight = data['insight']
            rows = len(data['data'])
            print(f'✅ Q: {q}')
            print(f'   SQL: {sql[:80]}...')
            print(f'   Rows returned: {rows}')
            print(f'   Insight: {insight[:100]}...\n')
        else:
            print(f'❌ Q: {q} - Status {response.status_code}\n')
    except Exception as e:
        print(f'❌ Q: {q} - Error: {str(e)}\n')
