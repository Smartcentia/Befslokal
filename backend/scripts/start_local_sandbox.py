import sys
import os
import uvicorn

# Add backend directory to sys.path to ensure imports work if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

# Import the server app from ai_lab.runtime
from app.ai_lab.runtime.server import app

def main():
    print("🚀 Starting Local AI Sandbox on http://localhost:5050")
    print("⚠️  WARNING: This enables arbitrary code execution on your machine.")
    print("⚠️  Only use this for development and with trusted code.")
    
    # Run uvicorn on port 5050 to avoid conflict with main backend (8000) or frontend (3000)
    uvicorn.run(app, host="127.0.0.1", port=5050)

if __name__ == "__main__":
    main()
