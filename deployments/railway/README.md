# Railway Multi-Service Deployment

Complete guide for deploying the GPU Price Tracker as multiple independent services on Railway.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         Railway Project                      │
├─────────────────────────────────────────────┤
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │   API    │  │ Scraper  │  │PostgreSQL │ │
│  │ Service  │  │  Worker  │  │ Database  │ │
│  │ (HTTP)   │  │ (Cron)   │  │           │ │
│  └─────┬────┘  └─────┬────┘  └─────┬─────┘ │
│        │             │              │       │
│        └─────────────┴──────────────┘       │
│              Shared Database                │
└─────────────────────────────────────────────┘
```

## 📋 Prerequisites

1. Railway account ([railway.app](https://railway.app))
2. Railway CLI installed (optional, for local testing)
3. GitHub repository connected to Railway

## 🚀 Deployment Steps

### Step 1: Create Railway Project

```bash
# Login to Railway
railway login

# Create new project
railway init

# Link to your GitHub repository
railway link
```

### Step 2: Add PostgreSQL Database

1. Go to Railway dashboard
2. Click "New Service" → "Database" → "PostgreSQL"
3. Railway will automatically set `DATABASE_URL` environment variable

### Step 3: Deploy API Service

1. Click "New Service" → "GitHub Repo"
2. Select your repository
3. Configure service:
   - **Name**: `api`
   - **Root Directory**: `services/api`
   - **Build Command**: (auto-detected from Dockerfile)
   - **Start Command**: `./start.sh`
4. Add environment variables:
   ```
   ENVIRONMENT=production
   SERVICE_NAME=api
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   PORT=8000
   ```
5. Generate domain:
   - Click "Settings" → "Networking" → "Generate Domain"
   - Your API will be available at: `https://your-project.up.railway.app`

### Step 4: Deploy Scraper Worker

1. Click "New Service" → "GitHub Repo"
2. Select your repository (same as API)
3. Configure service:
   - **Name**: `scraper`
   - **Root Directory**: `services/scraper`
   - **Build Command**: (auto-detected from Dockerfile)
   - **Start Command**: `./start.sh`
4. Add environment variables:
   ```
   ENVIRONMENT=production
   SERVICE_NAME=scraper
   WORKER_MODE=daemon
   SCRAPE_INTERVAL_SECONDS=21600
   TOR_ENABLED=true
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ```
5. **Important**: Do NOT generate a domain for scraper (it's a background worker)

### Step 5: Configure Environment Variables

#### Required for both services:

- `DATABASE_URL` - Auto-set by Railway from PostgreSQL service
- `ENVIRONMENT` - Set to `production`

#### Optional (recommended):

- `SENTRY_DSN` - Error monitoring (get from sentry.io)
- `LOG_LEVEL` - Set to `INFO` or `WARNING` for production

#### API Service specific:

- `CORS_ORIGINS` - Allowed origins (default: `*`)
- `API_PORT` - Port for API (default: `8000`)

#### Scraper Worker specific:

- `WORKER_MODE` - `daemon` for Railway (continuous scraping)
- `SCRAPE_INTERVAL_SECONDS` - Interval between scrapes (default: `21600` = 6 hours)
- `SCRAPER_MAX_PAGES` - Max pages per search term (default: `999`)
- `TOR_ENABLED` - Enable TOR proxy (default: `true`)

## 🔧 Configuration Files

Each service has its Railway configuration in this directory:

- `railway.api.toml` - API Service configuration
- `railway.scraper.toml` - Scraper Worker configuration

To use these configurations:

```bash
# For API Service
railway up -d services/api -c deployments/railway/railway.api.toml

# For Scraper Worker
railway up -d services/scraper -c deployments/railway/railway.scraper.toml
```

## 🏥 Health Checks

### API Service
- **Endpoint**: `GET /health`
- **Expected**: `{"status": "healthy"}`
- **Interval**: 30 seconds

### Scraper Worker
- **Type**: Process health check (TOR process)
- **No HTTP endpoint** (worker doesn't expose HTTP)

## 📊 Monitoring

### View Logs

```bash
# API Service logs
railway logs --service api

# Scraper Worker logs
railway logs --service scraper

# PostgreSQL logs
railway logs --service postgres
```

### Metrics

Check Railway dashboard for:
- CPU usage
- Memory usage
- Network traffic
- Deployment history

## 🔄 Updates & Deployments

Railway automatically deploys on git push:

```bash
git add .
git commit -m "Update services"
git push origin main
```

To deploy specific service:

```bash
# Deploy only API
railway up -d services/api -s api

# Deploy only Scraper
railway up -d services/scraper -s scraper
```

## 🐛 Troubleshooting

### API Service won't start

1. Check DATABASE_URL is set
2. Check logs: `railway logs --service api`
3. Verify PostgreSQL is running
4. Test locally with docker-compose

### Scraper Worker won't start

1. Check TOR is initializing (check logs)
2. Verify DATABASE_URL is accessible
3. Check WORKER_MODE is set to `daemon`
4. Verify sufficient memory (1GB recommended)

### Database connection errors

1. Verify DATABASE_URL format: `postgresql://user:pass@host:port/db`
2. Check PostgreSQL service is running
3. Verify both services can access database
4. Check Railway network settings

### Scraper not collecting data

1. Check scraper logs for errors
2. Verify TOR is running: should see "Bootstrapped 100%"
3. Check DATABASE_URL is writable
4. Verify SCRAPE_INTERVAL_SECONDS is reasonable (not too short)

## 💰 Cost Optimization

Railway pricing is based on:
- **Compute**: $0.000463/GB-hour of RAM
- **Egress**: $0.10/GB

### Tips to reduce costs:

1. **API Service**:
   - Scale down to 512MB RAM if possible
   - Use caching to reduce database queries
   - Optimize static file serving

2. **Scraper Worker**:
   - Increase SCRAPE_INTERVAL_SECONDS (less frequent scraping)
   - Reduce SCRAPER_MAX_PAGES if full coverage not needed
   - Use daemon mode (more efficient than cron)

3. **PostgreSQL**:
   - Enable query optimization
   - Regular vacuum and analyze
   - Archive old data

## 🔐 Security Best Practices

1. **Never commit secrets** to git
2. Use Railway's environment variables UI
3. Enable **private networking** between services
4. Rotate database passwords regularly
5. Monitor Sentry for security errors

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Railway CLI Reference](https://docs.railway.app/develop/cli)
- [Railway Pricing](https://railway.app/pricing)
- [Project GitHub](https://github.com/yourusername/gpu_price_tracker)

## 🆘 Support

For issues:
1. Check Railway service logs
2. Review health check status
3. Consult troubleshooting section above
4. Open GitHub issue if bug found
