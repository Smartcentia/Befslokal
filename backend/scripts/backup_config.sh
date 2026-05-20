#!/bin/bash
set -e

# BEFS3 KNOWME - Configuration Backup Script
# Creates sanitized templates of environment files (secrets excluded)

DATE=$(date +%Y%m%d)
BACKUP_DIR="./backups/config"
mkdir -p $BACKUP_DIR

echo "🔄 Starting configuration backup..."
echo "Date: $(date)"

# Backend .env template (exclude sensitive values)
if [ -f "backend/.env" ]; then
    echo "📝 Creating backend .env template..."
    grep -v "PASSWORD\|SECRET\|KEY\|TOKEN\|CREDENTIAL" backend/.env > $BACKUP_DIR/backend_env_template_$DATE.txt
    echo "✅ Backend template created"
else
    echo "⚠️  backend/.env not found"
fi

# Frontend .env.local template (exclude sensitive values)
if [ -f "frontend/.env.local" ]; then
    echo "📝 Creating frontend .env.local template..."
    grep -v "PASSWORD\|SECRET\|KEY\|TOKEN\|CREDENTIAL" frontend/.env.local > $BACKUP_DIR/frontend_env_template_$DATE.txt
    echo "✅ Frontend template created"
else
    echo "⚠️  frontend/.env.local not found"
fi

# docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    echo "📝 Backing up docker-compose.yml..."
    cp docker-compose.yml $BACKUP_DIR/docker-compose_$DATE.yml
    echo "✅ Docker config backed up"
fi

echo ""
echo "✅ Configuration backup completed!"
echo "📂 Location: $BACKUP_DIR"
echo ""
echo "⚠️  IMPORTANT: Actual secrets are NOT included in these backups."
echo "   Store secrets securely in:"
echo "   - Fly.io secrets (flyctl secrets list)"
echo "   - Vercel environment variables"
echo "   - Password manager (1Password, LastPass, etc.)"
echo "   - Encrypted local file (NOT in Git!)"
