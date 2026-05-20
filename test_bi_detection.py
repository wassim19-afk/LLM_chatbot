from services.bi_assistant import get_bi_assistant

bi = get_bi_assistant()

tests = [
    ('ca 2024', True),
    ('CA par mois', False),
    ('Quel est mon CA par mois', False),
    ('CA janvier 2025 SAPEC', True),
    ('top 10 clients', False),
    ('encaissement février 2023 PEM', True),
    ('répartition CA par région', False),
    ('tendance CA', False),
    ('CA 2024', True),
]

print('\n🔍 BI Question Detection Tests:')
print('='*60)
for q, expected in tests:
    result = bi.is_bi_question(q)
    status = '✅' if result == expected else '❌'
    print(f'{status} "{q}"')
    print(f'   → Result: {result} | Expected: {expected}\n')
