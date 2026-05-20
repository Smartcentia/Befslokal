
import os
import sys
import psycopg2
from dotenv import load_dotenv
import uuid

# Load environment variables from backend .env
from pathlib import Path
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

DB_URL = os.getenv('DATABASE_URL')
# Fallback to reading file directly if dotenv fails (sometimes due to format)
if not DB_URL and os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                DB_URL = line.strip().split('=', 1)[1].strip('"\'')
                print("Loaded DATABASE_URL manually from .env")

PROPERTY_ID = '022fa3c0-9c3a-431c-a239-6dbf5d8f31c8'

def check_property_data():
    if not DB_URL:
        print("Error: DATABASE_URL not found in environment")
        return

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        print(f"Checking database for Property ID: {PROPERTY_ID}")

        # 1. Check if property exists in properties table (if table exists)
        try:
            cur.execute("SELECT count(*) FROM properties WHERE property_id = %s", (PROPERTY_ID,))
            count = cur.fetchone()[0]
            print(f"Property found in 'properties' table: {count > 0}")
        except Exception as e:
            print(f"Could not query properties table: {e}")
            conn.rollback()

        # 2. Check GL Transactions
        try:
            cur.execute("SELECT count(*) FROM gl_transactions WHERE property_id = %s", (PROPERTY_ID,))
            count = cur.fetchone()[0]
            print(f"GL Transactions count: {count}")
            
            if count > 0:
                cur.execute("SELECT * FROM gl_transactions WHERE property_id = %s LIMIT 5", (PROPERTY_ID,))
                rows = cur.fetchall()
                print("First 5 transactions:")
                for row in rows:
                    print(row)
        except Exception as e:
            print(f"Could not query gl_transactions table: {e}")
            conn.rollback()

        # 3. Check Contracts
        try:
            # Need to match via ID or some link. The CSVs implied a link via address, but let's check contract table for any reference or if unit_id matches property_id
            # Also check if there is a contract with this property_id as unit_id?
            cur.execute("SELECT count(*) FROM contracts WHERE unit_id = %s", (PROPERTY_ID,))
            count = cur.fetchone()[0]
            print(f"Contracts found with unit_id = property_id: {count}")
        except Exception as e:
            print(f"Could not query contracts table: {e}")
            conn.rollback()
            
        conn.close()

    except Exception as e:
        print(f"Database connection failed: {e}")

if __name__ == "__main__":
    check_property_data()
