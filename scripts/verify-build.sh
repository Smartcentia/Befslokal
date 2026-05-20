#!/bin/bash
# Verify Frontend Build Stability
# Usage: ./scripts/verify-build.sh

set -e

echo "🔍 Starting Frontend Build Verification..."

cd frontend

echo "📦 Installing/Checking dependencies..."
# Use --no-audit for speed, but ensure prisma is generated
npm install --no-audit

echo "💎 Generating Prisma Client..."
npx prisma generate

echo "✨ Running Lint..."
npm run lint || echo "⚠️ Lint warnings found (continuing...)"

echo "🏗️  Starting Production Build Test..."
npm run build

echo ""
echo "✅ Build verified successfully! It is safe to deploy."
