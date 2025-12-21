.PHONY: help install run test clean deploy backup health logs \
        frontend-install frontend-dev frontend-build frontend-test \
        start start-all stop status \
        full-install full-clean

# Default target
.DEFAULT_GOAL := help

# Colors
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

help: ## Show this help message
	@echo '${GREEN}═══════════════════════════════════════════${RESET}'
	@echo '${GREEN}   GPU Market - Full Stack Application${RESET}'
	@echo '${GREEN}═══════════════════════════════════════════${RESET}'
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo '${GREEN}🚀 Quick Start:${RESET}'
	@echo '  ${YELLOW}make start${RESET}              - Start COMPLETE stack (API + Frontend + Redis + Celery + Tor)'
	@echo '  ${YELLOW}make stop${RESET}               - Stop all services'
	@echo '  ${YELLOW}make status${RESET}             - Check service status'
	@echo ''
	@echo '${GREEN}📦 Full Stack:${RESET}'
	@awk 'BEGIN {FS = ":.*?## "} /^(start|stop|full-|init):.*?## / {printf "  ${YELLOW}%-20s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ''
	@echo '${GREEN}🎨 Frontend:${RESET}'
	@awk 'BEGIN {FS = ":.*?## "} /^frontend-.*?## / {printf "  ${YELLOW}%-20s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ''
	@echo '${GREEN}🐍 Backend:${RESET}'
	@awk 'BEGIN {FS = ":.*?## "} /^(install|dev|scrape|test|lint|format):.*?## / {printf "  ${YELLOW}%-20s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ''
	@echo '${GREEN}🐳 Docker:${RESET}'
	@awk 'BEGIN {FS = ":.*?## "} /^docker-.*?## / {printf "  ${YELLOW}%-20s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ''
	@echo '${GREEN}🛠️  Utilities:${RESET}'
	@awk 'BEGIN {FS = ":.*?## "} /^(clean|logs|health|backup|db-):.*?## / {printf "  ${YELLOW}%-20s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"

install-dev: ## Install development dependencies
	@echo "📦 Installing dev dependencies..."
	pip install -r requirements.txt
	pip install pytest pytest-cov black flake8 mypy
	@echo "✓ Dev dependencies installed"

run: ## Run the application
	@echo "🚀 Starting GPU Market Service..."
	./run.sh

dev: ## Run in development mode with auto-reload
	@echo "🔧 Starting development server..."
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

scrape: ## Run data scraping pipeline
	@echo "🕷️  Starting scraper..."
	python -m ingest.pipeline

test: ## Run tests
	@echo "🧪 Running tests..."
	pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	pytest tests/ --cov=. --cov-report=html --cov-report=term

lint: ## Run code linting
	@echo "🔍 Running linters..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	black --check .

format: ## Format code with black
	@echo "✨ Formatting code..."
	black .

clean: ## Clean up backend temporary files
	@echo "🧹 Cleaning backend..."
	find . -path ./frontend -prune -o -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -path ./frontend -prune -o -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -path ./frontend -prune -o -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -path ./frontend -prune -o -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -path ./frontend -prune -o -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	@echo "✓ Backend cleanup complete"

backup: ## Create backup
	@echo "💾 Creating backup..."
	bash scripts/backup.sh

health: ## Check service health
	@echo "🏥 Checking service health..."
	bash scripts/health_check.sh

logs: ## Show backend logs (tail -f)
	@echo "📄 Showing backend logs (Ctrl+C to exit)..."
	tail -f logs/gpu_service.log 2>/dev/null || tail -f logs/backend.log

logs-frontend: ## Show frontend logs
	@echo "📄 Showing frontend logs..."
	tail -f logs/frontend.log 2>/dev/null || echo "No frontend logs found"

logs-all: ## Show all logs
	@echo "📄 Showing all logs (Ctrl+C to exit)..."
	tail -f logs/*.log

logs-error: ## Show error logs
	@echo "📄 Showing error logs..."
	grep -i "error\|exception\|critical" logs/gpu_service.log | tail -50

docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t gpu-market:latest .

docker-run: ## Run with Docker Compose
	@echo "🐳 Starting with Docker Compose..."
	docker-compose -f docker-compose.production.yml up -d

docker-stop: ## Stop Docker containers
	@echo "🐳 Stopping containers..."
	docker-compose -f docker-compose.production.yml down

docker-logs: ## Show Docker logs
	@echo "📄 Showing Docker logs..."
	docker-compose -f docker-compose.production.yml logs -f

deploy: ## Deploy to production
	@echo "🚀 Deploying to production..."
	@echo "⚠️  Make sure you have configured .env.production"
	@read -p "Continue? [y/N] " ans; \
	if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ]; then \
		bash deploy.sh; \
	else \
		echo "Deployment cancelled"; \
	fi

service-status: ## Show systemd service status (production)
	@echo "📊 Systemd Service Status:"
	@echo ""
	@systemctl status gpu-market.service --no-pager || echo "Service not installed"

restart: ## Restart service
	@echo "🔄 Restarting service..."
	@systemctl restart gpu-market.service || echo "Service not installed"

update: ## Pull latest code and restart
	@echo "🔄 Updating application..."
	git pull origin main
	pip install -r requirements.txt
	@make restart

db-reset: ## Reset database (WARNING: deletes all data!)
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " ans; \
	if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ]; then \
		python scripts/reset_db.py; \
		echo "✓ Database reset complete"; \
	else \
		echo "Operation cancelled"; \
	fi

# ═══════════════════════════════════════════
# 🚀 FULL STACK COMMANDS
# ═══════════════════════════════════════════

start: ## Start EVERYTHING (API + Frontend + Redis + Celery + Tor + Scraper)
	@echo "🚀 Starting Complete Stack..."
	@./start-all.sh

start-all: ## Alias for 'start' - Start complete stack
	@make start

stop: ## Stop all services
	@echo "🛑 Stopping all services..."
	@./stop.sh

status: ## Check status of all services
	@./status.sh

full-install: ## Install all dependencies (Backend + Frontend)
	@echo "📦 Installing all dependencies..."
	@echo ""
	@echo "1️⃣  Backend dependencies..."
	@make install
	@echo ""
	@echo "2️⃣  Frontend dependencies..."
	@make frontend-install
	@echo ""
	@echo "✓ All dependencies installed!"

full-clean: ## Clean all build artifacts (Backend + Frontend)
	@echo "🧹 Cleaning all artifacts..."
	@make clean
	@make frontend-clean
	@echo "✓ Cleanup complete!"

# ═══════════════════════════════════════════
# 🎨 FRONTEND COMMANDS
# ═══════════════════════════════════════════

frontend-install: ## Install frontend dependencies
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✓ Frontend dependencies installed"

frontend-dev: ## Run frontend in development mode
	@echo "🎨 Starting frontend dev server..."
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	@echo "🏗️  Building frontend..."
	cd frontend && npm run build
	@echo "✓ Frontend built to frontend/dist/"

frontend-preview: ## Preview production build
	@echo "👀 Starting preview server..."
	cd frontend && npm run preview

frontend-test: ## Run frontend tests
	@echo "🧪 Running frontend tests..."
	cd frontend && npm run test || echo "No tests configured yet"

frontend-lint: ## Lint frontend code
	@echo "🔍 Linting frontend..."
	cd frontend && npm run lint || echo "ESLint not configured"

frontend-clean: ## Clean frontend build artifacts
	@echo "🧹 Cleaning frontend..."
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.vite
	@echo "✓ Frontend cleanup complete"

# ═══════════════════════════════════════════
# 🐍 BACKEND COMMANDS (Original)
# ═══════════════════════════════════════════

init: ## Initialize project (first time setup)
	@echo "🎬 Initializing GPU Market Service..."
	@echo ""
	@echo "1️⃣  Creating directories..."
	mkdir -p logs backups data frontend
	@echo "2️⃣  Copying environment templates..."
	cp .env.example .env || true
	cd frontend && cp .env.example .env || true
	@echo "3️⃣  Installing backend dependencies..."
	@make install
	@echo "4️⃣  Installing frontend dependencies..."
	@make frontend-install
	@echo "5️⃣  Creating database..."
	python -c "from storage.db import init_db; init_db()" || echo "DB already exists"
	@echo ""
	@echo "✓ Initialization complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env files (backend and frontend/.env)"
	@echo "  2. Run 'make scrape' to collect initial data"
	@echo "  3. Run 'make start' to start the full stack"