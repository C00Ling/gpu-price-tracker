#!/bin/bash

# ═══════════════════════════════════════════════════════
#     GPU Market - Stop All Services
#     Stops: API + Frontend + Redis + Celery Worker + Beat
# ═══════════════════════════════════════════════════════

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${BLUE}"
cat << "EOF"
  ╔═══════════════════════════════════════════════════════╗
  ║         🛑  STOPPING GPU MARKET SERVICES  🛑         ║
  ╚═══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Stop Backend API
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo -e "${YELLOW}⏹  Stopping Backend API...${NC}"
    pkill -9 -f "uvicorn main:app"
    echo -e "${GREEN}✅ Backend stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Backend is not running${NC}"
fi

# Stop Frontend
if pgrep -f "vite" > /dev/null; then
    echo -e "${YELLOW}⏹  Stopping Frontend...${NC}"
    pkill -9 -f "vite"
    echo -e "${GREEN}✅ Frontend stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend is not running${NC}"
fi

# Stop Celery Worker
if pgrep -f "celery.*worker" > /dev/null; then
    echo -e "${YELLOW}⏹  Stopping Celery Worker...${NC}"
    pkill -9 -f "celery.*worker"
    echo -e "${GREEN}✅ Celery Worker stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Celery Worker is not running${NC}"
fi

# Stop Celery Beat
if pgrep -f "celery.*beat" > /dev/null; then
    echo -e "${YELLOW}⏹  Stopping Celery Beat...${NC}"
    pkill -9 -f "celery.*beat"
    echo -e "${GREEN}✅ Celery Beat stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Celery Beat is not running${NC}"
fi

# Stop Redis
if pgrep -f "redis-server" > /dev/null; then
    echo -e "${YELLOW}⏹  Stopping Redis...${NC}"
    redis-cli shutdown 2>/dev/null || pkill -9 -f "redis-server"
    echo -e "${GREEN}✅ Redis stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Redis is not running${NC}"
fi

# Stop Tor (if running)
if pgrep -f "tor -f config/torrc" > /dev/null; then
    echo -e "${YELLOW}⏹  Stopping Tor...${NC}"
    pkill -9 -f "tor -f config/torrc"
    echo -e "${GREEN}✅ Tor stopped${NC}"
fi

# Clean up PID files
rm -f celerybeat.pid 2>/dev/null

echo ""
echo -e "${GREEN}${BOLD}✅ All services stopped!${NC}"
echo ""
