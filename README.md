# 🎮 GPU Market Service

> **Production-ready** система за анализ и мониторинг на цени на видео карти в България

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=github-actions)](https://github.com/C00Ling/gpu_price_tracker/actions)
[![Tests](https://img.shields.io/badge/tests-93%25%20passing-success)](https://github.com/C00Ling/gpu_price_tracker/actions)
[![Coverage](https://img.shields.io/badge/coverage-62%25-yellow)](https://codecov.io)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker)](https://hub.docker.com)

---

## 📋 Съдържание

- [Features](#-features)
- [Архитектура](#-архитектура)
- [Инсталация](#-инсталация)
- [Конфигурация](#-конфигурация)
- [Стартиране](#-стартиране)
- [API Документация](#-api-документация)
- [Dashboard](#-dashboard)
- [Структура на проекта](#-структура-на-проекта)
- [Security](#-security)
- [Development](#-development)
- [Deployment](#-deployment)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)

---

## 🚀 Features

### Core Features
- ✅ **Intelligent Web Scraping** - Single-pass scraping с TOR защита
- ✅ **Post-Processing Filtering** - Statistical outlier detection след scraping
- ✅ **Smart Quality Control** - Премахване на счупени, mining и overpriced карти
- ✅ **FPS per лв Analysis** - Изчисляване на най-добра стойност (min price)
- ✅ **RESTful API** - FastAPI с автоматична документация
- ✅ **Modern React Frontend** - Professional SPA с TypeScript, TailwindCSS и React Query
- ✅ **WebSocket Real-time Updates** - Live data synchronization
- ✅ **SQLite Database** - Лесно преносима база данни

### Technical Features
- 🔧 **Rate Limiting** - Token bucket algorithm за control на заявки
- 🔧 **Retry Mechanism** - Exponential backoff при грешки
- 🔧 **Structured Logging** - Log rotation и цветен console output
- 🔧 **Error Handling** - Comprehensive error handling на всички нива
- 🔧 **Error Monitoring** - Sentry integration за production error tracking
- 🔧 **Input Validation** - Pydantic models за валидация
- 🔧 **Repository Pattern** - Clean architecture за database layer
- 🔧 **Environment Variables** - Гъвкава конфигурация
- 🔧 **Health Checks** - Monitoring endpoints

### Data Sources
- 📊 **OLX.bg** - GPU listings (основен източник на данни за цени)
- 📊 **Tom's Hardware GPU Hierarchy 2025** - 1080p raster performance benchmarks (96 GPU models)
- 📊 **Future**: Pazaruvaj.com, Technomarket, etc.

---

## 🏗️ Архитектура

### Professional Multi-Service Architecture

Системата използва **модерна multi-service архитектура** с разделени API и Scraper services за независимо scaling и deployment.

```
┌─────────────────────────────────────────────────────────────┐
│                  GPU Price Tracker System                   │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  API Service │    │   Scraper    │    │  PostgreSQL  │
│  (HTTP)      │    │   Worker     │    │   Database   │
│  Read-Only   │    │  (Daemon)    │    │              │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                    │
       │                   │                    │
       └───────────────────┴────────────────────┘
              Shared Database Connection
```

**Services:**
- **API Service** - Read-only HTTP server (FastAPI + Uvicorn)
- **Scraper Worker** - Autonomous background worker (TOR + BeautifulSoup)
- **PostgreSQL** - Centralized persistent storage
- **Shared Libraries** - Common code (core, api, storage, ingest)

**Benefits:**
- ✅ Independent scaling (API horizontal, Scraper fixed at 1)
- ✅ Fault isolation (API crash doesn't stop scraping)
- ✅ Graceful shutdown (no data loss)
- ✅ Production-ready monitoring and health checks

📚 **Detailed Architecture Documentation:** [ARCHITECTURE.md](ARCHITECTURE.md)

### Data Flow

1. **Collection Phase** (adaptive single-pass scraping):
   ```
   SINGLE PASS with Adaptive Filtering:
   ├─ Warm-up Phase (first 5 listings/model): Basic filters only
   └─ Statistical Phase (5+ listings/model): Full outlier detection
   → Save to database
   ```
   *Previously used a two-pass approach, now optimized to single pass*

2. **Processing Phase**:
   ```
   Raw Data → Validation → Model Extraction → Price Stats → Value Analysis
   ```

3. **API Phase**:
   ```
   Database → Repository → API Endpoints → JSON Response
   ```

---

## 📦 Инсталация

### Системни изисквания

- **Python**: 3.8 или по-нова версия
- **TOR**: За анонимен scraping
- **pip**: Package manager
- **Git**: Version control

### Стъпка 1: Клониране на проекта

```bash
git clone https://github.com/C00Ling/gpu_price_tracker.git
cd gpu_price_tracker
```

### Стъпка 2: Virtual Environment

```bash
# Създаване на virtual environment
python -m venv venv

# Активиране
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### Стъпка 3: Инсталиране на зависимости

```bash
pip install -r requirements.txt
```

### Стъпка 4: Database Setup

```bash
# Инициализирай базата данни с Alembic migrations
alembic upgrade head
```

Това ще създаде SQLite база данни (`gpu.db`) с правилната схема.

### Стъпка 5: TOR инсталация

#### Arch Linux / CachyOS
```bash
sudo pacman -S tor
sudo systemctl enable tor
sudo systemctl start tor
```

#### Ubuntu / Debian
```bash
sudo apt update
sudo apt install tor
sudo systemctl enable tor
sudo systemctl start tor
```

#### macOS (Homebrew)
```bash
brew install tor
brew services start tor
```

#### Windows
1. Изтегли [Tor Expert Bundle](https://www.torproject.org/download/tor/)
2. Разархивирай и стартирай `tor.exe`

### Стъпка 6: Проверка на TOR

```bash
# Провери дали TOR работи
curl --socks5 localhost:9050 https://check.torproject.org/api/ip

# Очакван резултат: {"IsTor":true,"IP":"xxx.xxx.xxx.xxx"}
```

---

## ⚙️ Конфигурация

### Environment Variables

1. **Копирай template файла:**
```bash
cp .env.example .env
```

2. **Генерирай SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

3. **Редактирай `.env` с твоите настройки:**
```bash
nano .env  # или vim, code, etc.
```

### Основни настройки

#### Database
```bash
DATABASE_URL=sqlite:///./gpu.db  # За development
# DATABASE_URL=postgresql://user:pass@localhost/gpu  # За production
```

#### API Server
```bash
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true  # false за production
```

#### Scraper
```bash
SCRAPER_MAX_PAGES=3
SCRAPER_USE_TOR=true
SCRAPER_RATE_LIMIT_REQUESTS_PER_MINUTE=10
```

#### Logging
```bash
LOGGING_LEVEL=INFO  # DEBUG за development
LOGGING_FILE=logs/gpu_service.log
```

### Config.yaml

Алтернативно, можеш да използваш `config.yaml` за конфигурация.
**Важно:** Environment variables имат приоритет над config.yaml!

---

## 🏃 Стартиране

### Multi-Service Architecture (Препоръчително)

#### Docker Compose - Стартиране на всички services

```bash
# Стартирай PostgreSQL + API + Scraper
docker-compose up -d

# Провери статуса
docker-compose ps

# Виж logs
docker-compose logs -f api      # API logs
docker-compose logs -f scraper  # Scraper logs

# Спри всички services
docker-compose down
```

**Какво се случва:**
- ✅ PostgreSQL стартира на `localhost:5432`
- ✅ API стартира на `http://localhost:8000`
- ✅ Scraper worker стартира в daemon mode (scrape every 1 hour)
- ✅ TOR proxy се инициализира автоматично
- ✅ Database migrations се прилагат автоматично

**Достъп:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: `psql postgresql://postgres:postgres@localhost:5432/gpu_tracker`

#### Ръчно стартиране на отделни services

**API Service:**
```bash
cd services/api
pip install -r requirements.txt
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/gpu_tracker"
./start.sh
```

**Scraper Worker:**
```bash
cd services/scraper
pip install -r requirements.txt
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/gpu_tracker"
export WORKER_MODE=oneshot  # или daemon
./start.sh
```

### Legacy Monolith (Deprecated)

```bash
chmod +x run.sh
./run.sh
```

**Бележка:** Монолитната версия е deprecated. Използвай multi-service architecture!

---

## 📡 API Документация

### Base URL
```
http://localhost:8000
```

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API информация |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc документация |
| GET | `/dashboard` | Interactive dashboard |

### 📋 Listings Endpoints

#### Get all listings
```http
GET /api/listings/
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `size` (int): Page size (default: 100, max: 1000)

**Response:**
```json
[
  {
    "id": 1,
    "model": "RTX 4070",
    "price": 1299.0,
    "source": "OLX"
  }
]
```

#### Get listings by model
```http
GET /api/listings/{model}
```

**Example:**
```bash
curl http://localhost:8000/api/listings/RTX%204070
```

#### Get total count
```http
GET /api/listings/count/total
```

**Response:**
```json
{
  "total": 157
}
```

#### Get available models
```http
GET /api/listings/models/list
```

**Response:**
```json
{
  "models": ["RTX 4090", "RTX 4070", "RX 7900 XTX"],
  "count": 28
}
```

### 📊 Statistics Endpoints

#### Get all statistics
```http
GET /api/stats/
```

**Response:**
```json
{
  "RTX 4070": {
    "min": 1199.0,
    "max": 1899.0,
    "median": 1299.0,
    "mean": 1350.5,
    "count": 15,
    "percentile_25": 1250.0
  }
}
```

#### Get statistics for specific model
```http
GET /api/stats/{model}
```

### 💎 Value Analysis Endpoints

#### Get all GPUs sorted by FPS/лв
```http
GET /api/value/
```

**Response:**
```json
[
  {
    "model": "RX 6600",
    "fps": 75.0,
    "price": 350.0,
    "fps_per_lv": 0.214
  }
]
```

#### Get top N best value GPUs
```http
GET /api/value/top/{n}
```

**Example:**
```bash
curl http://localhost:8000/api/value/top/10
```

### 🏥 System Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "Service is running",
  "database": "connected",
  "models_available": 28
}
```

---

## 🎨 Frontend Application

### Tech Stack
- **React 18** + TypeScript - Modern UI framework
- **Vite** - Lightning-fast build tool
- **TailwindCSS v4** - Utility-first styling
- **React Query** - Server state management с intelligent caching
- **React Router v6** - Client-side routing
- **Zustand** - Lightweight state management
- **WebSocket** - Real-time data updates

### Достъп
```bash
# Development
http://localhost:5173

# Production (след build)
http://localhost:8000
```

### Страници

**🏠 Home Dashboard** (`/`)
- Summary statistics (обяви, модели, цени)
- Топ 5 GPU по стойност (FPS/лв)
- Quick navigation към всички секции

**📋 Listings** (`/listings`)
- Всички обяви с търсене и филтри
- Sortable таблица по модел, цена, дата
- Filter по GPU модел
- Pagination support

**💎 Value Analysis** (`/value`)
- Класиране по FPS/лв ефективност
- Цветно кодирани резултати:
  - 🟢 Отлична стойност (≥ 0.5)
  - 🔵 Добра стойност (≥ 0.3)
  - 🟡 Средна стойност (≥ 0.2)
- Sortable по всички колони

**ℹ️ About** (`/about`)
- Методология и документация
- API endpoints
- Технологичен стек
- Контакти

### Features

- ✨ **Responsive Design** - Mobile-first approach
- ⚡ **Performance** - React Query caching (5-10 min TTL)
- 🔄 **Real-time Updates** - WebSocket integration
- 🎨 **Modern UI** - TailwindCSS с custom theme
- 🔍 **Search & Filter** - Instant filtering and sorting
- ⌨️ **TypeScript** - Full type safety
- 🚀 **Fast** - Vite HMR за instant feedback
- 📊 **Data Visualization** - Recharts integration (planned)

### Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Create `frontend/.env`:

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_APP_NAME=GPU Market
VITE_APP_VERSION=1.2.0
```

### Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   │   ├── Card.tsx
│   │   ├── Button.tsx
│   │   ├── Table.tsx
│   │   ├── Navbar.tsx
│   │   ├── Loading.tsx
│   │   └── ErrorBoundary.tsx
│   ├── pages/          # Page components
│   │   ├── Home.tsx
│   │   ├── Listings.tsx
│   │   ├── ValueAnalysis.tsx
│   │   └── About.tsx
│   ├── hooks/          # Custom React hooks
│   │   ├── useGPUData.ts
│   │   └── useWebSocket.ts
│   ├── services/       # API communication
│   │   └── api.ts
│   ├── lib/            # Configuration
│   │   ├── config.ts
│   │   └── queryClient.ts
│   ├── types/          # TypeScript types
│   │   └── index.ts
│   └── store/          # State management
├── public/
├── index.html
├── vite.config.ts
├── tailwind.config.js
└── package.json
```

### Custom Hooks

```typescript
// Data fetching hooks with React Query
useListings()           // Fetch all GPU listings
useListingsByModel()    // Filter by model
useSummaryStats()       // Summary statistics
useValueAnalysis()      // FPS/лв ranking
useTopValue(n)         // Top N by value

// WebSocket hook with auto-reconnect
useWebSocket({
  onMessage: (msg) => { /* handle updates */ },
  reconnect: true,
  maxReconnectAttempts: 5
})
```

---

## 🗂️ Структура на проекта

### Multi-Service Architecture

```
GPU_PRICE_TRACKER/
│
├── 📄 docker-compose.yml      # Multi-service local development
├── 📄 README.md               # Main documentation
├── 📄 ARCHITECTURE.md         # Architecture documentation
├── 📄 .gitignore              # Git ignore rules
│
├── 📁 services/               # ⭐ Multi-Service Architecture
│   │
│   ├── 📁 api/                # API Service (Read-Only HTTP Server)
│   │   ├── 📄 main.py         # FastAPI application
│   │   ├── 📄 Dockerfile      # API container build
│   │   ├── 📄 start.sh        # Startup script with DB checks
│   │   ├── 📄 requirements.txt # HTTP server dependencies
│   │   └── 📄 .dockerignore   # Docker build optimization
│   │
│   ├── 📁 scraper/            # Scraper Worker (Background Worker)
│   │   ├── 📄 worker.py       # Worker with 3 modes (daemon/oneshot/cron)
│   │   ├── 📄 Dockerfile      # Scraper container (TOR + Python)
│   │   ├── 📄 start.sh        # TOR init + worker startup
│   │   ├── 📄 requirements.txt # Scraping dependencies
│   │   ├── 📄 crontab         # Cron schedule config
│   │   └── 📄 .dockerignore   # Docker build optimization
│   │
│   └── 📁 shared/             # Shared Code (both services use this)
│       ├── 📁 api/            # API routes and schemas
│       │   ├── routers/       # FastAPI endpoints
│       │   │   ├── listings.py
│       │   │   ├── stats.py
│       │   │   └── value.py
│       │   └── dependencies.py
│       │
│       ├── 📁 core/           # Business logic
│       │   ├── config.py      # Configuration manager
│       │   ├── logging.py     # Structured logging
│       │   ├── sentry.py      # Error monitoring
│       │   ├── filters.py     # Quality filters
│       │   ├── resolver.py    # GPU model extraction
│       │   ├── stats.py       # Statistics
│       │   └── value.py       # FPS/лв analysis
│       │
│       ├── 📁 ingest/         # Data collection
│       │   ├── pipeline.py    # Scraping pipeline
│       │   └── scraper.py     # Web scraper
│       │
│       └── 📁 storage/        # Database layer
│           ├── db.py          # SQLAlchemy setup
│           ├── models.py      # ORM models (PostgreSQL)
│           └── repo.py        # Repository pattern
│
├── 📁 deployments/            # Deployment Configurations
│   └── 📁 railway/            # Railway.app deployment
│       ├── 📄 README.md       # Complete Railway guide
│       ├── 📄 railway.api.toml
│       └── 📄 railway.scraper.toml
│
├── 📁 frontend/               # React Frontend (SPA)
│   ├── 📁 src/
│   │   ├── pages/             # React pages
│   │   ├── components/        # UI components
│   │   ├── hooks/             # Custom hooks
│   │   └── services/          # API client
│   ├── 📄 package.json
│   ├── 📄 vite.config.ts
│   └── 📄 tailwind.config.js
│
├── 📁 tests/                  # Unit & Integration Tests
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_filters.py
│   ├── test_scraper.py
│   └── test_sentry.py
│
├── 📁 alembic/                # Database Migrations
│   ├── versions/              # Migration files
│   ├── env.py
│   └── script.py.mako
│
├── 📄 alembic.ini             # Alembic configuration
├── 📄 main.py                 # Legacy monolith (deprecated)
├── 📄 requirements.txt        # Legacy dependencies (deprecated)
└── 📄 run.sh                  # Legacy startup (deprecated)
```

### Key Directories

#### Multi-Service Architecture (New)
- **`services/api/`** - HTTP API server (FastAPI, read-only)
- **`services/scraper/`** - Background worker (TOR, scraping)
- **`services/shared/`** - Shared code (core, api, storage, ingest)
- **`deployments/railway/`** - Railway deployment configs

#### Supporting Directories
- **`frontend/`** - React SPA (TypeScript, Vite, TailwindCSS)
- **`tests/`** - Unit and integration tests
- **`alembic/`** - Database migrations

#### Legacy (Deprecated)
- **`main.py`** - Old monolithic application (use `services/api/` instead)
- **`api/`, `core/`, `ingest/`, `storage/`** - Moved to `services/shared/`

📚 **Migration Guide:** Старият монолит е deprecated. Използвай `docker-compose up` за новата multi-service архитектура!

---

## 🔒 Security

### Implemented Security Measures

✅ **Input Validation**
- Pydantic models за всички API inputs
- Custom validators за model names, prices
- SQL injection prevention чрез ORM

✅ **Rate Limiting**
- Token bucket algorithm
- Configurable limits per endpoint

✅ **Error Handling**
- No sensitive data leak в error messages
- Structured logging за audit trail

✅ **CORS Configuration**
- Configurable allowed origins
- Credentials support

✅ **Environment Variables**
- Sensitive data не се hard-code-ват
- .env файл не се commit-ва

### Security Best Practices

#### Development
```bash
# .env
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key
```

#### Production
```bash
# .env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<strong-random-key>
API_CORS_ORIGINS=https://yourdomain.com
```

#### Генериране на SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📊 Monitoring & Error Tracking

### Sentry Error Monitoring

Проектът има built-in **Sentry** integration за production error tracking и performance monitoring.

#### Setup

1. **Създай Sentry проект:**
   - Отиди на [sentry.io](https://sentry.io/)
   - Създай нов проект (тип: Python/FastAPI)
   - Копирай DSN от Settings → Client Keys

2. **Конфигурирай в `.env`:**
   ```bash
   # Sentry Error Tracking (Recommended for Production)
   SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
   SENTRY_ENVIRONMENT=production
   RELEASE=v1.0.0  # или git commit hash
   ```

3. **Стартирай приложението:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

Sentry ще автоматично:
- ✅ Capture всички unhandled exceptions
- ✅ Track API errors с request context (endpoint, method, params)
- ✅ Monitor scraper errors с additional context
- ✅ Integrate с FastAPI и SQLAlchemy
- ✅ Filter out expected errors (404, 401, DB warmup errors)

#### Features

**Automatic Error Capture:**
```python
# API errors са automatically captured в global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Автоматично изпраща към Sentry с request context
    capture_api_error(exc, endpoint=request.url.path, context={...})
```

**Custom Error Capture:**
```python
from core.sentry import capture_scraper_error, capture_api_error

# Scraper errors
capture_scraper_error(error, context={
    "page": 5,
    "search_term": "rtx 4090"
})

# API errors
capture_api_error(error, endpoint="/api/stats", context={
    "model": "RTX 4090"
})
```

**Event Filtering:**
- ✅ Expected client errors (404, 401, 403) are filtered out
- ✅ Database warmup errors (connection refused) are filtered out
- ✅ Only real errors reach Sentry (reduced noise)

**Performance Monitoring:**
```bash
# Development: 100% performance sampling
SENTRY_ENVIRONMENT=development

# Production: 10% performance sampling (cost optimization)
SENTRY_ENVIRONMENT=production
```

**Privacy & Security:**
```python
# PII (Personally Identifiable Information) is NOT sent by default
send_default_pii=False

# Sample rate: 100% error capture (all errors)
sample_rate=1.0

# Traces sample rate: 10% in production (performance monitoring)
traces_sample_rate=0.1
```

#### Testing

```bash
# Run Sentry integration tests
pytest tests/test_sentry.py -v

# Test error capture manually (visit this endpoint)
# http://localhost:8000/test-error
```

#### Monitoring Dashboard

След setup, можеш да:
- 📊 View error trends и frequency
- 🔍 Inspect stack traces с source code
- 📈 Monitor API performance
- 🔔 Setup alerts за critical errors
- 📧 Get email notifications

#### Cost

**Sentry Pricing:**
- **Developer Plan**: Free (5,000 errors/месец)
- **Team Plan**: $26/месец (50,000 errors/месец)

За този проект, Developer планът е **напълно достатъчен**.

#### Без Sentry

Ако не конфигурираш `SENTRY_DSN`, приложението ще работи нормално:
```
⚠️  Sentry DSN not configured - error monitoring disabled
```

Errors ще се логват само локално в `logs/gpu_service.log`.

---

## 🛠️ Development

### Setup Development Environment

```bash
# 1. Clone и setup
git clone <repo>
cd gpu_service
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env
# Edit .env with your settings

# 4. Start TOR
sudo systemctl start tor

# 5. Run tests
pytest

# 6. Start development server
uvicorn main:app --reload
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run with output
pytest -s
```

### Code Quality

```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

### Database Operations

#### Database Migrations с Alembic

Проектът използва [Alembic](https://alembic.sqlalchemy.org/) за управление на database schema changes.

**Първоначална инсталация:**
```bash
# Приложи всички migrations
alembic upgrade head
```

**Проверка на текуща версия:**
```bash
alembic current
```

**Създаване на нов migration (след промяна в models):**
```bash
# Autogenerate migration от промените в ORM models
alembic revision --autogenerate -m "Description of changes"

# Прегледай генерирания файл в alembic/versions/
# Провери дали промените са правилни

# Приложи migration
alembic upgrade head
```

**Migration история:**
```bash
# Покажи всички migrations
alembic history

# Покажи verbose информация
alembic history --verbose
```

**Rollback (downgrade):**
```bash
# Rollback до предишна версия
alembic downgrade -1

# Rollback до конкретна версия
alembic downgrade <revision_id>

# Rollback всичко (ВНИМАНИЕ: Изтрива всички данни!)
alembic downgrade base
```

**Важни бележки:**
- ⚠️ Винаги прави backup на базата данни преди migration в production!
- ⚠️ Прегледай auto-generated migrations преди да ги приложиш
- ⚠️ Test migrations с upgrade/downgrade преди production deployment
- ✅ Migrations се commit-ват в Git (alembic/versions/*.py)
- ✅ Database файлът (gpu.db) НЕ се commit-ва

#### Reset Database
```bash
python scripts/reset_db.py
```

#### Manual Database Operations
```python
from storage.db import SessionLocal, init_db
from storage.repo import GPURepository

# Initialize (legacy метод - използвай Alembic вместо това!)
init_db()

# Use repository
session = SessionLocal()
repo = GPURepository(session)

# Operations
listings = repo.get_all_listings()
stats = repo.get_price_stats("RTX 4070")

# Cleanup
session.close()
```

---

## 🚀 Deployment

Проектът използва **production-ready multi-service architecture** готова за deployment.

### 🎯 Quick Start - Railway (5 minutes)

**Railway multi-service deployment** е най-бързият начин за production deployment:

```bash
# 1. Push към GitHub
git push origin main

# 2. Login to Railway
railway login

# 3. Create project
railway init

# 4. Add PostgreSQL
# Railway Dashboard → New Service → Database → PostgreSQL

# 5. Deploy API Service
# New Service → GitHub Repo → services/api/
# Set env vars: DATABASE_URL, ENVIRONMENT=production

# 6. Deploy Scraper Worker
# New Service → GitHub Repo → services/scraper/
# Set env vars: DATABASE_URL, WORKER_MODE=daemon

# 7. Generate domain for API
# API Settings → Networking → Generate Domain

# ✅ Done! System is live!
```

**Architecture:**
```
Railway Project
├─ PostgreSQL Database (managed)
├─ API Service (1-3 replicas, auto-scaling)
└─ Scraper Worker (1 replica, daemon mode)
```

**Cost:** $0-5/month with $5 free credit

📚 **Complete Railway Guide:** [deployments/railway/README.md](deployments/railway/README.md)

### 📚 Deployment Options

#### Option 1: Railway (Recommended)
- ✅ **Setup time:** 5 minutes
- ✅ **Cost:** $0-5/month
- ✅ **Auto-scaling:** Yes (API service)
- ✅ **Managed DB:** PostgreSQL included
- ✅ **SSL:** Automatic HTTPS
- 📖 **Guide:** [deployments/railway/README.md](deployments/railway/README.md)

#### Option 2: Docker Compose
- ✅ **Setup time:** 2 minutes
- ✅ **Cost:** Free (self-hosted)
- ✅ **Flexibility:** Full control
- ⚠️ **Requires:** Docker + Docker Compose
- 📖 **Guide:** [docker-compose.yml](docker-compose.yml)

```bash
# Start all services (PostgreSQL + API + Scraper)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

#### Option 3: VPS Deployment
- ✅ **Setup time:** 30 minutes
- ✅ **Cost:** €4-6/month (Hetzner/DigitalOcean)
- ✅ **Control:** Complete infrastructure control
- ⚠️ **Requires:** Linux server administration skills
- 📖 **Guide:** [DEPLOYMENT_VPS.md](DEPLOYMENT_VPS.md)

#### Option 4: Kubernetes (Advanced)
- ✅ **Setup time:** 1-2 hours
- ✅ **Cost:** Varies
- ✅ **Scaling:** Advanced horizontal scaling
- ⚠️ **Complexity:** High
- 📖 **Guide:** Contact for enterprise deployment

### 💰 Cost Comparison

| Platform | Monthly Cost | Setup Time | Scaling | Managed DB |
|----------|--------------|------------|---------|------------|
| Railway | $0-5 | 5 min | Auto | ✅ Yes |
| Hetzner VPS | €4 | 30 min | Manual | ❌ No |
| DigitalOcean | $6 | 15 min | Manual | ✅ Optional |
| Docker (Local) | Free | 2 min | No | Self-hosted |

### 🔧 Multi-Service Architecture

**Services:**
- **API Service** - HTTP server (FastAPI), scales 1-3 replicas
- **Scraper Worker** - Background worker (TOR), fixed 1 replica
- **PostgreSQL** - Database, managed or self-hosted

**Benefits:**
- Independent scaling and deployment
- Fault isolation (service crashes don't affect others)
- Graceful shutdown (no data loss)
- Production monitoring and health checks

📚 **Architecture Details:** [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🔄 CI/CD Pipeline

Проектът използва **GitHub Actions** за автоматизация на testing, quality control, security scanning и deployment.

### Workflows

**CI Pipeline** ([.github/workflows/ci.yml](.github/workflows/ci.yml)):
- ✅ Automated testing на Python 3.11 и 3.12
- ✅ Code coverage tracking (минимум 60%)
- ✅ Linting с Black, isort, flake8
- ✅ Security scanning с Bandit и Safety
- ✅ Docker build validation
- ✅ Daily scheduled runs (02:00 UTC)

**Deployment Pipeline** ([.github/workflows/deploy.yml](.github/workflows/deploy.yml)):
- ✅ Integration testing с PostgreSQL и Redis
- ✅ Docker build и push към GitHub Container Registry
- ✅ Automated deployment към VPS
- ✅ Database migrations
- ✅ Health checks
- ✅ Slack notifications

### Triggers

- **Push/PR** към `main` или `develop` → Full CI pipeline
- **Push към `production`** → Full deployment pipeline
- **Daily at 02:00 UTC** → Scheduled test run

### Quick Start

```bash
# Локално пускане на CI проверки
pytest tests/ --cov=. --cov-report=term -v
black --check .
isort --check-only .
flake8 . --max-line-length=127
bandit -r . -ll

# Docker build test
docker build -t gpu-price-tracker:test .
```

📚 **Пълна документация:** [docs/CI_CD.md](docs/CI_CD.md)

---

## 🐛 Troubleshooting

### TOR не работи

**Симптоми:** Connection errors, timeout

**Решение:**
```bash
# 1. Провери статус
sudo systemctl status tor

# 2. Рестартирай
sudo systemctl restart tor

# 3. Провери connectivity
curl --socks5 localhost:9050 https://check.torproject.org/api/ip

# 4. Виж logs
sudo journalctl -u tor -f
```

### Database грешки

**Симптоми:** Database locked, schema errors

**Решение:**
```bash
# 1. Нулирай базата
python scripts/reset_db.py

# 2. Ръчно пресъздай таблиците
python -c "from storage.db import init_db; init_db()"

# 3. Провери permissions
ls -la gpu.db
```

### Port е зает

**Симптоми:** Address already in use

**Решение:**
```bash
# 1. Намери процеса
lsof -i :8000
# или
ss -tlnp | grep 8000

# 2. Убий процеса
kill -9 <PID>

# 3. Стартирай отново
./run.sh
```

### Scraping errors

**Симптоми:** No data collected, timeout errors

**Решение:**
```bash
# 1. Провери TOR
curl --socks5 localhost:9050 https://check.torproject.org/api/ip

# 2. Увеличи timeout в .env
SCRAPER_TIMEOUT=30

# 3. Намали rate limit
SCRAPER_RATE_LIMIT_REQUESTS_PER_MINUTE=5

# 4. Виж logs
tail -f logs/gpu_service.log
```

### Memory issues

**Симптоми:** High memory usage, slow performance

**Решение:**
```bash
# 1. Провери memory
free -h

# 2. Намали page size
SCRAPER_MAX_PAGES=1

# 3. Clear old data
python -c "from storage.repo import GPURepository; from storage.db import SessionLocal; repo = GPURepository(SessionLocal()); repo.clear_listings()"
```

---

## 🗺️ Roadmap

### Version 1.1 (Q1 2026) ✅ **COMPLETED**
- [x] Docker containerization ✅ **COMPLETED**
- [x] Database migrations с Alembic ✅ **COMPLETED**
- [x] Test suite (93% passing, 62% coverage) ✅ **COMPLETED**
- [x] CI/CD pipeline (GitHub Actions) ✅ **COMPLETED**
- [ ] Improve test coverage (stretch goal: 80%+)

### Version 1.2 (Q2 2026) ✅ **COMPLETED**
- [x] Redis caching layer ✅ **COMPLETED**
- [x] WebSocket support за real-time updates ✅ **COMPLETED**
- [x] Scheduled automatic scraping (Celery) ✅ **COMPLETED**
- [x] Email/Telegram notifications за price drops ✅ **COMPLETED**

### Version 1.3 (Q3 2026)
- [ ] Additional data sources (Pazaruvaj.com, etc.)
- [ ] External benchmark API integration
- [ ] GraphQL API
- [ ] Advanced filtering options

### Version 2.0 (Q4 2026)
- [ ] User authentication & profiles
- [ ] Wishlist functionality
- [ ] Price history tracking
- [ ] Machine learning price predictions
- [ ] Mobile app (React Native)

---

## 🤝 Contributing

Contributions are welcome! Следвай тези стъпки:

### 1. Fork the Project
```bash
git clone https://github.com/C00Ling/gpu_price_tracker.git
```

### 2. Create Feature Branch
```bash
git checkout -b feature/AmazingFeature
```

### 3. Make Changes
- Следвай coding style на проекта
- Добави tests за новата functionality
- Update документацията

### 4. Commit Changes
```bash
git commit -m 'Add some AmazingFeature'
```

### 5. Push to Branch
```bash
git push origin feature/AmazingFeature
```

### 6. Open Pull Request

### Coding Guidelines

- **Code Style**: PEP 8
- **Docstrings**: Google style
- **Type Hints**: Mandatory за public functions
- **Tests**: Required за всички нови features
- **Logging**: Use structured logging

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 👤 Author

**C00Ling**

- GitHub: [@C00Ling](https://github.com/C00Ling)
- Project: [GPU Price Tracker](https://github.com/C00Ling/gpu_price_tracker)

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and ORM
- [TOR Project](https://www.torproject.org/) - Anonymity network
- [Chart.js](https://www.chartjs.org/) - Data visualization
- [OLX.bg](https://www.olx.bg/) - Data source
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - Web scraping

---

## 📞 Support

Имаш въпрос или проблем? Отвори [issue](https://github.com/C00Ling/gpu_price_tracker/issues)!

---

<div align="center">
  <strong>Made with ❤️ in Bulgaria</strong>
</div>