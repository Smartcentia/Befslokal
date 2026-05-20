from fastapi.testclient import TestClient
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from app.main import app

client = TestClient(app)

def test_lab_api():
    print("🧪 Testing AI Lab API Endpoint...")
    
    # 1. Simple Status Check
    resp = client.get("/api/v1/lab/status")
    print(f"Status Endpoint: {resp.status_code} - {resp.json()}")
    assert resp.status_code == 200
    
    # 2. Chat Request (Password Gen)
    # This might take time as it calls OpenAI + Sandbox
    payload = {"query": "I need a random string of 15 characters."}
    print(f"🚀 Sending Chat Request: {payload}")
    
    resp = client.post("/api/v1/lab/chat", json=payload, timeout=60.0)
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Success! Response:\n{data}")
        print(f"Status: {data.get('status')}")
        print(f"Message: {data.get('message')}")
        
        # Verify Logs exist
        logs = data.get("logs", [])
        print(f"Logs captured: {len(logs)} lines.")
    else:
        print(f"❌ Failed: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    test_lab_api()
