#!/bin/bash

# ═══════════════════════════════════════════════════════
#     GPU Market - Service Status Checker
# ═══════════════════════════════════════════════════════

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${BLUE}"
cat << "EOF"
  ╔═══════════════════════════════════════════════════════╗
  ║           📊  GPU MARKET SERVICE STATUS  📊          ║
  ╚═══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

check_service() {
    local name=$1
    local pattern=$2
    local port=$3

    if pgrep -f "$pattern" > /dev/null; then
        if [ -n "$port" ]; then
            echo -e "  ${GREEN}✅${NC} ${name} ${GREEN}RUNNING${NC} (port: $port)"
        else
            echo -e "  ${GREEN}✅${NC} ${name} ${GREEN}RUNNING${NC}"
        fi
        return 0
    else
        echo -e "  ${RED}❌${NC} ${name} ${RED}STOPPED${NC}"
        return 1
    fi
}

# Check all services
check_service "Backend API     " "uvicorn main:app" "8000"
check_service "Frontend        " "vite" "5173"
check_service "Redis           " "redis-server" "6379"
check_service "Celery Worker   " "celery.*worker"
check_service "Celery Beat     " "celery.*beat"
check_service "Tor Proxy       " "tor -f config/torrc" "9150"

echo ""
echo -e "${BLUE}📊 Port Status:${NC}"

check_port() {
    local port=$1
    local name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅${NC} Port $port ($name) is ${GREEN}OPEN${NC}"
    else
        echo -e "  ${YELLOW}⚠️${NC}  Port $port ($name) is ${YELLOW}CLOSED${NC}"
    fi
}

check_port 8000 "Backend API"
check_port 5173 "Frontend"
check_port 6379 "Redis"

echo ""
echo -e "${BLUE}📝 Recent Logs:${NC}"
if [ -f "logs/backend.log" ]; then
    echo -e "${YELLOW}Backend (last 3 lines):${NC}"
    tail -n 3 logs/backend.log 2>/dev/null || echo "  No logs"
fi

echo ""
