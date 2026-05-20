import requests
import sys

BASE_URL = "http://localhost:8000/api/v1/deviations"

def test_stats():
    try:
        response = requests.get(f"{BASE_URL}/stats")
        if response.status_code == 200:
            print("✓ Stats Endpoint OK")
            print(response.json())
        else:
            print(f"✗ Stats Endpoint Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"✗ Connection Failed: {e}")

if __name__ == "__main__":
    test_stats()
