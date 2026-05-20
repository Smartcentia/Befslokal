#!/usr/bin/env python3
"""Start backend server."""
import sys
import os
from dotenv import load_dotenv

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Load environment variables
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

# Now import and run
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[backend_dir]
    )
