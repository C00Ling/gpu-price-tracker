#!/bin/bash
# GPU Market Service - Quick Start Script
# Usage: ./quickstart.sh

set -e

echo "=========================================="
echo "🚀 GPU Market Service - Quick Start"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}📌 Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $python_version"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo -e "${BLUE}🔌 Activating virtual environment...${NC}"
source .venv/bin/activate

# Install dependencies
echo -e "${BLUE}📥 Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Initialize database
echo -e "${BLUE}🗄️  Initializing database...${NC}"
if [ ! -f "gpu.db" ]; then
    python -c "from storage.db import init_db; init_db()"
    echo -e "${GREEN}✅ Database created${NC}"
else
    echo -e "${GREEN}✅ Database already exists${NC}"
fi

# Run tests
echo -e "${BLUE}🧪 Running tests...${NC}"
pytest tests/ -q --tb=no || {
    echo -e "${YELLOW}⚠️  Some tests failed, but continuing...${NC}"
}

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Setup complete!${NC}"
echo "=========================================="
echo ""
echo "🌐 Start the API server:"
echo "   python main.py"
echo ""
echo "📖 API Documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "🎨 Dashboard:"
echo "   http://localhost:8000/dashboard"
echo ""
echo "📊 Sample endpoints:"
echo "   http://localhost:8000/health"
echo "   http://localhost:8000/api/listings/"
echo "   http://localhost:8000/api/stats/"
echo ""
echo "🔧 To run scraper:"
echo "   python -m ingest.pipeline"
echo ""
echo "=========================================="
