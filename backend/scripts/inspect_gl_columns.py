import sys
import os
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

# Load env from backend/.env manually
env_path = os.path.join(os.getcwd(), 'backend/.env')
db_url = None
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                # Remove DATABASE_URL= and optional quotes
                val = line.strip().split("=", 1)[1]
                db_url = val.strip('"').strip("'")
                break

if not db_url:
    print(f"DATABASE_URL not found in {env_path}")
    sys.exit(1)

# Fix asyncpg driver if present, we need sync for this simple script or use async engine
if "+asyncpg" in db_url:
    db_url = db_url.replace("+asyncpg", "")

# Strip query params (e.g. ?sslmode=require)
if "?" in db_url:
    db_url = db_url.split("?")[0]

print(f"Connecting to: {db_url.split('@')[-1]}") # Log host/db only for safety

try:
    engine = create_engine(db_url)
    inspector = inspect(engine)

    print("Columns in gl_transactions:")
    columns = inspector.get_columns('gl_transactions')
    for col in columns:
        print(f"- {col['name']} ({col['type']})")

    # Check row count
    with engine.connect() as conn:
        result = conn.execute(text("SELECT count(*) FROM gl_transactions"))
        count = result.scalar()
        print(f"Row count: {count}")

except Exception as e:
    print(f"Error inspecting DB: {e}")
