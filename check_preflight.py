import requests
import json

try:
    resp = requests.get('http://localhost:8000/api/preflight')
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
