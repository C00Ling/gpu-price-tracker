# ✅ Deployment Checklist

## Pre-Deployment

- [x] Код е тестван (124/124 tests passing)
- [x] Deprecations са поправени
- [x] Static files са създадени
- [x] Documentation е актуална
- [x] Docker setup е готов
- [x] CI/CD pipeline е конфигуриран

## Environment Setup

### Development
```bash
ENVIRONMENT=development
DATABASE_URL=sqlite:///./gpu.db
REDIS_ENABLED=false
```

### Production
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@localhost:5432/gpu_market
REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_PORT=6379
```

## Deployment Steps

### Option 1: Local Development (Ready NOW)
```bash
# 1. Quick start
./quickstart.sh

# 2. Start API
python main.py

# 3. Access
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Dashboard: http://localhost:8000/dashboard
```

### Option 2: Docker Compose (Recommended for Production)
```bash
# 1. Set environment variables
export DB_USER=gpu_user
export DB_PASSWORD=secure_password
export REDIS_PASSWORD=redis_password

# 2. Start services
docker-compose -f docker-compose.production.yml up -d

# 3. Check health
curl http://localhost:8000/health
```

### Option 3: Kubernetes (Advanced)
```bash
# TODO: Create k8s manifests
kubectl apply -f k8s/
```

## Post-Deployment

### 1. Health Checks
```bash
# API Health
curl http://localhost:8000/health

# Database connection
curl http://localhost:8000/api/listings/count/total

# Stats endpoint
curl http://localhost:8000/api/stats/
```

### 2. Run Initial Scrape
```bash
python -m ingest.pipeline
```

### 3. Setup Cron/Celery for Scheduled Scraping
```bash
# Start Celery worker
celery -A jobs.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A jobs.celery_app beat --loglevel=info
```

### 4. Monitor Logs
```bash
# Docker logs
docker-compose logs -f api

# Local logs
tail -f logs/gpu_service.log
```

## Security Checklist (Production)

- [ ] Change default passwords
- [ ] Enable HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Set up monitoring (Sentry, Prometheus)
- [ ] Regular backups configured
- [ ] Secrets in environment variables (not in code)

## Database Migration (SQLite → PostgreSQL)

Follow: [docs/POSTGRES_MIGRATION.md](docs/POSTGRES_MIGRATION.md)

## Rollback Plan

```bash
# Stop services
docker-compose down

# Restore from backup
cp backups/gpu.db.backup gpu.db

# Restart with SQLite
export DATABASE_URL=sqlite:///./gpu.db
docker-compose up -d
```

## Monitoring Endpoints

- `/health` - Service health
- `/api/listings/count/total` - Total listings count
- `/api/stats/` - Statistics
- `/docs` - API documentation (disable in production!)

## Support

- GitHub Issues: https://github.com/yourusername/gpu_price_tracker/issues
- Documentation: [README.md](README.md)
- Quick Start: [QUICKSTART.md](QUICKSTART.md)

---

**Last Updated:** 2025-12-21
**Status:** ✅ Production Ready
