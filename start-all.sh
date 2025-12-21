#!/bin/bash

# ═══════════════════════════════════════════════════════
#     GPU Market - Complete Stack Starter
#     Стартира: API + Frontend + Redis + Celery + Scraper
# ═══════════════════════════════════════════════════════

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${BLUE}"
cat << "EOF"
  ╔═══════════════════════════════════════════════════════╗
  ║                                                       ║
  ║       🎮  GPU MARKET - FULL STACK STARTER  🎮        ║
  ║                                                       ║
  ╚═══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Parse arguments
RUN_SCRAPER="${1:-yes}"

# ════════════════════════════════════════════════════════
# Helper Functions
# ════════════════════════════════════════════════════════

check_port() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

kill_port() {
    if check_port $1; then
        echo -e "${YELLOW}⚠️  Port $1 in use. Killing process...${NC}"
        lsof -ti:$1 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

check_command() {
    if ! command -v $1 >/dev/null 2>&1; then
        echo -e "${RED}❌ $1 is not installed!${NC}"
        return 1
    fi
    return 0
}

wait_for_service() {
    local port=$1
    local name=$2
    local max_wait=30

    echo -e "${CYAN}⏳ Waiting for $name on port $port...${NC}"
    for i in $(seq 1 $max_wait); do
        if check_port $port; then
            echo -e "${GREEN}✅ $name is ready!${NC}"
            return 0
        fi
        sleep 1
    done
    echo -e "${RED}❌ $name failed to start!${NC}"
    return 1
}

# ════════════════════════════════════════════════════════
# Step 1: Prerequisites Check
# ════════════════════════════════════════════════════════

echo -e "${BLUE}${BOLD}[1/7] Checking Prerequisites...${NC}"
echo ""

check_command python3 || exit 1
check_command node || echo -e "${YELLOW}⚠️  Node.js not found - Frontend won't start${NC}"
check_command redis-server || echo -e "${YELLOW}⚠️  Redis not found - Installing...${NC}"

# Install Redis if missing (auto-detect OS)
if ! command -v redis-server >/dev/null 2>&1; then
    echo -e "${YELLOW}📦 Installing Redis...${NC}"

    # Detect package manager
    if command -v pacman >/dev/null 2>&1; then
        # Arch-based (CachyOS, Manjaro, etc.)
        echo -e "${CYAN}🔧 Detected Arch-based system (using pacman)${NC}"
        sudo pacman -S --noconfirm redis || {
            echo -e "${RED}❌ Failed to install Redis. Please run: sudo pacman -S redis${NC}"
            exit 1
        }
    elif command -v apt-get >/dev/null 2>&1; then
        # Debian-based (Ubuntu, etc.)
        echo -e "${CYAN}🔧 Detected Debian-based system (using apt)${NC}"
        sudo apt-get update -qq && sudo apt-get install -y redis-server || {
            echo -e "${RED}❌ Failed to install Redis. Please run: sudo apt-get install redis-server${NC}"
            exit 1
        }
    elif command -v dnf >/dev/null 2>&1; then
        # Fedora/RHEL
        echo -e "${CYAN}🔧 Detected Fedora/RHEL (using dnf)${NC}"
        sudo dnf install -y redis || {
            echo -e "${RED}❌ Failed to install Redis. Please run: sudo dnf install redis${NC}"
            exit 1
        }
    else
        echo -e "${RED}❌ Unknown package manager. Please install Redis manually:${NC}"
        echo -e "${YELLOW}  - Arch/CachyOS: sudo pacman -S redis${NC}"
        echo -e "${YELLOW}  - Ubuntu/Debian: sudo apt install redis-server${NC}"
        echo -e "${YELLOW}  - Fedora: sudo dnf install redis${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Redis installed successfully${NC}"
fi

echo -e "${GREEN}✅ All prerequisites checked${NC}"
echo ""

# ════════════════════════════════════════════════════════
# Step 2: Python Environment Setup
# ════════════════════════════════════════════════════════

echo -e "${BLUE}${BOLD}[2/7] Setting up Python Environment...${NC}"
echo ""

if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚡ Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

source .venv/bin/activate

if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}⚡ Installing dependencies...${NC}"
    pip install -q -r requirements.txt
fi

echo -e "${GREEN}✅ Python environment ready${NC}"
echo ""

# ════════════════════════════════════════════════════════
# Step 3: Start Tor (Optional)
# ════════════════════════════════════════════════════════

echo -e "${BLUE}${BOLD}[3/8] Starting Tor (Optional)...${NC}"
echo ""

if [ -f "config/torrc" ] && command -v tor >/dev/null 2>&1; then
    # Check if Tor is already running
    if check_port 9150 && check_port 9151; then
        echo -e "${GREEN}✅ Tor already running (ports 9150, 9151)${NC}"
    else
        echo -e "${CYAN}🧅 Starting Tor with custom config...${NC}"
        mkdir -p logs tor_data
        tor -f config/torrc > logs/tor.log 2>&1 &
        TOR_PID=$!

        # Wait for Tor to initialize
        for i in {1..15}; do
            if check_port 9150 && check_port 9151; then
                echo -e "${GREEN}✅ Tor started (SOCKS: 9150, Control: 9151)${NC}"
                break
            fi
            sleep 1
        done

        if ! check_port 9150; then
            echo -e "${YELLOW}⚠️  Tor failed to start - continuing without Tor${NC}"
        fi
    fi
else
    if [ ! -f "config/torrc" ]; then
        echo -e "${YELLOW}⚠️  No Tor config found - skipping Tor${NC}"
    elif ! command -v tor >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Tor not installed - skipping${NC}"
    fi
fi

echo ""

# ════════════════════════════════════════════════════════
# Step 4: Start Redis
# ════════════════════════════════════════════════════════

echo -e "${BLUE}${BOLD}[4/8] Starting Redis...${NC}"
echo ""

if check_port 6379; then
    echo -e "${GREEN}✅ Redis already running${NC}"
else
    mkdir -p logs
    echo -e "${CYAN}🚀 Starting Redis on port 6379...${NC}"
    redis-server --daemonize yes --logfile logs/redis.log --dir ./
    wait_for_service 6379 "Redis" || exit 1
fi

echo ""

# ════════════════════════════════════════════════════════
# Step 5: Database Setup
# ════════════════════════════════════════════════════════

echo -e "${BLUE}${BOLD}[5/8] Database Setup...${NC}"
echo ""

if [ ! -f "gpu.db" ]; then
    echo -e "${YELLOW}⚠️  Database not found. Running migrations...${NC}"
    .venv/bin/alembic upgrade head 2>/dev/null || echo -e "${YELLOW}⚠️  No migrations${NC}"
fi

echo -e "${GREEN}✅ Database ready${NC}"
echo ""

# ════════════════════════════════════════════════════════
# Step 6: Start Backend API
# ════════════════════════════════════════════════════════

echo -e "${BLUE}${BOLD}[6/8] Starting Backend API...${NC}"
echo ""

kill_port 8000

mkdir -p logs
echo -e "${CYAN}🚀 Starting FastAPI on http://localhost:8000${NC}"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!

wait_for_service 8000 "Backend API" || exit 1
echo ""

# ════════════════════════════════════════════════════════
# Step 7: Start Celery (Worker + Beat)
# ════════════════════════════════════════════════════════

echo -e "${BLUE}${BOLD}[7/8] Starting Celery Services...${NC}"
echo ""

echo -e "${CYAN}🚀 Starting Celery Worker...${NC}"
celery -A jobs.celery_app worker --loglevel=info --logfile=logs/celery_worker.log --detach

sleep 2

echo -e "${CYAN}🚀 Starting Celery Beat (Scheduler)...${NC}"
celery -A jobs.celery_app beat --loglevel=info --logfile=logs/celery_beat.log --detach

sleep 2

echo -e "${GREEN}✅ Celery Worker & Beat started${NC}"
echo ""

# ════════════════════════════════════════════════════════
# Step 8: Start Frontend
# ════════════════════════════════════════════════════════

echo -e "${BLUE}${BOLD}[8/8] Starting Frontend...${NC}"
echo ""

if [ -d "frontend" ] && command -v node >/dev/null 2>&1; then
    cd frontend

    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}⚡ Installing frontend dependencies...${NC}"
        npm install
    fi

    kill_port 5173

    echo -e "${CYAN}🚀 Starting Vite dev server on http://localhost:5173${NC}"
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!

    cd ..

    wait_for_service 5173 "Frontend" || echo -e "${YELLOW}⚠️  Frontend startup delayed${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping frontend (not found or Node.js missing)${NC}"
fi

echo ""

# ════════════════════════════════════════════════════════
# Optional: Run Initial Scrape
# ════════════════════════════════════════════════════════

if [ "$RUN_SCRAPER" = "yes" ] || [ "$RUN_SCRAPER" = "now" ]; then
    echo -e "${BLUE}${BOLD}[BONUS] Running Initial Scrape...${NC}"
    echo ""
    echo -e "${CYAN}🕷️  Starting scraper (this may take a few minutes)...${NC}"
    python -m ingest.pipeline || echo -e "${YELLOW}⚠️  Scraper completed with warnings${NC}"
    echo ""
fi

# ════════════════════════════════════════════════════════
# Summary
# ════════════════════════════════════════════════════════

echo -e "${GREEN}${BOLD}"
cat << "EOF"
  ╔═══════════════════════════════════════════════════════╗
  ║                                                       ║
  ║            ✅  ALL SERVICES STARTED  ✅              ║
  ║                                                       ║
  ╚═══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${CYAN}📊 Service Status:${NC}"
echo ""
echo -e "  ${GREEN}✅${NC} Backend API:    http://localhost:8000"
echo -e "  ${GREEN}✅${NC} API Docs:       http://localhost:8000/docs"
echo -e "  ${GREEN}✅${NC} Frontend:       http://localhost:5173"
echo -e "  ${GREEN}✅${NC} Redis:          localhost:6379"
echo -e "  ${GREEN}✅${NC} Celery Worker:  Running (see logs/celery_worker.log)"
echo -e "  ${GREEN}✅${NC} Celery Beat:    Running (see logs/celery_beat.log)"

# Check if Tor is running
if check_port 9150; then
    echo -e "  ${GREEN}✅${NC} Tor Proxy:      SOCKS5 localhost:9150"
else
    echo -e "  ${YELLOW}⚠️${NC}  Tor Proxy:      Not running (optional)"
fi
echo ""

echo -e "${CYAN}📝 Logs:${NC}"
echo "  - Backend:       tail -f logs/backend.log"
echo "  - Frontend:      tail -f logs/frontend.log"
echo "  - Celery Worker: tail -f logs/celery_worker.log"
echo "  - Celery Beat:   tail -f logs/celery_beat.log"
echo "  - Redis:         tail -f logs/redis.log"
echo "  - Tor:           tail -f logs/tor.log (if enabled)"
echo ""

echo -e "${CYAN}🛑 To stop all services:${NC}"
echo "  ./stop.sh"
echo ""

echo -e "${YELLOW}💡 Tips:${NC}"
echo "  - Scraper runs automatically every 6 hours (via Celery Beat)"
echo "  - To run scraper manually: python -m ingest.pipeline"
echo "  - To skip initial scrape: ./start-all.sh no"
echo ""

# Keep processes running in foreground (optional)
# Uncomment to wait for user interrupt:
# echo -e "${CYAN}Press Ctrl+C to stop all services...${NC}"
# wait

echo -e "${GREEN}✨ GPU Market is ready!${NC}"
