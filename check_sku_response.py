import requests
import json

BASE_URL = "http://127.0.0.1:5000"

print("Checking SKU API Response Structure...")
resp = requests.get(f"{BASE_URL}/api/skus")
print(f"\nStatus Code: {resp.status_code}")
print(f"\nResponse JSON:")

print(json.dumps(resp.json(), indent=2))
