# Multi-Service Architecture

## Overview

The GPU Price Tracker has been redesigned with a **professional multi-service architecture** that separates concerns and enables independent scaling and deployment.

## Architecture Diagram

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
│              │    │  (Daemon)    │    │              │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                    │
       │                   │                    │
       └───────────────────┴────────────────────┘
              Shared Database Connection
```

## Services

### 1. API Service ([services/api/](services/api/))

**Purpose:** Read-only HTTP server for web UI and REST API

**Responsibilities:**
- Serve REST API endpoints
- Handle WebSocket connections for real-time updates
- Serve static frontend files
- Health checks and monitoring
- **NO scraping logic** - purely data access layer

**Technology Stack:**
- FastAPI (async web framework)
- SQLAlchemy (database ORM)
- Uvicorn (ASGI server)

**Key Files:**
- [main.py](services/api/main.py) - FastAPI application entry point
- [Dockerfile](services/api/Dockerfile) - Multi-stage build, non-root user
- [start.sh](services/api/start.sh) - Startup script with DB health checks
- [requirements.txt](services/api/requirements.txt) - HTTP server dependencies

**Environment Variables:**
```bash
ENVIRONMENT=production
SERVICE_NAME=api
DATABASE_URL=postgresql://user:pass@host:5432/db
PORT=8000
LOG_LEVEL=INFO
CORS_ORIGINS=*
```

**Scaling:**
- Horizontal scaling supported (multiple replicas)
- Recommended: 1-3 replicas depending on traffic
- Memory: 512MB - 1GB per replica

### 2. Scraper Worker ([services/scraper/](services/scraper/))

**Purpose:** Autonomous background worker for GPU data collection

**Responsibilities:**
- Periodic web scraping (OLX.bg)
- TOR proxy management for anonymity
- Data validation and quality control
- Database writes
- **NO HTTP endpoints** - pure background worker

**Technology Stack:**
- Python 3.11+
- BeautifulSoup4 (HTML parsing)
- TOR + PySocks (anonymity)
- SQLAlchemy (database ORM)

**Worker Modes:**
- **daemon** - Continuous scraping with configurable interval (production)
- **oneshot** - Single scrape and exit (cron jobs, manual runs)
- **cron** - Scheduled execution via cron daemon

**Key Files:**
- [worker.py](services/scraper/worker.py) - Worker entry point with 3 modes
- [Dockerfile](services/scraper/Dockerfile) - Includes TOR, cron support
- [start.sh](services/scraper/start.sh) - TOR initialization, mode selection
- [requirements.txt](services/scraper/requirements.txt) - Scraping dependencies
- [crontab](services/scraper/crontab) - Cron schedule configuration

**Environment Variables:**
```bash
ENVIRONMENT=production
SERVICE_NAME=scraper
WORKER_MODE=daemon              # daemon | oneshot | cron
SCRAPE_INTERVAL_SECONDS=21600   # 6 hours
TOR_ENABLED=true
DATABASE_URL=postgresql://user:pass@host:5432/db
SCRAPER_MAX_PAGES=999           # Scrape all pages
```

**Scaling:**
- Fixed at **1 replica** to avoid duplicate scraping
- Memory: 1GB recommended (for TOR + scraping)
- CPU: Low (most time spent waiting for network)

### 3. PostgreSQL Database

**Purpose:** Centralized persistent storage

**Responsibilities:**
- Store GPU listings
- Store price statistics
- Store benchmark data
- Transaction management

**Configuration:**
- Version: PostgreSQL 15+
- Connection pooling: SQLAlchemy manages connections
- Health checks: `pg_isready` command

**Schema:**
See [storage/models.py](services/shared/storage/models.py) for ORM definitions.

### 4. Shared Libraries ([services/shared/](services/shared/))

**Purpose:** Code shared between API and Scraper services

**Contents:**
- **core/** - Business logic, utilities, logging, Sentry
- **api/** - API routes, schemas, dependencies
- **storage/** - Database models, repository pattern
- **ingest/** - Scraping pipeline, data processing

**Import Path:**
Both services add `/app/shared` to Python path:
```python
sys.path.insert(0, '/app/shared')
from storage.db import init_db
from ingest.pipeline import run_pipeline
```

## Communication Patterns

### API → Database
- Read-only queries (SELECT)
- Connection pooling for performance
- Repository pattern for data access

### Scraper → Database
- Write operations (INSERT, UPDATE)
- Batch inserts for efficiency
- Retry logic for transient failures

### API ← → User
- HTTP REST API
- WebSocket for real-time updates
- CORS configured for web browsers

## Data Flow

### Scraping Flow (Scraper Worker)
```
┌─────────────┐
│ Start Timer │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Initialize TOR  │
│ (10s wait)      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Connect to DB   │
│ (30 retries)    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Scrape OLX.bg   │
│ (7 search terms)│
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Filter & Validate│
│ (Quality control)│
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Save to DB      │
│ (Batch insert)  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Sleep N seconds │
│ (if daemon mode)│
└──────┬──────────┘
       │
       └──────► (Loop if daemon)
```

### API Request Flow
```
┌─────────────┐
│ HTTP Request│
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ FastAPI Router  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Validate Input  │
│ (Pydantic)      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Repository Query│
│ (SQLAlchemy)    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Transform to    │
│ JSON Response   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Return to Client│
└─────────────────┘
```

## Deployment Options

### Option 1: Railway (Recommended - 5 minutes)

Complete guide: [deployments/railway/README.md](deployments/railway/README.md)

**Architecture:**
```
Railway Project
├─ PostgreSQL Service (managed)
├─ API Service (1-3 replicas, auto-scaling)
└─ Scraper Worker (1 replica, daemon mode)
```

**Steps:**
1. Push to GitHub
2. Create Railway project
3. Add PostgreSQL database
4. Deploy API service from `services/api/`
5. Deploy Scraper service from `services/scraper/`
6. Configure environment variables
7. Generate domain for API

**Cost:** $0-5/month

### Option 2: Docker Compose (Local Development)

Complete setup: [docker-compose.yml](docker-compose.yml)

**Start all services:**
```bash
docker-compose up -d
```

**Services:**
- PostgreSQL: `localhost:5432`
- API: `http://localhost:8000`
- Scraper: Background worker

**View logs:**
```bash
docker-compose logs -f api      # API logs
docker-compose logs -f scraper  # Scraper logs
```

### Option 3: VPS Deployment

Deploy to DigitalOcean, Hetzner, or any VPS:

1. Install Docker and Docker Compose
2. Clone repository
3. Configure environment variables
4. Run `docker-compose -f docker-compose.production.yml up -d`
5. Setup Nginx reverse proxy (optional)

See: [DEPLOYMENT_VPS.md](DEPLOYMENT_VPS.md)

## Monitoring & Observability

### Health Checks

**API Service:**
- Endpoint: `GET /health`
- Response: `{"status": "healthy", "database": "connected"}`
- Interval: Every 30 seconds

**Scraper Worker:**
- Process health check (TOR process running)
- No HTTP endpoint (worker doesn't expose HTTP)
- Logs indicate health status

**PostgreSQL:**
- Command: `pg_isready -U postgres`
- Interval: Every 10 seconds

### Logging

**API Service:**
```
[2025-01-15 14:30:45] INFO API Service started on 0.0.0.0:8000
[2025-01-15 14:30:50] INFO GET /api/listings/ - 200 OK (15ms)
```

**Scraper Worker:**
```
[2025-01-15 14:00:00] INFO Starting scraping cycle #42
[2025-01-15 14:05:23] INFO Scraped 1308 listings (7 search terms)
[2025-01-15 14:05:30] INFO Sleeping for 21600s until next cycle...
```

**View logs:**
```bash
# Railway
railway logs --service api
railway logs --service scraper

# Docker Compose
docker-compose logs -f api
docker-compose logs -f scraper
```

### Error Monitoring

**Sentry Integration:**
- Automatic error capture
- API errors with request context
- Scraper errors with scraping context
- Performance monitoring
- Alert notifications

**Configuration:**
```bash
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=production
```

See: [README.md - Monitoring & Error Tracking](README.md#-monitoring--error-tracking)

## Graceful Shutdown

Both services implement graceful shutdown to prevent data loss:

**API Service:**
- Receives SIGTERM/SIGINT
- Completes in-flight requests
- Closes database connections
- Exits cleanly

**Scraper Worker:**
- Receives SIGTERM/SIGINT
- Completes current scraping cycle
- Saves all collected data
- Closes TOR and database connections
- Exits cleanly

**Implementation:**
```python
shutdown_requested = False

def handle_shutdown_signal(signum, frame):
    global shutdown_requested
    logger.info("Received shutdown signal, completing current work...")
    shutdown_requested = True

signal.signal(signal.SIGTERM, handle_shutdown_signal)
signal.signal(signal.SIGINT, handle_shutdown_signal)
```

## Security

### API Service
- Non-root user (`apiuser`)
- No write access to database
- CORS configuration
- Input validation (Pydantic)
- Rate limiting (planned)

### Scraper Worker
- Non-root user (`scraperuser`)
- TOR proxy for anonymity
- No exposed HTTP ports
- Isolated network access

### Database
- Strong passwords
- Connection encryption (SSL in production)
- Backup strategy (daily recommended)

### Environment Variables
- Never commit secrets to Git
- Use Railway's secrets management
- Rotate credentials regularly

## Troubleshooting

### API won't start
```bash
# Check DATABASE_URL is set
echo $DATABASE_URL

# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs api
```

### Scraper won't start
```bash
# Check TOR initialization
docker-compose logs scraper | grep "TOR"

# Check DATABASE_URL
docker-compose exec scraper env | grep DATABASE

# Verify worker mode
docker-compose exec scraper env | grep WORKER_MODE
```

### No data being collected
```bash
# Check scraper logs
docker-compose logs -f scraper

# Verify TOR is working
docker-compose exec scraper curl --socks5 localhost:9050 https://check.torproject.org/api/ip

# Check database connectivity
docker-compose exec scraper python -c "from storage.db import engine; engine.connect()"
```

### Database connection errors
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Check connection string
echo $DATABASE_URL  # Should be: postgresql://user:pass@host:port/db

# Verify PostgreSQL is accessible
docker-compose exec postgres pg_isready
```

## Performance

### API Service
- **Response time:** < 100ms (typical)
- **Throughput:** 1000+ req/s (single replica)
- **Memory:** 512MB - 1GB
- **CPU:** Low (I/O bound)

### Scraper Worker
- **Scraping time:** 5-10 minutes per cycle
- **Memory:** 1GB (TOR + scraping)
- **CPU:** Low (network bound)
- **Interval:** 6 hours (configurable)

### Database
- **Storage:** ~100MB for 10K listings
- **Connections:** 10-20 concurrent
- **Queries:** Simple SELECT/INSERT (no complex joins)

## Benefits of Multi-Service Architecture

✅ **Independent Scaling**
- Scale API horizontally (1-3+ replicas)
- Scraper stays at 1 replica (no duplicates)

✅ **Independent Deployment**
- Deploy API without affecting scraper
- Update scraper without API downtime

✅ **Fault Isolation**
- API crash doesn't stop scraping
- Scraper crash doesn't affect API

✅ **Technology Flexibility**
- Different dependencies per service
- Different resource limits
- Different update schedules

✅ **Development Speed**
- Work on API and scraper independently
- Smaller, focused codebases
- Easier testing and debugging

✅ **Production Ready**
- Graceful shutdown prevents data loss
- Health checks for monitoring
- Professional logging and error tracking

## Migration from Monolith

The old monolithic architecture (single service with SQLite) has been replaced with this multi-service architecture. Key changes:

**Before:**
- Single `main.py` with scraping + API
- SQLite database (file-based)
- Everything in one Docker container
- Mixed concerns (scraping + HTTP serving)

**After:**
- Separated API and Scraper services
- PostgreSQL database (centralized)
- Independent Docker containers
- Clear separation of concerns

**Migration Path:**
1. Deploy new multi-service architecture
2. Run initial scrape to populate PostgreSQL
3. Verify data integrity
4. Switch traffic to new API
5. Decommission old monolith

## Future Enhancements

- [ ] Redis caching layer for API responses
- [ ] Celery task queue for advanced scheduling
- [ ] Prometheus metrics for monitoring
- [ ] Grafana dashboards for visualization
- [ ] API rate limiting and authentication
- [ ] Horizontal scraper scaling (with deduplication)
- [ ] Real-time notifications via WebSocket
- [ ] GraphQL API alongside REST

---

**Last Updated:** 2025-01-15

For detailed deployment instructions, see:
- [Railway Deployment Guide](deployments/railway/README.md)
- [Main README](README.md)
- [VPS Deployment Guide](DEPLOYMENT_VPS.md)
