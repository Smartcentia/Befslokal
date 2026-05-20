import requests
import json
import sys

# Production URL from deploy.sh
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/validate-credentials"

def test_prod_login():
    print(f"Testing login against: {LOGIN_URL}")
    
    payload = {
        "email": "frankvevle@gmail.com",
        "password": "Sureminer_6533"
    }
    
    try:
        response = requests.post(LOGIN_URL, json=payload, headers={"Content-Type": "application/json"})
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Login SUCCESS on Production Backend!")
            else:
                print("❌ Login FAILED (Logic): Backend returned success=False")
        else:
            print("❌ Login FAILED (HTTP Error)")
            
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    test_prod_login()
