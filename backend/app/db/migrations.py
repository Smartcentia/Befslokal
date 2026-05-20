import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine

logger = logging.getLogger("DatabaseMigrations")

async def run_migrations():
    """
    Runs ad-hoc database migrations to ensure schema consistency.
    """
    logger.info("Starting ad-hoc database migrations...")
    
    try:
        logger.info("Attempting to acquire engine connection...")
        async with engine.begin() as conn:
            logger.info("Connection acquired. Starting migration checks...")
            # 1. Migrate external_api_data.entity_id from UUID to VARCHAR
            # We check the type first to avoid redundant ALTERS
            check_query = text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'external_api_data' 
                AND column_name = 'entity_id';
            """)
            result = await conn.execute(check_query)
            row = result.fetchone()
            
            if row and row[0].lower() == 'uuid':
                logger.info("Migrating external_api_data.entity_id from UUID to VARCHAR(100)...")
                await conn.execute(text("ALTER TABLE external_api_data ALTER COLUMN entity_id TYPE VARCHAR(100);"))
                logger.info("Migration successful.")
            else:
                logger.info("external_api_data.entity_id is already VARCHAR or table not found. Skipping.")
            
            # 2. Add start_date and end_date to contracts if missing
            for col in ["start_date", "end_date"]:
                check_col_query = text(f"""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'contracts' AND column_name = '{col}';
                """)
                res = await conn.execute(check_col_query)
                if not res.fetchone():
                    logger.info(f"Adding column {col} to contracts table...")
                    await conn.execute(text(f"ALTER TABLE contracts ADD COLUMN {col} DATE;"))
                    logger.info(f"Column {col} added.")
            
            # 3. Create infrastructure_costs table if it doesn't exist
            check_table_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    AND table_name = 'infrastructure_costs'
                );
            """)
            res = await conn.execute(check_table_query)
            if not res.fetchone()[0]:
                logger.info("Creating infrastructure_costs table...")
                await conn.execute(text("""
                    CREATE TABLE infrastructure_costs (
                        id SERIAL PRIMARY KEY,
                        service_name VARCHAR(50) NOT NULL,
                        collection_date TIMESTAMP NOT NULL DEFAULT NOW(),
                        raw_metrics JSONB,
                        estimated_cost_usd DECIMAL(10, 2),
                        active_time_seconds INTEGER,
                        cpu_used_seconds INTEGER,
                        storage_gb DECIMAL(10, 2),
                        bandwidth_gb DECIMAL(10, 2),
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                    CREATE INDEX idx_costs_service_date ON infrastructure_costs(service_name, collection_date);
                    CREATE INDEX idx_costs_collection_date ON infrastructure_costs(collection_date);
                """))
                logger.info("infrastructure_costs table created.")
            else:
                logger.info("infrastructure_costs table already exists. Skipping.")
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # We don't necessarily want to block startup if research migrations fail, 
        # but for this critical one, we log it clearly.
