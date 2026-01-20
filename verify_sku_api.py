import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def test_api():
    print("Testing SKU API...")
    
    # 1. Add SKU
    print("\n1. Testing Manual Add...")
    try:
        resp = requests.post(f"{BASE_URL}/api/skus", json={
            "name": "AutoTest Item",
            "sku": "AUTO_SKU_001",
            "rating": 4.5,
            "review_count": 100
        })
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # 2. Upload CSV
    print("\n2. Testing CSV Upload...")
    csv_content = """name,base_sku,sku,link,rating,review_count
CSV_Item_1,BASE_A,CSV_SKU_01,http://example.com/1,4.0,10
CSV_Item_2,BASE_A,CSV_SKU_02,http://example.com/2,3.5,5
"""
    files = {'file': ('test_upload.csv', csv_content)}
    resp = requests.post(f"{BASE_URL}/api/skus/upload", files=files)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")

    # 3. Get SKUs
    print("\n3. Verifying List...")
    resp = requests.get(f"{BASE_URL}/api/skus")
    skus = resp.json().get('skus', [])
    print(f"Total SKUs found: {len(skus)}")
    for s in skus:
        if 'AUTO' in s['sku'] or 'CSV' in s['sku']:
            print(f" - Found: {s['name']} ({s['sku']})")

if __name__ == "__main__":
    # Wait a bit for server to potentially start if user runs this manually
    test_api()
