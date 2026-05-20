import asyncio
from logging.config import fileConfig
import sys
import os
import ssl
sys.path.append(os.getcwd())

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config, create_async_engine

from alembic import context
from app.core.config import settings
from app.db.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Overwrite the sqlalchemy.url in the config object
if settings.DATABASE_URL:
    config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))
else:
    print("WARNING: DATABASE_URL not found in settings. Make sure .env is configured.")

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    # transaction_per_migration=True: hver migrasjon i egen transaksjon – feil i én avbryter ikke hele kjeden, og vi ser tydelig hvilken som feiler
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        transaction_per_migration=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    db_url = config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL
    
    connect_args: dict = {"statement_cache_size": 0}
    # SSL kun for sky-DB (Supabase/Railway), ikke lokal Postgres
    if db_url and "localhost" not in db_url and "127.0.0.1" not in db_url:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_context
    
    connectable = create_async_engine(
        db_url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
