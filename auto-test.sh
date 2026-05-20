#!/bin/bash

# 🧪 Automatisk Test Script for BEFS
# Tester hele autentiseringsflyten automatisk

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 BEFS Auto Test Script${NC}"
echo "=============================="
echo ""

# Configuration
FRONTEND_URL="https://knowme-frontend-amber.vercel.app"
BACKEND_URL="http://localhost:8000/api/v1"

TESTS_PASSED=0
TESTS_FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

echo -e "${YELLOW}📋 Test 1: Backend Health${NC}"
echo "----------------------------"
HEALTH=$(curl -s "${BACKEND_URL}/health" 2>/dev/null || echo "")
if echo "$HEALTH" | grep -q '"status":"healthy"'; then
    test_result 0 "Backend health check"
else
    test_result 1 "Backend health check"
    echo "Response: $HEALTH"
fi
echo ""

echo -e "${YELLOW}📋 Test 2: Backend Database${NC}"
echo "----------------------------"
if echo "$HEALTH" | grep -q '"db":"connected"'; then
    test_result 0 "Database connection"
else
    test_result 1 "Database connection"
fi
echo ""

echo -e "${YELLOW}📋 Test 3: Frontend Accessibility${NC}"
echo "----------------------------"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}" 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    test_result 0 "Frontend is accessible"
else
    test_result 1 "Frontend accessibility (HTTP $FRONTEND_STATUS)"
fi
echo ""

echo -e "${YELLOW}📋 Test 4: Frontend API Routes (Requires Browser)${NC}"
echo "----------------------------"
echo -e "${YELLOW}⚠️  Dette krever browser. Åpne Console og kjør:${NC}"
echo ""
echo -e "${BLUE}Test script for browser Console:${NC}"
cat << 'EOF'
(async () => {
  console.log('=== Testing Session ===');
  const sessionRes = await fetch('/api/auth/session');
  const session = await sessionRes.json();
  console.log('Session:', session);
  console.log('Has accessToken:', !!session?.accessToken);
  
  if (!session?.accessToken) {
    console.error('❌ No accessToken!');
    return;
  }
  
  console.log('✅ Session OK');
  
  console.log('\n=== Testing Endpoints ===');
  const propsRes = await fetch('/api/properties?skip=0&limit=6');
  console.log('Properties status:', propsRes.status);
  
  const statsRes = await fetch('/api/dashboard/stats');
  console.log('Stats status:', statsRes.status);
  
  if (propsRes.status === 200 && statsRes.status === 200) {
    console.log('✅ All tests passed!');
  } else {
    console.error('❌ Some tests failed');
  }
})();
EOF
echo ""

echo "=============================="
echo -e "${BLUE}📊 Test Summary${NC}"
echo "=============================="
echo -e "${GREEN}✅ Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}❌ Failed: ${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All automated tests passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Some tests failed. Check output above.${NC}"
fi

echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Åpne ${FRONTEND_URL} i browser"
echo "2. Clear cookies og re-login"
echo "3. Åpne Console og kjør test-scriptet over"
echo ""
