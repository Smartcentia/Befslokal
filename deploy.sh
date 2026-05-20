#!/bin/bash
# 🚀 Komplett Deploy Script - Frontend
# Frontend: Vercel (auto-deploy ved push).

set -e

# Farger for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Konfigurasjon
APP_NAME="knowme-backend-prod"
# BACKEND_URL: Configure based on your hosting provider

FRONTEND_URL="https://knowme-frontend-amber.vercel.app"

echo ""
echo -e "${BLUE}🚀 BEFS Deploy Script${NC}"
echo "=================================="
echo ""

# Funksjoner
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Sjekk at vi er i riktig mappe
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Må kjøre fra prosjektets rot-mappe (BEFS_CLEAN)"
    exit 1
fi

# Steg 1: Sjekk git status
echo "📋 Steg 1: Sjekker Git Status"
echo "----------------------------"
if [ -n "$(git status --porcelain)" ]; then
    print_warning "Det finnes uncommitted endringer:"
    git status --short
    echo ""
    read -p "Vil du committe disse først? (j/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        git add .
        read -p "Commit melding: " commit_msg
        git commit -m "$commit_msg"
        print_success "Endringer committet"
    else
        print_warning "Hopper over commit - deployer eksisterende commits"
    fi
else
    print_success "Ingen uncommitted endringer"
fi

# Vis commits som ikke er pushet
AHEAD=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "0")
if [ "$AHEAD" -gt "0" ]; then
    echo ""
    print_info "Du har $AHEAD commit(s) som ikke er pushet:"
    git log --oneline @{u}..HEAD
    echo ""
else
    print_info "Alle commits er pushet"
fi

# Steg 2: Git Push (Frontend auto-deployer)
echo ""
echo "📋 Steg 2: Git Push (Frontend Auto-Deploy)"
echo "------------------------------------------"
read -p "Vil du pushe til GitHub nå? (j/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Jj]$ ]]; then
    print_info "Prøver git push..."
    if git push origin main; then
        print_success "Git push lykkes!"
        print_info "Frontend vil auto-deploye på Vercel om 2-5 minutter"
        print_info "Se status: https://vercel.com"
    else
        print_error "Git push feilet (nettverksproblem?)"
        print_warning "Du kan deploye frontend manuelt via Vercel Dashboard"
        print_info "URL: https://vercel.com"
    fi
else
    print_warning "Hopper over git push"
fi

# Steg 3: Verifiser Secrets
echo ""
echo "📋 Steg 3: Verifiser Secrets"
echo "----------------------------"
print_info "Sjekk frontend secret:"
echo "  Vercel Dashboard → Settings → Environment Variables → NEXTAUTH_SECRET"
echo ""

# Oppsummering
echo ""
echo "=================================="
echo -e "${GREEN}✅ Deploy Prosess Fullført!${NC}"
echo "=================================="
echo ""
echo "📊 Oppsummering:"
echo "  • Git push: $(if git rev-parse --verify origin/main &>/dev/null && [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ]; then echo -e "${GREEN}✅${NC}"; else echo -e "${YELLOW}⏳${NC}"; fi)"
echo "  • Frontend: $(if [ -n "$(git rev-parse --verify origin/main 2>/dev/null)" ]; then echo -e "${GREEN}✅ Auto-deployer${NC}"; else echo -e "${YELLOW}⏳ Vent på git push${NC}"; fi)"
echo ""
echo "🔗 Nyttige lenker:"
echo "  • Frontend Dashboard: https://vercel.com"
echo "  • Frontend URL: $FRONTEND_URL"
echo ""

