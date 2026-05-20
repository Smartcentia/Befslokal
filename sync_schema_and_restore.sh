#!/bin/bash

# Script to sync database schema using Prisma and restore data
# Usage: ./sync_schema_and_restore.sh

set -e

echo "🚀 Starting Database Schema Sync & Restoration..."

# Check if .env exists in backend
if [ ! -f "backend/.env" ]; then
    echo "⚠️  backend/.env file not found!"
    exit 1
fi

echo "📋 Step 1: Syncing Database Schema with Prisma..."
# This will push the schema defined in schema.prisma to the database
# It might warn about data loss if schema changed significantly, which is acceptable here as we are restoring
cd frontend
npx prisma db push --accept-data-loss
cd ..

echo "📋 Step 2: Generating Prisma Client..."
cd frontend
npx prisma generate
cd ..

echo "📋 Step 3: Improving Alembic Migration Status (Fake Apply)..."
# Since Prisma manages the schema now, we might want to skip Alembic or just stamp it
# For now, we assume Alembic is secondary or legacy for schema management,
# BUT the python scripts might rely on Alembic being up to date.
# Let's try to just stamp it to "head" so Alembic doesn't try to create tables again.
cd backend
# We use 'stamp' to tell Alembic "the database is already at this version, don't run migrations"
# This avoids the "table already exists" or "column missing" errors if Prisma did the job.
python3 -m alembic stamp head || echo "⚠️ Alembic stamp failed, proceeding anyway..."
cd ..

echo "📋 Step 4: Importing Real Property Data (Oslo)..."
cd backend
python3 scripts/import_oslo.py
cd ..

echo "📋 Step 5: Seeding User Hierarchy and Contracts..."
cd backend
python3 app/db/seed.py
cd ..

echo "📋 Step 6: Verifying Data..."
cd backend
python3 scripts/verify_admin.py
cd ..

echo ""
echo "✅ Database synchronization and restoration complete!"
echo "   The database schema is now in sync with Prisma, and data has been seeded."
