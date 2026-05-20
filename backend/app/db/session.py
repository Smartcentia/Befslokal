from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings
import ssl

# For async operations (FastAPI default)
database_url = settings.DATABASE_URL
if not database_url:
    raise ValueError("DATABASE_URL is not set in environment!")


# SSL: disable cert verification (works for both Railway internal Postgres
# and Supabase which uses a self-signed cert)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# For Railway internal .railway.internal URLs, no SSL needed
_ssl: object = ssl_context
if database_url and ".railway.internal" in database_url:
    _ssl = False  # Railway internal network is secure without SSL

connect_args = {
    "server_settings": {
        "application_name": "knowme-backend"
    },
    "command_timeout": 60,
    "timeout": 30,
    "ssl": _ssl,
    "statement_cache_size": 0,  # Required for PgBouncer transaction pooling (Supabase)
}

# Connection pool settings optimized for serverless Postgres
# Database may suspend after inactivity - pre_ping handles wakeup gracefully
engine = create_async_engine(
    database_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,           # CRITICAL: Test connections before using (handles serverless suspend)
    pool_size=3,                  # Smaller pool for serverless (limit connections)
    max_overflow=7,               # Allow burst to 10 total connections
    pool_recycle=3600,            # Recycle connections every hour (conservative)
    pool_timeout=30,              # Wait max 30s for available connection
)
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

# For sync operations (if needed for older dependencies, though we aim for full async)
from sqlalchemy import create_engine
# engine_sync = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
# SessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=engine_sync)
