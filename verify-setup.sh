#!/bin/bash
# Multi-Service Architecture Setup Verification Script
# Checks that all services are running correctly

set -e

echo "=================================================================="
echo "🔍 GPU Price Tracker - Multi-Service Setup Verification"
echo "=================================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Success/Failure counters
CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to print check results
check_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

echo "1️⃣  Checking Docker and Docker Compose..."
echo "------------------------------------------------------------------"

# Check if Docker is installed
if command -v docker &> /dev/null; then
    check_pass "Docker is installed ($(docker --version))"
else
    check_fail "Docker is not installed"
    echo "   Install: https://docs.docker.com/get-docker/"
fi

# Check if Docker Compose is installed
if command -v docker-compose &> /dev/null; then
    check_pass "Docker Compose is installed ($(docker-compose --version))"
else
    check_fail "Docker Compose is not installed"
    echo "   Install: https://docs.docker.com/compose/install/"
fi

# Check if Docker daemon is running
if docker info &> /dev/null; then
    check_pass "Docker daemon is running"
else
    check_fail "Docker daemon is not running"
    echo "   Start: sudo systemctl start docker"
fi

echo ""
echo "2️⃣  Checking Docker Compose Services..."
echo "------------------------------------------------------------------"

# Check if docker-compose.yml exists
if [ -f "docker-compose.yml" ]; then
    check_pass "docker-compose.yml found"
else
    check_fail "docker-compose.yml not found"
    exit 1
fi

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    RUNNING_SERVICES=$(docker-compose ps --services --filter "status=running")

    # Check PostgreSQL
    if echo "$RUNNING_SERVICES" | grep -q "postgres"; then
        check_pass "PostgreSQL service is running"
    else
        check_fail "PostgreSQL service is not running"
    fi

    # Check API
    if echo "$RUNNING_SERVICES" | grep -q "api"; then
        check_pass "API service is running"
    else
        check_fail "API service is not running"
    fi

    # Check Scraper
    if echo "$RUNNING_SERVICES" | grep -q "scraper"; then
        check_pass "Scraper worker is running"
    else
        check_fail "Scraper worker is not running"
    fi
else
    check_warn "No services are running. Start with: docker-compose up -d"
fi

echo ""
echo "3️⃣  Checking Service Health..."
echo "------------------------------------------------------------------"

# Check PostgreSQL health
if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
    check_pass "PostgreSQL is healthy and accepting connections"
else
    check_fail "PostgreSQL is not responding"
fi

# Check API health endpoint
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    API_HEALTH=$(curl -s http://localhost:8000/health)
    check_pass "API health endpoint is responding"
    echo "   Response: $API_HEALTH"
else
    check_fail "API health endpoint is not responding"
    check_warn "Is the API service running on port 8000?"
fi

# Check if API can connect to database
if curl -s http://localhost:8000/health | grep -q '"database":"connected"'; then
    check_pass "API can connect to PostgreSQL"
else
    check_warn "API may have database connection issues"
fi

echo ""
echo "4️⃣  Checking Database..."
echo "------------------------------------------------------------------"

# Check if database exists
if docker-compose exec -T postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -qw gpu_tracker; then
    check_pass "Database 'gpu_tracker' exists"

    # Check if tables exist
    TABLE_COUNT=$(docker-compose exec -T postgres psql -U postgres -d gpu_tracker -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')

    if [ "$TABLE_COUNT" -gt 0 ]; then
        check_pass "Database has $TABLE_COUNT table(s)"
    else
        check_warn "Database has no tables yet (normal on first startup)"
    fi

    # Check if there's any data
    LISTING_COUNT=$(docker-compose exec -T postgres psql -U postgres -d gpu_tracker -t -c "SELECT COUNT(*) FROM gpu_listings;" 2>/dev/null | tr -d ' ' || echo "0")

    if [ "$LISTING_COUNT" -gt 0 ]; then
        check_pass "Database has $LISTING_COUNT GPU listings"
    else
        check_warn "No GPU listings in database yet"
        echo "   Wait for scraper to complete first cycle, or run:"
        echo "   docker-compose run --rm -e WORKER_MODE=oneshot scraper"
    fi
else
    check_fail "Database 'gpu_tracker' does not exist"
fi

echo ""
echo "5️⃣  Checking TOR (Scraper Worker)..."
echo "------------------------------------------------------------------"

# Check if TOR is running in scraper container
if docker-compose exec -T scraper pgrep tor > /dev/null 2>&1; then
    check_pass "TOR is running in scraper container"

    # Check TOR connectivity
    if docker-compose exec -T scraper curl --socks5 localhost:9050 -s https://check.torproject.org/api/ip 2>/dev/null | grep -q '"IsTor":true'; then
        check_pass "TOR connection is working"
    else
        check_warn "TOR may not be configured correctly"
    fi
else
    check_warn "TOR process not found (scraper may not be running yet)"
fi

echo ""
echo "6️⃣  Checking API Endpoints..."
echo "------------------------------------------------------------------"

# Check main endpoints
ENDPOINTS=(
    "/"
    "/health"
    "/docs"
    "/api/listings/"
)

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -f -s "http://localhost:8000${endpoint}" > /dev/null 2>&1; then
        check_pass "Endpoint ${endpoint} is accessible"
    else
        check_fail "Endpoint ${endpoint} is not accessible"
    fi
done

echo ""
echo "7️⃣  Checking Configuration Files..."
echo "------------------------------------------------------------------"

# Check if service .env files exist
if [ -f "services/api/.env" ] || [ -f "services/api/.env.example" ]; then
    check_pass "API service configuration exists"
else
    check_warn "API service .env not found (using defaults)"
fi

if [ -f "services/scraper/.env" ] || [ -f "services/scraper/.env.example" ]; then
    check_pass "Scraper service configuration exists"
else
    check_warn "Scraper service .env not found (using defaults)"
fi

echo ""
echo "=================================================================="
echo "📊 VERIFICATION SUMMARY"
echo "=================================================================="
echo -e "Checks Passed: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Checks Failed: ${RED}$CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 SUCCESS! Your multi-service architecture is working correctly!${NC}"
    echo ""
    echo "Next steps:"
    echo "  - Access API: http://localhost:8000"
    echo "  - View API Docs: http://localhost:8000/docs"
    echo "  - View logs: docker-compose logs -f"
    echo "  - Run manual scrape: docker-compose run --rm -e WORKER_MODE=oneshot scraper"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  ISSUES DETECTED${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Start services: docker-compose up -d"
    echo "  2. Check logs: docker-compose logs"
    echo "  3. Restart services: docker-compose restart"
    echo "  4. Read documentation: cat MIGRATION.md"
    echo ""
    exit 1
fi
