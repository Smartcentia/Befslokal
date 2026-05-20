import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
# Ensure sslmode is set
if "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

try:
    conn = psycopg2.connect(DATABASE_URL)
    print("Successfully connected to database!")
    
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM properties")
    print(f"Property count: {cur.fetchone()[0]}")
    
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
