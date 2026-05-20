
import os
import sys
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

# Add backend directory to path to find settings if needed, though we probably just need env
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Try to load from settings if env not set
    try:
        from app.core.config import settings
        DATABASE_URL = str(settings.DATABASE_URL)
    except ImportError:
        print("Could not load DATABASE_URL from env or settings.")
        sys.exit(1)

print(f"Checking database...")

try:
    # Fix for sslmode error with certain drivers
    if "sslmode" in DATABASE_URL:
        # For sync engine (psycopg2/default), we might need to adjust or rely on libpq
        # But often 'sslmode=require' in URL is fine for psycopg2, but not for others if args passed weirdly
        pass
    
    # Simpler approach: use text() to check tables if inspector fails, or just try to select
    engine = create_engine(DATABASE_URL.replace("+asyncpg", "")) # Ensure we use sync driver
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    auth_tables = ['nextauth_users', 'nextauth_accounts', 'nextauth_sessions', 'nextauth_verification_tokens']
    missing = [t for t in auth_tables if t not in tables]
    
    if missing:
        print(f"❌ Missing Auth Tables: {', '.join(missing)}")
        print("This confirms that Prisma migrations for NextAuth have NOT been applied.")
    else:
        print("✅ All NextAuth tables are present.")
        
except Exception as e:
    print(f"Error connecting to DB: {e}")
