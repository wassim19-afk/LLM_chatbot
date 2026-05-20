from services.bi_assistant import get_bi_assistant

bi = get_bi_assistant()

test_questions = [
    'ca 2024',
    'ca 2025',
    'ca janvier 2024',
    'ca janvier 2025',
    'ca avril 2025',
    'ca octobre 2025',
    'ca décembre 2025',
    'ca janvier 2025 PEM',
    'ca janvier 2025 SAPEC',
    'ca avril 2024 PEM',
    'ca avril 2024 SAPEC',
    'encaissement février 2025',
    'encaissement février 2025 PEM',
    'achat mars 2024',
    'achat mars 2024 SAPEC',
]

print('\n💰 KPI VALUES - Showing Variance:')
print('='*70)
for q in test_questions:
    parsed = bi.parse_query(q)
    value = bi.get_mock_kpi_value(parsed)
    kpi_type = parsed['kpi_type'].value
    year = parsed.get('year') or '    '
    month = parsed.get('month')
    company = parsed.get('company') or '-'
    
    month_name = {1:'Jan', 2:'Fév', 3:'Mar', 4:'Avr', 5:'Mai', 6:'Juin',
                  7:'Juil', 8:'Aoû', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Déc'}.get(month, '   ')
    
    print(f'{kpi_type:20} {str(year):>4} {month_name} {company:6} → {value:>12,.0f} BnFCFA')
