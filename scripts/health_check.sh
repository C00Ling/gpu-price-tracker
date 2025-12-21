#!/bin/bash

# ============================================
# GPU Market Service - Health Check Script
# ============================================
# Checks if all services are running properly
# Exit code 0 = healthy, 1 = unhealthy

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_URL=${API_URL:-"http://localhost:8000"}
TIMEOUT=10

echo "🏥 GPU Market Service - Health Check"
echo "===================================="
echo ""

ERRORS=0

# Function to check service
check_service() {
    local name=$1
    local check_command=$2
    
    echo -n "Checking $name... "
    
    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# 1. Check API Health Endpoint
check_service "API Health" \
    "curl -sf --max-time $TIMEOUT $API_URL/health"

# 2. Check API Docs
check_service "API Docs" \
    "curl -sf --max-time $TIMEOUT $API_URL/docs"

# 3. Check Dashboard
check_service "Dashboard" \
    "curl -sf --max-time $TIMEOUT $API_URL/dashboard"

# 4. Check Listings Endpoint
check_service "Listings API" \
    "curl -sf --max-time $TIMEOUT $API_URL/api/listings/"

# 5. Check Stats Endpoint
check_service "Stats API" \
    "curl -sf --max-time $TIMEOUT $API_URL/api/stats/"

# 6. Check Value Endpoint
check_service "Value API" \
    "curl -sf --max-time $TIMEOUT $API_URL/api/value/"

# 7. Check TOR (if enabled)
if [ "${SCRAPER_USE_TOR:-true}" = "true" ]; then
    check_service "TOR Proxy" \
        "curl -sf --max-time $TIMEOUT --socks5 localhost:9050 https://check.torproject.org/api/ip"
fi

# 8. Check Database
check_service "Database" \
    "test -f gpu.db"

# 9. Check Logs
check_service "Log Files" \
    "test -f logs/gpu_service.log"

echo ""
echo "===================================="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo -e "${GREEN}Service is healthy${NC}"
    exit 0
else
    echo -e "${RED}✗ $ERRORS check(s) failed!${NC}"
    echo -e "${RED}Service is unhealthy${NC}"
    exit 1
fi