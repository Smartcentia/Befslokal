#!/bin/bash

# 🔧 Automatisk Setup Script for BEFS
# Setter opp environment variables og trigger redeploy automatisk

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 BEFS Auto Setup Script${NC}"
echo "================================"
echo ""

# Configuration
VERCEL_PROJECT="knowme-frontend"
RAILWAY_SERVICE="BEFS1"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}⚠️  Vercel CLI ikke installert. Installerer...${NC}"
    npm install -g vercel
fi

# Check if user is logged in to Vercel
if ! vercel whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Ikke innlogget i Vercel. Logger inn...${NC}"
    vercel login
fi

echo -e "${GREEN}✅ Vercel CLI klar${NC}"
echo ""

# Generate or use existing secret
if [ -z "$NEXTAUTH_SECRET" ]; then
    echo -e "${YELLOW}Genererer ny NEXTAUTH_SECRET...${NC}"
    NEXTAUTH_SECRET=$(openssl rand -base64 32)
    echo -e "${GREEN}✅ Generert: ${NEXTAUTH_SECRET}${NC}"
else
    echo -e "${GREEN}✅ Bruker eksisterende NEXTAUTH_SECRET${NC}"
fi

echo ""
echo -e "${YELLOW}📋 Steg 1: Sett NEXTAUTH_SECRET i Vercel${NC}"
echo "----------------------------------------"

# Set NEXTAUTH_SECRET in Vercel
vercel env add NEXTAUTH_SECRET production <<< "$NEXTAUTH_SECRET" || {
    echo -e "${YELLOW}⚠️  Prøver å oppdatere eksisterende...${NC}"
    vercel env rm NEXTAUTH_SECRET production --yes
    vercel env add NEXTAUTH_SECRET production <<< "$NEXTAUTH_SECRET"
}

# Also add for preview and development
vercel env add NEXTAUTH_SECRET preview <<< "$NEXTAUTH_SECRET" 2>/dev/null || true
vercel env add NEXTAUTH_SECRET development <<< "$NEXTAUTH_SECRET" 2>/dev/null || true

echo -e "${GREEN}✅ NEXTAUTH_SECRET satt i Vercel${NC}"
echo ""

echo -e "${YELLOW}📋 Steg 2: Sett SECRET_KEY i Railway${NC}"
echo "----------------------------------------"
echo -e "${YELLOW}⚠️  Railway CLI ikke tilgjengelig.${NC}"
echo -e "${YELLOW}   Gå til Railway Dashboard og sett SECRET_KEY manuelt:${NC}"
echo -e "${GREEN}   Verdi: ${NEXTAUTH_SECRET}${NC}"
echo ""
read -p "Trykk Enter når SECRET_KEY er satt i Railway..."

echo ""
echo -e "${YELLOW}📋 Steg 3: Trigger Redeploy${NC}"
echo "----------------------------------------"

# Trigger redeploy by creating empty commit or using Vercel API
echo -e "${YELLOW}Triggerer redeploy i Vercel...${NC}"

# Option 1: Use Vercel API to trigger redeploy
if [ -n "$VERCEL_TOKEN" ]; then
    echo -e "${GREEN}✅ Bruker Vercel API token${NC}"
    # Get project ID
    PROJECT_ID=$(vercel ls --json | jq -r ".[] | select(.name==\"$VERCEL_PROJECT\") | .id" | head -1)
    
    if [ -n "$PROJECT_ID" ]; then
        # Trigger redeploy
        curl -X POST "https://api.vercel.com/v13/deployments?projectId=$PROJECT_ID" \
            -H "Authorization: Bearer $VERCEL_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"name":"'$VERCEL_PROJECT'","gitSource":{"type":"github","repo":"Smartcentia/BEFS1","ref":"main"}}' \
            &> /dev/null && echo -e "${GREEN}✅ Redeploy trigget via API${NC}" || echo -e "${YELLOW}⚠️  API redeploy feilet, bruk git push${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  VERCEL_TOKEN ikke satt. Bruker git push metode...${NC}"
    echo -e "${YELLOW}   Kjør: git commit --allow-empty -m 'trigger redeploy' && git push${NC}"
fi

echo ""
echo -e "${GREEN}✅ Setup ferdig!${NC}"
echo ""
echo -e "${YELLOW}📋 Neste Steg:${NC}"
echo "1. Vent til deploy er ferdig (2-3 minutter)"
echo "2. Clear cookies i browser"
echo "3. Re-login"
echo "4. Test med: fetch('/api/auth/session').then(r => r.json()).then(console.log)"
echo ""
