#!/bin/bash
# Quick setup script for security scanning tools
# Usage: bash scripts/setup-security.sh

set -e  # Exit on error

echo "🔒 Setting up security scanning for BEFS..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Install pre-commit
echo -e "${YELLOW}📦 Installing pre-commit...${NC}"
pip install pre-commit

# 2. Install pre-commit hooks
echo -e "${YELLOW}🔧 Installing pre-commit hooks...${NC}"
pre-commit install

# 3. Install security tools for backend
echo -e "${YELLOW}🐍 Installing Python security tools...${NC}"
cd backend
pip install safety bandit black
cd ..

# 4. Run initial security scan
echo -e "${YELLOW}🔍 Running initial security scan...${NC}"
pre-commit run --all-files || true

echo ""
echo -e "${GREEN}✅ Security tools installed!${NC}"
echo ""
echo "Next steps:"
echo "1. Go to GitHub repo → Settings → Security → Enable Dependabot"
echo "2. Sign up at snyk.io with GitHub"
echo "3. Add SNYK_TOKEN to GitHub Secrets"
echo "4. Read SECURITY_SETUP.md for full guide"
echo ""
echo "Happy secure coding! 🚀"
