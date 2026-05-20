#!/bin/bash
# Komplett pre-deploy test suite
# Kjør dette før commit og deploy

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🚀 Pre-Deploy Test Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Test 1: Python auth tests
echo -e "${YELLOW}Test 1: Python auth tests...${NC}"
if python3 test_auth_fixes.py; then
    echo -e "${GREEN}✅ Python auth tests passed${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Python auth tests failed${NC}"
    ((FAILED++))
fi
echo ""

# Test 2: Frontend build
echo -e "${YELLOW}Test 2: Frontend build...${NC}"
if bash test_frontend_build.sh; then
    echo -e "${GREEN}✅ Frontend build passed${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Frontend build failed${NC}"
    ((FAILED++))
fi
echo ""

# Test 3: Sjekk at kritiske filer er endret
echo -e "${YELLOW}Test 3: Verifiser kritiske filer...${NC}"
CRITICAL_FILES=(
    "backend/app/api/deps.py"
    "backend/app/core/security.py"
    "frontend/app/api/auth/[...nextauth]/route.ts"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ✅ $file eksisterer"
    else
        echo -e "  ${RED}❌ $file mangler${NC}"
        ((FAILED++))
    fi
done
((PASSED++))
echo ""

# Test 4: Sjekk git status
echo -e "${YELLOW}Test 4: Git status...${NC}"
if git diff --quiet && git diff --cached --quiet; then
    echo -e "  ${YELLOW}⚠️  Ingen endringer å committe${NC}"
else
    echo -e "  ✅ Endringer funnet (klar for commit)"
    git status --short
fi
echo ""

# Summary
echo "=========================================="
echo -e "${YELLOW}📊 Test Summary${NC}"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
    echo ""
    echo -e "${RED}❌ Noen tester feilet. Fiks feilene før commit/deploy!${NC}"
    exit 1
else
    echo -e "${GREEN}Failed: $FAILED${NC}"
    echo ""
    echo -e "${GREEN}✅ Alle tester passerte! Klar for commit/deploy.${NC}"
    exit 0
fi
