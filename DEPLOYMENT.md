# 🚀 Deployment Guide

Пълен guide за deploy на GPU Price Tracker в production.

---

## 🎯 Препоръка за платформа

| Нужда | Платформа | Цена | Сложност |
|-------|-----------|------|----------|
| **Бърз старт, безплатно** | Railway | $0-5/месец | ⭐ Лесно |
| **Пълен контрол, евтино** | Hetzner VPS | €4/месец | ⭐⭐ Средно |
| **Auto-scaling** | DigitalOcean | $5-12/месец | ⭐⭐ Средно |
| **Безплатно хоби** | Render.com | $0 | ⭐ Лесно |

---

## 🚂 Railway Deployment (Препоръчано)

Най-бързият начин да deploy-неш проекта в production.

### Предимства
- ✅ $5 безплатен кредит месечно
- ✅ Auto-deploy от GitHub
- ✅ PostgreSQL + Redis included
- ✅ Auto HTTPS
- ✅ Custom domains

### Стъпки

#### 1️⃣ Push към GitHub
```bash
# Създай GitHub repo на: https://github.com/new
# Repo name: gpu-price-tracker

cd /home/petar/Desktop/gpu_price_tracker
git remote add origin https://github.com/твоят-username/gpu-price-tracker.git
git push -u origin main
```

#### 2️⃣ Deploy на Railway
1. Отвори https://railway.app
2. Login with GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Избери `gpu-price-tracker`
5. Railway започва автоматичен build

#### 3️⃣ Добави бази данни
```
1. Click "New" → "Database" → "PostgreSQL"
2. Click "New" → "Database" → "Redis"
```

Railway автоматично създава `DATABASE_URL` и `REDIS_URL`.

#### 4️⃣ Конфигурирай Variables
В Railway dashboard → твоят service → **Variables**:

```env
ENVIRONMENT=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_ENABLED=true
REDIS_URL=${{Redis.REDIS_URL}}
SCRAPER_MAX_PAGES=5
SCRAPER_DELAY=2
```

#### 5️⃣ Generate Domain
1. Settings → Domains
2. Click **"Generate Domain"**
3. Получаваш URL като: `https://твоят-проект.up.railway.app`

### ✅ Тестване
```bash
# Health check
curl https://твоят-url.railway.app/health

# API docs
https://твоят-url.railway.app/docs

# Dashboard
https://твоят-url.railway.app/dashboard
```

### 💰 Pricing
- **Free tier:** $5 credit/месец (~500 часа)
- **Hobby:** $5/месец + usage (unlimited)

---

## 🖥️ VPS Deployment (Advanced)

За пълен контрол и евтино hosting.

### Quick Start
```bash
# 1. SSH към VPS
ssh root@your-server-ip

# 2. Install dependencies
apt update && apt upgrade -y
apt install -y python3-pip python3-venv nginx postgresql redis-server git

# 3. Clone project
cd /home
git clone https://github.com/твоят-username/gpu-price-tracker.git
cd gpu-price-tracker

# 4. Setup Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. Setup PostgreSQL
sudo -u postgres psql
CREATE DATABASE gpu_market;
CREATE USER gpu_user WITH PASSWORD 'твоята-парола';
GRANT ALL PRIVILEGES ON DATABASE gpu_market TO gpu_user;
\q

# 6. Configure .env
cp .env.example .env
nano .env
# Update DATABASE_URL, REDIS settings

# 7. Setup Systemd service
sudo cp scripts/gpu-market.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gpu-market
sudo systemctl start gpu-market

# 8. Setup Nginx reverse proxy
sudo nano /etc/nginx/sites-available/gpu-market
# Add proxy config (see DEPLOYMENT_VPS.md for details)
sudo ln -s /etc/nginx/sites-available/gpu-market /etc/nginx/sites-enabled/
sudo systemctl reload nginx

# 9. Setup SSL
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d твоят-домейн.com
```

### 💰 VPS Pricing
- **Hetzner:** €4/месец (2 vCPU, 4GB RAM)
- **DigitalOcean:** $6/месец (1 vCPU, 1GB RAM)
- **Linode:** $5/месец (1 vCPU, 1GB RAM)

Пълен VPS guide: [DEPLOYMENT_VPS.md](DEPLOYMENT_VPS.md)

---

## 🐳 Docker Deployment

За всяка платформа с Docker support.

```bash
# Production deployment
docker-compose -f docker-compose.production.yml up -d

# Check health
curl http://localhost:8000/health
```

**Environment variables:**
```bash
export DB_USER=gpu_user
export DB_PASSWORD=secure_password
export REDIS_PASSWORD=redis_password
```

---

## 📊 Platform Comparison

| Feature | Railway | VPS | Render.com |
|---------|---------|-----|------------|
| Setup време | 5 мин | 30 мин | 5 мин |
| Free tier | $5 credit | ❌ | ✅ Limited |
| Auto-deploy | ✅ | ❌ | ✅ |
| PostgreSQL | ✅ | Manual | ✅ |
| SSL/HTTPS | ✅ Auto | Manual | ✅ Auto |
| Пълен контрол | ❌ | ✅ | ❌ |
| Cost (месец) | $5-10 | €4-6 | $0-7 |

---

## ✅ Post-Deployment Checklist

След deploy, провери:

- [ ] API е достъпен на URL
- [ ] `/health` връща 200 OK
- [ ] `/docs` зарежда Swagger UI
- [ ] Dashboard зарежда без грешки
- [ ] Database connection работи
- [ ] Redis connection работи (ако е enabled)
- [ ] Logs са видими
- [ ] Може да се пусне scraper

### Пусни първи scrape
```bash
# Railway (via Railway CLI)
railway run python -m ingest.pipeline

# VPS/Docker
python -m ingest.pipeline
```

---

## 🆘 Troubleshooting

### Problem: Dashboard е празен след deploy
**Причина:** Използва се SQLite вместо PostgreSQL.

**Решение:**
```bash
# В Railway Variables, добави:
DATABASE_URL=${{Postgres.DATABASE_URL}}

# След redeploy, пусни scraper:
curl -X POST https://твоят-url.railway.app/api/trigger-scrape
```

### Problem: Build fails на Railway
**Причини:**
- Липсва `requirements.txt`
- Грешна Python версия
- Липсва `railway.json` config

**Решение:**
```bash
# Провери requirements.txt е commit-нат
git status

# Увери се че Python версията е правилна (3.11+)
cat railway.json
```

### Problem: Database connection error
**Причини:**
- `DATABASE_URL` не е set
- PostgreSQL service не е online
- Грешна connection string

**Решение:**
```bash
# Провери variables:
echo $DATABASE_URL

# Провери PostgreSQL е running
# Railway: Dashboard → Postgres service → Status
# VPS: sudo systemctl status postgresql
```

### Problem: Out of memory
**Решения:**
- Railway: Upgrade към Hobby plan ($5/месец)
- VPS: Upgrade към по-голям droplet
- Оптимизирай Redis cache settings
- Намали `SCRAPER_MAX_PAGES`

### Problem: Slow response times
**Решения:**
- Enable Redis caching (`REDIS_ENABLED=true`)
- Добави database indexes (вижте migrations)
- Enable CDN за static files
- Оптимизирай scraper delay

---

## 🔐 Security Best Practices

### Production Environment Variables
```env
# НИКОГА не commit-вай тези стойности!
DB_PASSWORD=strong-random-password
REDIS_PASSWORD=another-strong-password
SECRET_KEY=cryptographically-secure-key
```

Използвай Railway Variables или VPS environment variables.

### Enable HTTPS
- **Railway:** Автоматично ✅
- **Render:** Автоматично ✅
- **VPS:** Използвай Certbot (Let's Encrypt)

### Firewall (VPS only)
```bash
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### Rate Limiting
Вече enabled в API (`core/rate_limiter.py`):
- 100 requests/минута per IP
- Configurable via `config.yaml`

---

## 📊 Monitoring

### Railway
- Dashboard → Logs tab (real-time)
- Dashboard → Metrics (CPU, RAM, Network)
- Dashboard → Deployments (history)

### VPS
```bash
# Service logs
sudo journalctl -u gpu-market -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log

# System resources
htop
df -h
```

### Health Checks
```bash
# API health
curl https://твоят-url/health

# Database check
curl https://твоят-url/api/listings/count/total

# Stats endpoint
curl https://твоят-url/api/stats/
```

---

## 🔄 Updates & Maintenance

### Railway (Auto-deploy)
```bash
git add .
git commit -m "Update feature X"
git push
# Railway auto-deploys! 🚀
```

### VPS (Manual)
```bash
cd /home/gpu_price_tracker
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart gpu-market
```

### Database Backups
```bash
# Railway: Automatic backups included

# VPS: Setup cron job
0 2 * * * /home/deploy/backup-db.sh
```

---

## 🎯 Decision Tree

```
Искаш безплатно тестване?
├─ YES → Render.com Free Tier или Railway ($5 credit)
└─ NO  → Continue

Искаш най-лесен deploy?
├─ YES → Railway (5 минути setup)
└─ NO  → Continue

Искаш най-евтино за production?
├─ YES → Hetzner VPS (€4/месец)
└─ NO  → Continue

Искаш managed service с auto-scaling?
└─ YES → DigitalOcean App Platform или Railway
```

---

## 📚 Resources

- **Railway Guide:** Този файл (секция по-горе)
- **Advanced VPS Guide:** [DEPLOYMENT_VPS.md](DEPLOYMENT_VPS.md)
- **Docker Setup:** [docker-compose.production.yml](docker-compose.production.yml)
- **Main Docs:** [README.md](README.md)
- **Quick Start:** [QUICKSTART.md](QUICKSTART.md)

### External Links
- Railway Docs: https://docs.railway.app
- DigitalOcean Docs: https://docs.digitalocean.com
- Hetzner: https://www.hetzner.com/cloud
- Render: https://render.com

---

## 🎉 Success!

Ако deployment-ът е успешен, трябва да видиш:
- ✅ API responding на `/health`
- ✅ Dashboard зарежда на `/dashboard`
- ✅ API docs на `/docs`
- ✅ Listings в базата данни
- ✅ Stats endpoint работи

**Готово! Проектът е live!** 🚀

За проблеми или въпроси, провери [Troubleshooting](#-troubleshooting) секцията или отвори issue в GitHub.
