#!/usr/bin/env python3
"""Quick test script for backend"""
import json
import urllib.request
import urllib.error
import sys

try:
    question = "show customers"
    payload = json.dumps({"question": question}).encode('utf-8')
    
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/chat',
        data=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Testing question: '{question}'")
    with urllib.request.urlopen(req, timeout=45) as response:
        result = json.loads(response.read().decode('utf-8'))
        rows = len(result.get('data', []))
        print(f"✓ SUCCESS: {rows} rows returned")
        print(f"  SQL: {result.get('sql_query', '')[:100]}")
        
except urllib.error.URLError as e:
    print(f"✗ URLError: {str(e)[:100]}")
    sys.exit(1)
except TimeoutError as e:
    print(f"✗ TimeoutError: {str(e)[:100]}")
    sys.exit(1)
except Exception as e:
    print(f"✗ {type(e).__name__}: {str(e)[:100]}")
    sys.exit(1)
