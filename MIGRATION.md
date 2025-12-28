# Migration Guide: Monolith → Multi-Service Architecture

This guide helps you migrate from the old monolithic architecture to the new professional multi-service architecture.

## TL;DR - Quick Migration

```bash
# 1. Stop old monolith (if running)
pkill -f "python main.py"
pkill -f "uvicorn main:app"

# 2. Start new multi-service architecture
docker-compose up -d

# 3. Verify everything works
curl http://localhost:8000/health
docker-compose logs -f

# ✅ Done! You're now running the new architecture
```

## What Changed?

### Before (Monolith)
```
┌─────────────────────────────┐
│    Single Application       │
│  ┌──────────────────────┐   │
│  │   API + Scraper      │   │
│  │   (Mixed concerns)   │   │
│  └──────────────────────┘   │
│           │                 │
│           ▼                 │
│      SQLite File            │
└─────────────────────────────┘
```

**Problems:**
- ❌ API and scraping mixed together
- ❌ Can't scale independently
- ❌ SQLite file-based (single point of failure)
- ❌ API restart stops scraping
- ❌ Scraping blocks API during execution

### After (Multi-Service)
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  API Service │  │   Scraper    │  │  PostgreSQL  │
│  (Read-Only) │  │   Worker     │  │   Database   │
│              │  │  (Daemon)    │  │              │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       └─────────────────┴──────────────────┘
              Shared Database
```

**Benefits:**
- ✅ Separated concerns (API vs Scraper)
- ✅ Independent scaling
- ✅ PostgreSQL (production-ready)
- ✅ API restart doesn't affect scraper
- ✅ Fault isolation
- ✅ Graceful shutdown (no data loss)

## Migration Steps

### Step 1: Backup Your Data (Optional)

If you have important data in the old SQLite database:

```bash
# Export data from old SQLite database
python -c "
from storage.db import SessionLocal
from storage.repo import GPURepository

session = SessionLocal()
repo = GPURepository(session)
listings = repo.get_all_listings()

print(f'Found {len(listings)} listings to migrate')
# Save to JSON or CSV if needed
"
```

### Step 2: Stop Old Services

```bash
# Stop old monolith
pkill -f "python main.py"
pkill -f "uvicorn main:app"

# Stop old background processes
pkill -f "python -m ingest.pipeline"

# Verify nothing is running
ps aux | grep python
```

### Step 3: Update Configuration

**Old configuration files (no longer used):**
- `.env` (root directory)
- `config.yaml`

**New configuration:**
- `services/api/.env` - API service config
- `services/scraper/.env` - Scraper worker config
- `docker-compose.yml` - Local development

```bash
# Create API service .env
cp services/api/.env.example services/api/.env

# Create Scraper service .env
cp services/scraper/.env.example services/scraper/.env

# Edit values if needed (defaults work for local dev)
nano services/api/.env
nano services/scraper/.env
```

### Step 4: Start New Multi-Service Architecture

```bash
# Start all services (PostgreSQL + API + Scraper)
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected output:
# gpu_tracker_db       postgres:15-alpine   running   5432/tcp
# gpu_tracker_api      services/api         running   8000/tcp
# gpu_tracker_scraper  services/scraper     running
```

### Step 5: Verify Everything Works

```bash
# Check API health
curl http://localhost:8000/health

# Expected: {"status":"healthy","database":"connected"}

# Check API is serving data
curl http://localhost:8000/api/listings/

# View API logs
docker-compose logs -f api

# View Scraper logs
docker-compose logs -f scraper

# Check database
docker-compose exec postgres psql -U postgres -d gpu_tracker -c "SELECT COUNT(*) FROM gpu_listings;"
```

### Step 6: Wait for First Scrape

The scraper runs in daemon mode with a 1-hour interval (development) or 6-hour interval (production).

**To trigger immediate scrape:**
```bash
# Run one-time scrape
docker-compose run --rm -e WORKER_MODE=oneshot scraper

# Watch logs
docker-compose logs -f scraper
```

**Expected scraper output:**
```
🔧 Starting TOR service...
✅ TOR service is running
🗄️ Waiting for PostgreSQL...
✅ Database connection verified
🚀 STARTING SCRAPER WORKER (daemon mode)
🔍 STARTING SCRAPING CYCLE
✅ Scraped 1308 listings
😴 Sleeping for 3600s until next cycle...
```

### Step 7: Access the Application

```bash
# API
http://localhost:8000

# API Documentation
http://localhost:8000/docs

# Database (if needed)
psql postgresql://postgres:postgres@localhost:5432/gpu_tracker
```

## File Structure Changes

### Deprecated Files (No Longer Used)

These files are now **deprecated** and not used by the new architecture:

```
❌ main.py                  → Use services/api/main.py
❌ run.sh                   → Use docker-compose up
❌ requirements.txt         → Use services/*/requirements.txt
❌ .env (root)              → Use services/*/.env
❌ config.yaml              → Use environment variables
❌ api/                     → Moved to services/shared/api/
❌ core/                    → Moved to services/shared/core/
❌ ingest/                  → Moved to services/shared/ingest/
❌ storage/                 → Moved to services/shared/storage/
❌ gpu.db (SQLite)          → PostgreSQL in Docker
```

**You can safely delete these files** if you don't need backward compatibility.

### New File Structure

```
services/
├── api/                    # NEW: API Service
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── scraper/                # NEW: Scraper Worker
│   ├── worker.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
└── shared/                 # Shared code (moved from root)
    ├── api/
    ├── core/
    ├── ingest/
    └── storage/

docker-compose.yml          # NEW: Multi-service orchestration
ARCHITECTURE.md             # NEW: Architecture documentation
```

## Common Issues

### Issue 1: Port 8000 Already in Use

**Symptom:**
```
Error: bind: address already in use
```

**Solution:**
```bash
# Stop old service
pkill -f "uvicorn main:app"

# Or use different port
# Edit docker-compose.yml:
ports:
  - "8001:8000"  # Changed from 8000:8000
```

### Issue 2: Database Connection Errors

**Symptom:**
```
Connection refused to PostgreSQL
```

**Solution:**
```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### Issue 3: Scraper Not Collecting Data

**Symptom:**
- No listings in database
- Scraper logs show errors

**Solution:**
```bash
# Check scraper logs
docker-compose logs scraper

# Verify TOR is working
docker-compose exec scraper curl --socks5 localhost:9050 https://check.torproject.org/api/ip

# Run manual scrape
docker-compose run --rm -e WORKER_MODE=oneshot scraper
```

### Issue 4: Old SQLite Data Not Migrated

**Symptom:**
- New database is empty
- Want to keep old data

**Solution:**

The new architecture uses PostgreSQL instead of SQLite. Old data won't automatically migrate.

**Option 1: Start Fresh (Recommended)**
- Let the scraper collect new data
- Scraper will populate the database automatically

**Option 2: Manual Migration**
```python
# Create a migration script if needed
# Read from old SQLite → Write to new PostgreSQL
```

For most users, starting fresh is the best option since the scraper will collect fresh data anyway.

## Rollback to Monolith (If Needed)

If you need to rollback to the old monolithic architecture:

```bash
# 1. Stop new services
docker-compose down

# 2. Start old monolith
./run.sh

# Or manually:
python main.py
```

**Note:** The old monolith is **deprecated** and will not receive updates. The new multi-service architecture is the recommended approach.

## Production Deployment

For production deployment to Railway:

1. **Read the Railway guide:**
   ```bash
   cat deployments/railway/README.md
   ```

2. **Deploy services:**
   - Add PostgreSQL database
   - Deploy API service from `services/api/`
   - Deploy Scraper worker from `services/scraper/`

3. **Configure environment variables:**
   - Set `WORKER_MODE=daemon` for scraper
   - Set `SCRAPE_INTERVAL_SECONDS=21600` (6 hours)
   - Set `SCRAPER_MAX_PAGES=999` (all pages)

See [deployments/railway/README.md](deployments/railway/README.md) for complete instructions.

## Benefits of New Architecture

✅ **Reliability**
- Services restart independently
- Database is centralized and managed
- Graceful shutdown prevents data loss

✅ **Scalability**
- API can scale horizontally (1-3+ replicas)
- Scraper stays at 1 replica (no duplicates)
- PostgreSQL handles concurrent connections

✅ **Maintainability**
- Clear separation of concerns
- Easier to debug (isolated logs)
- Smaller, focused codebases

✅ **Production-Ready**
- Health checks for monitoring
- Professional logging
- Sentry error tracking
- Docker containerization

## Questions?

- **Architecture details:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Railway deployment:** [deployments/railway/README.md](deployments/railway/README.md)
- **Main documentation:** [README.md](README.md)
- **Issues:** Open an issue on GitHub

---

**Last Updated:** 2025-01-15

Welcome to the new multi-service architecture! 🚀
