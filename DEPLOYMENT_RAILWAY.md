# 🚂 Railway Deployment Guide

## Защо Railway?
- ✅ Безплатен план ($5 кредит месечно)
- ✅ Автоматичен deploy от GitHub
- ✅ PostgreSQL вграден
- ✅ Redis вграден
- ✅ Автоматичен HTTPS
- ✅ Custom domain support
- ✅ Лесна конфигурация

## 📋 Prerequisites

1. GitHub акаунт
2. Railway акаунт (https://railway.app)
3. Проектът на GitHub

---

## 🚀 Deployment Steps

### 1. Подготовка на GitHub repo

```bash
cd /home/petar/Desktop/gpu_price_tracker

# Инициализирай git (ако не е)
git init
git add .
git commit -m "Initial commit - Production ready"

# Създай GitHub repo и push-ни
# На GitHub: New Repository -> gpu_price_tracker
git remote add origin https://github.com/yourusername/gpu_price_tracker.git
git branch -M main
git push -u origin main
```

### 2. Deploy на Railway

#### А. Отвори Railway
1. Отиди на https://railway.app
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Избери `gpu_price_tracker`

#### Б. Добави PostgreSQL
1. Click "New" → "Database" → "PostgreSQL"
2. Railway автоматично създава DB и `DATABASE_URL`

#### В. Добави Redis (optional)
1. Click "New" → "Database" → "Redis"
2. Railway създава `REDIS_URL`

#### Г. Конфигурирай Environment Variables
В Railway dashboard → Settings → Variables:

```env
ENVIRONMENT=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_ENABLED=true
REDIS_URL=${{Redis.REDIS_URL}}

# OLX Scraping
SCRAPER_MAX_PAGES=5
SCRAPER_DELAY=2

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

#### Д. Configure Build
Railway автоматично detection на Python.

Ако трябва custom build command:
```bash
# Build Command
pip install -r requirements.txt && cd frontend && npm install && npm run build && cd ..

# Start Command
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 3. Deploy!

Railway автоматично deploy-ва при всеки git push!

```bash
git add .
git commit -m "Update feature"
git push
# Railway auto-deploys!
```

### 4. Достъп до сайта

Railway дава URL като:
```
https://gpu-price-tracker-production.up.railway.app
```

Custom domain:
1. Settings → Domains
2. Add custom domain
3. Update DNS records

---

## 🔧 Production Configuration

### Procfile (optional)
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
worker: celery -A jobs.celery_app worker --loglevel=info
beat: celery -A jobs.celery_app beat --loglevel=info
```

### Railway.json (optional)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## 📊 Monitoring

### Logs
```bash
# Railway dashboard → Logs tab
# Real-time logs
```

### Metrics
- CPU usage
- Memory usage
- Network traffic
- Request counts

---

## 💰 Pricing

### Free Tier ($5/month credit)
- Enough за малък проект
- ~500 hours/month
- 512MB RAM
- 1GB Storage

### Hobby Plan ($5/month)
- Unlimited hours
- 8GB RAM
- 100GB Storage

---

## 🆘 Troubleshooting

### Build fails
```bash
# Check railway.json
# Check requirements.txt
# Check Python version
```

### Database connection error
```bash
# Verify DATABASE_URL is set
# Check PostgreSQL service running
```

### Out of memory
```bash
# Upgrade to Hobby plan
# Optimize code (reduce memory usage)
```

---

## ✅ Post-Deployment Checklist

- [ ] API accessible at URL
- [ ] Database connected
- [ ] /health returns 200
- [ ] /docs works
- [ ] Frontend loads
- [ ] Scraper can run
- [ ] Logs are visible
- [ ] Metrics tracking

---

## 🔐 Security

```env
# Never commit these!
DB_PASSWORD=xxx
REDIS_PASSWORD=xxx
SECRET_KEY=xxx
```

Use Railway's environment variables!

---

## 📚 Resources

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Status: https://status.railway.app

