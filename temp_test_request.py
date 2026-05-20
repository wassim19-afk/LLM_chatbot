import requests
url = 'http://localhost:8000/api/chat'
payload = {'question': "combien le chiffre d'affaire de l'annee 2025?"}
try:
    r = requests.post(url, json=payload)
    print('status', r.status_code)
    print('text', r.text)
except Exception as e:
    print('error', str(e))
