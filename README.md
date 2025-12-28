# 🎮 GPU Price Tracker

> Real-time GPU price monitoring and analysis for the Bulgarian market

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker)](https://www.docker.com/)

---

## 🚀 Features

- **Smart Scraping** - TOR-enabled web scraping with rate limiting
- **Price Analysis** - FPS per лв calculation using HowManyFPS benchmarks
- **REST API** - FastAPI with automatic OpenAPI documentation
- **Real-time Updates** - WebSocket support for live data
- **Modern Frontend** - React + TypeScript + TailwindCSS
- **Multi-service Architecture** - Separate API and scraper services

---

## 📦 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend)

### 1. Clone & Setup

```bash
git clone https://github.com/C00Ling/gpu-price-tracker.git
cd gpu-price-tracker
```

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# Or start individually
docker-compose up -d postgres  # Database
docker-compose up -d api       # API service
docker-compose up -d scraper   # Scraper worker
```

### 4. Access

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173

---

## 🏗️ Architecture

```
gpu-price-tracker/
├── services/
│   ├── api/              # FastAPI REST API (read-only)
│   ├── scraper/          # Data collection worker
│   └── shared/           # Shared libraries
├── frontend/             # React SPA
├── tests/                # Test suite
└── deployments/          # Deployment configs
```

**Services:**

- **API Service** - Read-only HTTP server for frontend and REST API
- **Scraper Worker** - Background data collection with TOR support
- **PostgreSQL** - Primary database
- **Frontend** - React SPA with real-time updates

---

## 🔧 Development

### Local Development

```bash
# Install dependencies
pip install -r services/api/requirements.txt
pip install -r services/scraper/requirements.txt

# Run tests
pytest tests/ -v

# Start API locally
cd services/api
uvicorn main:app --reload

# Start scraper locally
cd services/scraper
python worker.py
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

---

## 🚢 Deployment

### Docker Compose (Recommended)

```bash
docker-compose -f docker-compose.production.yml up -d
```

### Railway

See `deployments/railway/` for service-specific configurations:

- `railway.api.toml` - API service
- `railway.scraper.toml` - Scraper worker

---

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/listings/` | GET | All GPU listings |
| `/api/stats/` | GET | Price statistics by model |
| `/api/value/` | GET | FPS per лв rankings |
| `/docs` | GET | Interactive API documentation |

**Query Parameters:**

- `min_vram` - Filter by minimum VRAM (e.g., `?min_vram=8`)

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=services/shared --cov-report=html

# Run specific test file
pytest tests/test_core.py -v
```

---

## 🔒 Security

- **TOR Support** - Anonymous scraping to avoid IP bans
- **Rate Limiting** - Configurable request throttling
- **Environment Variables** - Sensitive data in `.env` files
- **PostgreSQL** - Production-ready database with connection pooling

---

## 📝 Configuration

Key configuration in `config.yaml`:

```yaml
database:
  url: postgresql://postgres:postgres@localhost:5432/gpu_tracker

scraper:
  max_pages: 100
  use_tor: true
  rate_limit:
    requests_per_minute: 8
    delay_between_pages: 7
```

Override with environment variables:
- `DATABASE_URL` - Database connection string
- `ENVIRONMENT` - `development` or `production`

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- **HowManyFPS** - GPU benchmark data source
- **FastAPI** - Modern Python web framework
- **React** - Frontend framework
- **TailwindCSS** - Utility-first CSS framework

---

**Made with ❤️ for the Bulgarian GPU market**
