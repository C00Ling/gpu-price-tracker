# GPU Price Tracker

> Real-time GPU price monitoring and analysis for the Bulgarian market

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

---

## Features

- **Smart Scraping** - TOR-enabled web scraping with rate limiting and bot detection avoidance
- **Price Analysis** - FPS per lv calculation using benchmark data
- **Quality Filtering** - Automatic rejection of broken/damaged listings
- **REST API** - FastAPI with automatic OpenAPI documentation
- **Real-time Updates** - WebSocket support for live data
- **Modern Frontend** - React + TypeScript + TailwindCSS
- **Multi-service Architecture** - Separate API and scraper services
- **Railway Deployment** - Production-ready deployment configuration

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Node.js 18+ (for frontend)
- TOR (optional, for anonymous scraping)

### 1. Clone & Setup

```bash
git clone https://github.com/C00Ling/gpu-price-tracker.git
cd gpu-price-tracker
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install API dependencies
pip install -r services/api/requirements.txt

# Install scraper dependencies
pip install -r services/scraper/requirements.txt
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb gpu_tracker

# Or configure DATABASE_URL environment variable
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/gpu_tracker"
```

### 4. Start Services

```bash
# Start API server
cd services/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# In another terminal - start scraper worker
cd services/scraper
python worker.py
```

### 5. Access

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173 (when running `npm run dev`)

---

## Architecture

```
gpu-price-tracker/
├── services/
│   ├── api/              # FastAPI REST API service
│   │   ├── main.py       # API entry point
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── scraper/          # Data collection worker
│   │   ├── worker.py     # Scraper entry point
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── shared/           # Shared libraries
│       ├── api/          # API routers and dependencies
│       ├── core/         # Core logic (config, logging, filters, stats)
│       ├── ingest/       # Scraping and data pipeline
│       └── storage/      # Database models and repositories
├── frontend/             # React SPA
├── tests/                # Test suite
├── scripts/              # Utility scripts
├── config.yaml           # Application configuration
└── railway.toml          # Railway deployment config
```

**Services:**

- **API Service** - Read-only HTTP server for frontend and REST API
- **Scraper Worker** - Background data collection with TOR support
- **PostgreSQL** - Primary database
- **Frontend** - React SPA with real-time updates

---

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=services/shared --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

---

## Deployment

### Railway (Recommended)

The project includes a `railway.toml` configuration for multi-service deployment:

- **API Service** (`gpu-tracker-api`) - Exposes the REST API
- **Scraper Service** (`gpu-tracker-scraper`) - Runs in daemon mode

Required environment variables on Railway:
- `DATABASE_URL` - PostgreSQL connection string
- `ENVIRONMENT` - Set to `production`
- `SENTRY_DSN` (optional) - For error tracking

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/listings/` | GET | All GPU listings |
| `/api/stats/` | GET | Price statistics by model |
| `/api/value/` | GET | FPS per lv rankings |
| `/api/rejected/` | GET | Rejected listings (filtered out) |
| `/api/export/` | GET | Export data in various formats |
| `/docs` | GET | Interactive API documentation |

**Query Parameters:**

- `min_vram` - Filter by minimum VRAM (e.g., `?min_vram=8`)
- `max_price` - Filter by maximum price
- `model` - Filter by GPU model

---

## Configuration

Main configuration in `config.yaml`:

```yaml
database:
  url: postgresql://postgres:postgres@localhost:5432/gpu_tracker

scraper:
  max_pages: 100
  use_tor: true
  rate_limit:
    requests_per_minute: 5
    delay_between_pages: 10
```

Override with environment variables:
- `DATABASE_URL` - Database connection string
- `ENVIRONMENT` - `development` or `production`

---

## Security

- **TOR Support** - Anonymous scraping to avoid IP bans
- **Rate Limiting** - Configurable request throttling
- **Quality Filters** - Blacklist keywords for damaged/broken items
- **Environment Variables** - Sensitive data via environment variables
- **Sentry Integration** - Error tracking in production

---

## Testing

The project has comprehensive test coverage:

```bash
pytest tests/ -v
```

Test files include:
- `test_api.py` - API endpoint tests
- `test_scraper.py` - Scraper functionality tests
- `test_filters.py` - Quality filter tests
- `test_pipeline.py` - Data pipeline tests
- `test_storage.py` - Database operations tests

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) file for details

---

## Acknowledgments

- **FastAPI** - Modern Python web framework
- **React** - Frontend framework
- **TailwindCSS** - Utility-first CSS framework

---

**Made for the Bulgarian GPU market**
