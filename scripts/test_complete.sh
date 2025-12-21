#!/bin/bash

# ============================================
# Complete Integration Test
# ============================================
# Tests entire application stack

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 GPU Market Service - Complete Integration Test${NC}"
echo "=========================================================="
echo ""

ERRORS=0
API_PID=""

cleanup() {
    if [ -n "$API_PID" ]; then
        echo ""
        echo -e "${YELLOW}🛑 Stopping test server...${NC}"
        kill $API_PID 2>/dev/null || true
    fi
    
    if [ $ERRORS -eq 0 ]; then
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${GREEN}🎉 Your application is production ready!${NC}"
        exit 0
    else
        echo ""
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}✗ $ERRORS test(s) failed${NC}"
        echo -e "${RED}========================================${NC}"
        exit 1
    fi
}

trap cleanup EXIT INT TERM

test_step() {
    local name=$1
    local command=$2
    
    echo -n "Testing $name... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# 1. Environment Check
echo -e "${BLUE}📋 Step 1: Environment Check${NC}"
echo "----------------------------"

test_step "Python version" "python3 --version | grep -E '3\.(8|9|10|11|12|13)'"
test_step "Dependencies installed" "pip show fastapi uvicorn sqlalchemy"
test_step "TOR service" "systemctl is-active tor || pgrep tor"
test_step ".env file exists" "test -f .env"
test_step "config.yaml exists" "test -f config.yaml"

echo ""

# 2. Database Check
echo -e "${BLUE}💾 Step 2: Database Check${NC}"
echo "------------------------"

test_step "Database file exists" "test -f gpu.db"
test_step "Database has data" "sqlite3 gpu.db 'SELECT COUNT(*) FROM listings' | grep -v '^0$'"

echo ""

# 3. Start API Server
echo -e "${BLUE}🚀 Step 3: Starting API Server${NC}"
echo "-------------------------------"

echo -n "Starting server... "
uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/api_test.log 2>&1 &
API_PID=$!

# Wait for startup
for i in {1..15}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Started (PID: $API_PID)${NC}"
        break
    fi
    
    if [ $i -eq 15 ]; then
        echo -e "${RED}✗ Failed to start${NC}"
        echo "Logs:"
        cat /tmp/api_test.log
        ERRORS=$((ERRORS + 1))
        exit 1
    fi
    
    sleep 1
done

echo ""

# 4. API Endpoint Tests
echo -e "${BLUE}🔌 Step 4: API Endpoint Tests${NC}"
echo "-----------------------------"

test_step "Health endpoint" "curl -sf http://localhost:8000/health | grep -q 'healthy'"
test_step "Root endpoint" "curl -sf http://localhost:8000/ | grep -q 'GPU Market'"
test_step "Docs endpoint" "curl -sf http://localhost:8000/docs"
test_step "Dashboard endpoint" "curl -sf http://localhost:8000/dashboard | grep -q 'GPU Market'"

echo ""
echo -e "${BLUE}📊 Step 5: Data Endpoints${NC}"
echo "------------------------"

test_step "Listings API" "curl -sf http://localhost:8000/api/listings/ | python3 -c 'import sys,json; data=json.load(sys.stdin); exit(0 if len(data)>0 else 1)'"
test_step "Stats API" "curl -sf http://localhost:8000/api/stats/ | python3 -c 'import sys,json; data=json.load(sys.stdin); exit(0 if len(data)>0 else 1)'"
test_step "Value API" "curl -sf http://localhost:8000/api/value/ | python3 -c 'import sys,json; data=json.load(sys.stdin); exit(0 if len(data)>0 else 1)'"

echo ""
echo -e "${BLUE}🎨 Step 6: Frontend Tests${NC}"
echo "-------------------------"

test_step "Dashboard loads" "curl -sf http://localhost:8000/dashboard | grep -q 'Chart.js'"
test_step "Landing page (if exists)" "curl -sf http://localhost:8000/home | grep -q 'GPU' || true"

echo ""
echo -e "${BLUE}📈 Step 7: Performance Tests${NC}"
echo "---------------------------"

echo -n "Response time check... "
START=$(date +%s%N)
curl -sf http://localhost:8000/health > /dev/null
END=$(date +%s%N)
DURATION=$(( (END - START) / 1000000 ))

if [ $DURATION -lt 1000 ]; then
    echo -e "${GREEN}✓ ${DURATION}ms${NC}"
else
    echo -e "${YELLOW}⚠ ${DURATION}ms (slow)${NC}"
fi

echo ""
echo -e "${BLUE}🔍 Step 8: Data Quality Check${NC}"
echo "-----------------------------"

# Check data quality
LISTING_COUNT=$(curl -sf http://localhost:8000/api/listings/ | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
MODEL_COUNT=$(curl -sf http://localhost:8000/api/stats/ | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")

echo -e "Listings: ${GREEN}$LISTING_COUNT${NC}"
echo -e "Models: ${GREEN}$MODEL_COUNT${NC}"

if [ "$LISTING_COUNT" -gt 0 ] && [ "$MODEL_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Data quality check passed${NC}"
else
    echo -e "${RED}✗ No data found${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo -e "${BLUE}🔧 Step 9: System Resources${NC}"
echo "--------------------------"

echo "Memory usage:"
ps aux | grep "uvicorn\|python" | grep -v grep | awk '{print "  "$11" - "$4"% RAM"}'

echo ""
echo "Disk usage:"
du -sh . | awk '{print "  Project: "$1}'
du -sh gpu.db 2>/dev/null | awk '{print "  Database: "$1}' || echo "  Database: N/A"
du -sh logs/ 2>/dev/null | awk '{print "  Logs: "$1}' || echo "  Logs: N/A"

# Cleanup will run automatically via trap