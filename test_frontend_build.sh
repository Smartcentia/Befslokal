#!/bin/bash
# Test at frontend kan bygge uten feil
# Kjør dette før commit og deploy

set -e  # Exit on error

echo "=========================================="
echo "🧪 Tester frontend build..."
echo "=========================================="
echo ""

cd "$(dirname "$0")/frontend" || exit 1

# Sjekk at vi er i frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ package.json ikke funnet. Er du i frontend directory?"
    exit 1
fi

echo "📦 Installerer dependencies..."
npm install --silent

echo ""
echo "🔨 Bygger frontend..."
npm run build

echo ""
echo "✅ Frontend build vellykket!"
echo ""

# Sjekk at build output eksisterer
if [ ! -d ".next" ]; then
    echo "❌ .next directory ikke funnet etter build"
    exit 1
fi

echo "✅ Alle frontend tester passerte!"
exit 0
