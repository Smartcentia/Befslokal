#!/bin/bash
# Analyze why machine stops

echo "🔍 Analyzing why machine stops..."
echo ""

echo "1. Checking fly.toml configuration:"
grep -A 5 "http_service" fly.toml | head -10
echo ""

echo "2. Checking Dockerfile health check:"
grep -A 2 "HEALTHCHECK" Dockerfile
echo ""

echo "3. Checking if requests is in requirements:"
grep -i requests requirements.txt || echo "❌ requests not found!"
echo ""

echo "4. Health check endpoint logic:"
grep -A 20 "async def health_check" app/main.py | head -25
echo ""

echo "📊 ANALYSIS:"
echo "   - auto_stop_machines = true → Stopper ved inaktivitet"
echo "   - Health check kan feile hvis database ikke er tilkoblet"
echo "   - Dockerfile health check bruker 'requests' som kanskje mangler"
echo "   - Hvis health check feiler → Fly.io kan stoppe maskinen"
