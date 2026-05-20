#!/bin/bash

# Script to restore database schema and seed data
# Usage: ./restore_db.sh

set -e

echo "🚀 Starting Database Restoration..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found in current directory!"
    echo "    Please make sure you are in the 'backend' directory and have a .env file."
    exit 1
fi

echo "📋 Step 1: Running Database Migrations (Alembic)..."
# Try using python module approach to avoid path issues
python3 -m alembic upgrade head

echo "📋 Step 2: Importing Real Property Data (Oslo)..."
python3 scripts/import_oslo.py

echo "📋 Step 3: Seeding User Hierarchy and Contracts..."
python3 app/db/seed.py

echo "📋 Step 4: Verifying Data..."
python3 scripts/verify_admin.py

echo ""
echo "✅ Database restoration complete!"
echo "   You can now try to log in to the frontend."
