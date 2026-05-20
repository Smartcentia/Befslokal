#!/bin/bash

# 🔍 Omfattende test-suite for autentiseringsflyt
# Tester backend, frontend og hele auth-flow



echo "🔍 BEFS Authentication Flow Test Suite"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="https://striking-insight-production-a21b.up.railway.app/api/v1"
FRONTEND_URL="https://knowme-frontend-amber.vercel.app"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

echo "📋 Test 1: Backend Health Check"
echo "-------------------------------"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/health" 2>/dev/null || echo -e "\n000")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "Response: $BODY"
    if echo "$BODY" | grep -q '"status":"healthy"'; then
        test_result 0 "Backend health endpoint responds"
    else
        test_result 1 "Backend health endpoint returns 200 but status not healthy"
    fi
else
    test_result 1 "Backend health endpoint failed (HTTP $HTTP_CODE)"
fi
echo ""

echo "📋 Test 2: Backend Database Connection"
echo "--------------------------------------"
if echo "$BODY" | grep -q '"db":"connected"'; then
    test_result 0 "Database is connected"
else
    test_result 1 "Database connection failed"
    echo "Response: $BODY"
fi
echo ""

echo "📋 Test 3: Backend CORS Configuration"
echo "-------------------------------------"
CORS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Origin: ${FRONTEND_URL}" \
    -H "Access-Control-Request-Method: GET" \
    -X OPTIONS \
    "${BACKEND_URL}/health" 2>/dev/null || echo "000")

if [ "$CORS_RESPONSE" = "200" ] || [ "$CORS_RESPONSE" = "204" ]; then
    test_result 0 "CORS preflight request succeeds"
else
    test_result 1 "CORS preflight failed (HTTP $CORS_RESPONSE)"
fi
echo ""

echo "📋 Test 4: Unauthenticated Request (Should Fail)"
echo "------------------------------------------------"
UNAUTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/dashboard/status" 2>/dev/null || echo -e "\n000")
UNAUTH_HTTP=$(echo "$UNAUTH_RESPONSE" | tail -n1)
UNAUTH_BODY=$(echo "$UNAUTH_RESPONSE" | sed '$d')

if [ "$UNAUTH_HTTP" = "401" ]; then
    test_result 0 "Unauthenticated request correctly returns 401"
    if echo "$UNAUTH_BODY" | grep -q "Unauthorized\|Authentication"; then
        test_result 0 "Error message mentions authentication"
    fi
else
    test_result 1 "Unauthenticated request should return 401, got $UNAUTH_HTTP"
fi
echo ""

echo "📋 Test 5: Invalid Token (Should Fail)"
echo "---------------------------------------"
INVALID_TOKEN="invalid.token.here"
INVALID_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer ${INVALID_TOKEN}" \
    "${BACKEND_URL}/dashboard/status" 2>/dev/null || echo -e "\n000")
INVALID_HTTP=$(echo "$INVALID_RESPONSE" | tail -n1)
INVALID_BODY=$(echo "$INVALID_RESPONSE" | sed '$d')

if [ "$INVALID_HTTP" = "401" ]; then
    test_result 0 "Invalid token correctly returns 401"
else
    test_result 1 "Invalid token should return 401, got $INVALID_HTTP"
fi
echo ""

echo "📋 Test 6: Frontend Accessibility"
echo "---------------------------------"
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}" 2>/dev/null || echo "000")

if [ "$FRONTEND_RESPONSE" = "200" ]; then
    test_result 0 "Frontend is accessible"
else
    test_result 1 "Frontend not accessible (HTTP $FRONTEND_RESPONSE)"
fi
echo ""

echo "📋 Test 7: Frontend API Routes"
echo "----------------------------"
FRONTEND_API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}/api/auth/signin" 2>/dev/null || echo "000")

if [ "$FRONTEND_API_RESPONSE" = "200" ] || [ "$FRONTEND_API_RESPONSE" = "405" ]; then
    test_result 0 "Frontend API routes are accessible"
else
    test_result 1 "Frontend API routes not accessible (HTTP $FRONTEND_API_RESPONSE)"
fi
echo ""

echo "📋 Test 8: Backend Environment Variables Check"
echo "---------------------------------------------"
echo -e "${YELLOW}⚠️  Manual check required:${NC}"
echo "1. Railway Dashboard → BEFS1 → Environment"
echo "2. Verify these variables exist:"
echo "   - DATABASE_URL (should be set)"
echo "   - SECRET_KEY (should be set)"
echo "   - BACKEND_CORS_ORIGINS (should include ${FRONTEND_URL})"
echo "   - OPENAI_API_KEY (should be set)"
echo ""

echo "📋 Test 9: Frontend Environment Variables Check"
echo "----------------------------------------------"
echo -e "${YELLOW}⚠️  Manual check required:${NC}"
echo "1. Vercel Dashboard → knowme-frontend → Environment Variables"
echo "2. Verify these variables exist:"
echo "   - NEXTAUTH_SECRET (should be set)"
echo "   - NEXT_PUBLIC_API_URL (should be ${BACKEND_URL})"
echo "   - DATABASE_URL (should be set)"
echo ""

echo "📋 Test 10: Secret Synchronization Check"
echo "----------------------------------------"
echo -e "${YELLOW}⚠️  Manual check required:${NC}"
echo "1. Railway: BEFS1 → Environment → SECRET_KEY"
echo "2. Vercel: knowme-frontend → Environment Variables → NEXTAUTH_SECRET"
echo "3. These MUST be IDENTICAL (copy-paste to verify)"
echo ""

echo "📋 Test 11: Deployment Status"
echo "----------------------------"
echo -e "${YELLOW}⚠️  Manual check required:${NC}"
echo "1. Railway: BEFS1 → Check latest deploy is after SECRET_KEY was added"
echo "2. Vercel: knowme-frontend → Deployments → Check latest deploy is after NEXTAUTH_SECRET was added"
echo ""

echo "📋 Test 12: Token Generation Flow (Browser Test)"
echo "------------------------------------------------"
echo -e "${YELLOW}⚠️  Manual browser test required:${NC}"
echo "1. Open: ${FRONTEND_URL}"
echo "2. Open Developer Tools → Console"
echo "3. Log in with: admin@befs.no"
echo "4. Check console for:"
echo "   ✅ [NextAuth] Generating backend token for user: admin@befs.no"
echo "   ✅ [NextAuth] Token generated, length: XXX"
echo "   ✅ [fetchAPI] Token found, length: XXX"
echo "   ❌ Should NOT see: [fetchAPI] No accessToken in session!"
echo ""

echo "📋 Test 13: Authenticated API Call (Browser Test)"
echo "-------------------------------------------------"
echo -e "${YELLOW}⚠️  Manual browser test required:${NC}"
echo "1. After logging in, go to Dashboard"
echo "2. Open Developer Tools → Network tab"
echo "3. Check requests to striking-insight-production-a21b.up.railway.app"
echo "4. Click on a request → Headers"
echo "5. Verify: Authorization: Bearer <token> header exists"
echo "6. Verify: Response is 200 OK (not 401)"
echo ""

echo "======================================"
echo "📊 Test Summary"
echo "======================================"
echo -e "${GREEN}✅ Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}❌ Failed: ${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All automated tests passed!${NC}"
    echo ""
    echo "⚠️  Remember to complete manual tests (8-13)!"
else
    echo -e "${RED}⚠️  Some tests failed. Check output above.${NC}"
fi

echo ""
echo "🔍 Next Steps:"
echo "1. Complete manual tests (8-13)"
echo "2. If frontend still shows 401 errors:"
echo "   - Redeploy frontend in Vercel (click 'Redeploy' in notification)"
echo "   - Clear cookies and re-login"
echo "   - Check that NEXTAUTH_SECRET matches SECRET_KEY exactly"
echo ""
