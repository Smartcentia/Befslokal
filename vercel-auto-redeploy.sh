#!/bin/bash

# 🚀 Automatisk Redeploy Script for Vercel
# Trigger redeploy når environment variables er endret

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Vercel Auto Redeploy${NC}"
echo "=========================="
echo ""

# Configuration
VERCEL_PROJECT="knowme-frontend"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}❌ Vercel CLI ikke installert.${NC}"
    echo "Installer med: npm install -g vercel"
    exit 1
fi

# Check if logged in
if ! vercel whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Ikke innlogget. Logger inn...${NC}"
    vercel login
fi

echo -e "${GREEN}✅ Vercel CLI klar${NC}"
echo ""

# Method 1: Empty commit (simplest)
echo -e "${YELLOW}Metode 1: Empty commit${NC}"
echo "----------------------------"
echo "Dette vil trigge automatisk redeploy via GitHub/Vercel integration"
echo ""

read -p "Vil du lage en empty commit for å trigge redeploy? (j/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[JjYy]$ ]]; then
    git commit --allow-empty -m "chore: trigger redeploy after env var changes" || {
        echo -e "${RED}❌ Git commit feilet${NC}"
        exit 1
    }
    
    echo -e "${YELLOW}Push til GitHub? (j/n)${NC}"
    read -p "" -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[JjYy]$ ]]; then
        git push origin main || {
            echo -e "${RED}❌ Git push feilet${NC}"
            exit 1
        }
        echo -e "${GREEN}✅ Push ferdig! Vercel vil automatisk deploye.${NC}"
    else
        echo -e "${YELLOW}⚠️  Commit laget lokalt. Push manuelt med: git push${NC}"
    fi
fi

echo ""
echo -e "${YELLOW}Metode 2: Vercel API (krever VERCEL_TOKEN)${NC}"
echo "----------------------------------------"

if [ -z "$VERCEL_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  VERCEL_TOKEN ikke satt.${NC}"
    echo "Sett med: export VERCEL_TOKEN=your_token"
    echo "Hent token fra: https://vercel.com/account/tokens"
else
    echo -e "${GREEN}✅ VERCEL_TOKEN funnet${NC}"
    
    # Get project ID
    PROJECT_ID=$(vercel ls --json 2>/dev/null | grep -o "\"id\":\"[^\"]*\"" | head -1 | cut -d'"' -f4)
    
    if [ -n "$PROJECT_ID" ]; then
        echo -e "${YELLOW}Triggerer redeploy via API...${NC}"
        
        RESPONSE=$(curl -s -X POST "https://api.vercel.com/v13/deployments" \
            -H "Authorization: Bearer $VERCEL_TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"name\": \"$VERCEL_PROJECT\",
                \"project\": \"$PROJECT_ID\"
            }")
        
        if echo "$RESPONSE" | grep -q "id"; then
            echo -e "${GREEN}✅ Redeploy trigget via API!${NC}"
            DEPLOY_ID=$(echo "$RESPONSE" | grep -o "\"id\":\"[^\"]*\"" | head -1 | cut -d'"' -f4)
            echo "Deploy ID: $DEPLOY_ID"
            echo "Sjekk status: https://vercel.com/dashboard"
        else
            echo -e "${RED}❌ API redeploy feilet${NC}"
            echo "Response: $RESPONSE"
        fi
    else
        echo -e "${RED}❌ Kunne ikke finne project ID${NC}"
    fi
fi

echo ""
echo -e "${GREEN}✅ Redeploy trigget!${NC}"
echo ""
echo -e "${YELLOW}📋 Neste Steg:${NC}"
echo "1. Vent 2-3 minutter til deploy er ferdig"
echo "2. Sjekk status: https://vercel.com/dashboard"
echo "3. Clear cookies og re-login"
echo ""
