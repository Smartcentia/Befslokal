import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

print("Attempting to import app.main...")
try:
    from app.main import app
    print("SUCCESS: app.main imported successfully.")
except Exception as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
