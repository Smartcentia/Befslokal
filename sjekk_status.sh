#!/bin/bash
# 🔍 Sjekk Deploy og Environment Status

set -e

# Farger
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}🔍 Status Sjekk - BEFS System${NC}"
echo "=================================="
echo ""

# Backend URLs
RAILWAY_BACKEND="https://striking-insight-production-a21b.up.railway.app"
FRONTEND="https://knowme-frontend-amber.vercel.app"

# 1. Sjekk Backend
echo -e "${BLUE}📊 Backend (BEFS1)${NC}"
echo "----------------------------"
echo "URL: $RAILWAY_BACKEND"
echo ""

HEALTH=$(curl -s --max-time 10 "$RAILWAY_BACKEND/api/v1/health" 2>&1 || echo "Failed")
if echo "$HEALTH" | grep -q "healthy\|degraded"; then
    echo -e "${GREEN}✅ Backend er online${NC}"
    echo "$HEALTH" | jq . 2>/dev/null || echo "$HEALTH"
else
    echo -e "${RED}❌ Backend er ikke tilgjengelig${NC}"
    echo "$HEALTH"
    echo ""
    echo -e "${YELLOW}⚠️  Sjekk Railway Dashboard: https://railway.app${NC}"
fi

echo ""

# (Fly.io legacy sjekk fjernet – vi bruker kun Railway)

# 3. Sjekk Frontend
echo -e "${BLUE}📊 Frontend (Vercel)${NC}"
echo "----------------------------"
echo "URL: $FRONTEND"
echo ""

FRONTEND_STATUS=$(curl -s --max-time 10 -o /dev/null -w "%{http_code}" "$FRONTEND" 2>&1 || echo "Failed")
if [ "$FRONTEND_STATUS" = "200" ] || [ "$FRONTEND_STATUS" = "301" ] || [ "$FRONTEND_STATUS" = "302" ]; then
    echo -e "${GREEN}✅ Frontend er online (HTTP $FRONTEND_STATUS)${NC}"
else
    echo -e "${RED}❌ Frontend er ikke tilgjengelig (HTTP $FRONTEND_STATUS)${NC}"
fi

echo ""

# 4. Sjekk Environment Variables Status
echo -e "${BLUE}📋 Environment Variables Status${NC}"
echo "-----------------------------------"
echo ""

echo -e "${YELLOW}⚠️  Manuell sjekk nødvendig:${NC}"
echo ""
echo "Backend (BEFS1):"
echo "  1. Gå til: https://railway.app"
echo "  2. Velg: BEFS1 service"
echo "  3. Settings → Environment"
echo "  4. Sjekk at følgende er satt:"
echo "     - DATABASE_URL"
echo "     - OPENAI_API_KEY"
echo "     - SECRET_KEY"
echo "     - BACKEND_CORS_ORIGINS"
echo ""

echo "Vercel Frontend:"
echo "  1. Gå til: https://vercel.com/dashboard"
echo "  2. Velg: knowme-frontend"
echo "  3. Settings → Environment Variables"
echo "  4. Sjekk at følgende er satt:"
echo "     - NEXTAUTH_SECRET"
echo "     - NEXT_PUBLIC_API_URL"
echo ""

# 5. Sjekk Secrets Synkronisering
echo -e "${BLUE}🔐 Secrets Synkronisering${NC}"
echo "---------------------------"
echo ""
echo -e "${YELLOW}⚠️  VIKTIG: SECRET_KEY (Railway) må matche NEXTAUTH_SECRET (Vercel)${NC}"
echo ""
echo "Sjekk:"
echo "  • Railway SECRET_KEY = Vercel NEXTAUTH_SECRET"
echo "  • Begge må være identiske (samme hemmelige verdi)"
echo ""

# 6. Oppsummering
echo "=================================="
echo -e "${BLUE}📊 Oppsummering${NC}"
echo "=================================="
echo ""

if echo "$HEALTH" | grep -q "healthy\|degraded"; then
    echo -e "${GREEN}✅ Backend: Online${NC}"
else
    echo -e "${RED}❌ Backend: Offline eller feiler${NC}"
fi

if [ "$FRONTEND_STATUS" = "200" ] || [ "$FRONTEND_STATUS" = "301" ] || [ "$FRONTEND_STATUS" = "302" ]; then
    echo -e "${GREEN}✅ Frontend: Online${NC}"
else
    echo -e "${RED}❌ Frontend: Offline eller feiler${NC}"
fi

echo ""
echo -e "${YELLOW}⚠️  Husk å sjekke Environment Variables manuelt!${NC}"
echo ""
