# 🚀 Quick Start Guide - Multi-Service Architecture

Стартирай GPU Price Tracker за **2 минути** с Docker Compose.

## 📋 Предварителни изисквания

- Docker (20.10+)
- Docker Compose (1.29+)
- 2GB свободна RAM памет
- 1GB свободно дисково пространство

## ⚡ Бърз старт (2 минути)

```bash
# 1. Клонирай проекта
git clone https://github.com/yourusername/gpu_price_tracker.git
cd gpu_price_tracker

# 2. Стартирай всички services
docker-compose up -d

# 3. Провери дали всичко работи
./verify-setup.sh

# 4. Отвори приложението
open http://localhost:8000
```

Готово! Приложението работи.

## 🎯 Какво работи?

```
┌──────────────────────────────────────────┐
│   Твоята GPU Price Tracker система       │
├──────────────────────────────────────────┤
│                                          │
│  ✅ PostgreSQL Database (port 5432)     │
│  ✅ API Service (http://localhost:8000) │
│  ✅ Scraper Worker (background daemon)  │
│  ✅ TOR Proxy (за анонимен scraping)    │
│                                          │
└──────────────────────────────────────────┘
```

## 🌐 Достъп до приложението

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Database**: `psql postgresql://postgres:postgres@localhost:5432/gpu_tracker`

## 🎮 Основни команди

```bash
# Виж logs (всички services)
docker-compose logs -f

# Виж logs (конкретен service)
docker-compose logs -f api
docker-compose logs -f scraper

# Провери статус
docker-compose ps

# Рестартирай service
docker-compose restart api

# Спри всички services
docker-compose down

# Rebuild и рестарт
docker-compose up -d --build

# Пусни scrape веднага (не чакай)
docker-compose run --rm -e WORKER_MODE=oneshot scraper
```

## 📊 Първоначално събиране на данни

Scraper-ът работи автоматично всеки **1 час** (development) или **6 часа** (production).

**За данни веднага:**
```bash
# Пусни еднократен scrape
docker-compose run --rm -e WORKER_MODE=oneshot scraper

# Виж прогреса
docker-compose logs -f scraper
```

**Очакван output:**
```
🔧 Starting TOR service...
✅ TOR service is running
🗄️ Waiting for PostgreSQL...
✅ Database connection verified
🚀 STARTING SCRAPER WORKER
🔍 STARTING SCRAPING CYCLE
   Scraping OLX.bg (7 search terms)...
   Found 1308 listings
   Applying quality filters...
   Saving to database...
✅ SCRAPING COMPLETED SUCCESSFULLY
```

## ✅ Провери че всичко работи

```bash
# 1. Пусни verification script
./verify-setup.sh

# 2. Провери API health
curl http://localhost:8000/health

# 3. Вземи GPU listings
curl http://localhost:8000/api/listings/ | jq

# 4. Вземи най-добрите GPU по стойност
curl http://localhost:8000/api/value/top/10 | jq
```

## ⚙️ Конфигурация

**Default настройките работят веднага!**

Опционална персонализация:

```bash
# Копирай example configs
cp services/api/.env.example services/api/.env
cp services/scraper/.env.example services/scraper/.env

# Редактирай ако е нужно
nano services/api/.env
nano services/scraper/.env

# Рестартирай services
docker-compose restart
```

## 🆘 Troubleshooting

### Port 8000 е зает

```bash
# Намери и убий процеса
lsof -ti:8000 | xargs kill -9

# Или използвай друг port в docker-compose.yml
ports:
  - "8001:8000"
```

### Services не стартират

```bash
# Виж logs
docker-compose logs

# Рестартирай всичко
docker-compose down
docker-compose up -d
```

### Database connection грешки

```bash
# Рестартирай PostgreSQL
docker-compose restart postgres

# Провери дали PostgreSQL работи
docker-compose exec postgres pg_isready -U postgres
```

### Няма данни в базата

```bash
# Изчакай scraper да завърши първия цикъл (1 час)
# ИЛИ пусни scrape веднага:
docker-compose run --rm -e WORKER_MODE=oneshot scraper

# Виж scraper logs
docker-compose logs scraper
```

## 🏗️ Архитектура

```
services/
├── api/           # Read-only HTTP server (FastAPI)
├── scraper/       # Background worker (TOR + scraping)
└── shared/        # Споделени библиотеки

docker-compose.yml # Multi-service orchestration
```

**Ключови features:**
- ✅ Разделени API и Scraper services
- ✅ Независимо scaling (API horizontal, Scraper fixed)
- ✅ PostgreSQL за production storage
- ✅ TOR proxy за анонимен scraping
- ✅ Graceful shutdown (без загуба на данни)
- ✅ Health checks и monitoring

## 🛠️ Development

```bash
# Наблюдавай logs по време на development
docker-compose logs -f

# Rebuild след code промени
docker-compose up -d --build

# Достъп до database
docker-compose exec postgres psql -U postgres -d gpu_tracker

# Изпълни команди в containers
docker-compose exec api bash
docker-compose exec scraper bash
```

## 🚀 Production Deployment

За production deployment на Railway (5 минути):

```bash
# Виж пълното ръководство
cat deployments/railway/README.md

# Или deploy с Railway CLI
railway login
railway init
# Add PostgreSQL + API Service + Scraper Worker
```

**Railway Architecture:**
```
Railway Project
├─ PostgreSQL Database (managed)
├─ API Service (1-3 replicas, auto-scaling)
└─ Scraper Worker (1 replica, daemon mode)
```

**Цена:** $0-5/месец с безплатен $5 credit

## 📚 Научи повече

- **Architecture Details**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Migration Guide**: [MIGRATION.md](MIGRATION.md) (от стария monolith)
- **Railway Deployment**: [deployments/railway/README.md](deployments/railway/README.md)
- **Main Documentation**: [README.md](README.md)

## 📡 API Примери

```bash
# Вземи всички listings
curl http://localhost:8000/api/listings/

# Вземи listings за конкретно GPU
curl http://localhost:8000/api/listings/RTX%204070

# Вземи price statistics
curl http://localhost:8000/api/stats/

# Вземи най-добрите GPU (FPS per лв)
curl http://localhost:8000/api/value/

# Вземи топ 10 най-добри
curl http://localhost:8000/api/value/top/10

# Вземи наличните GPU models
curl http://localhost:8000/api/listings/models/list

# Вземи общ брой listings
curl http://localhost:8000/api/listings/count/total
```

## 🎯 Следващи стъпки

1. ✅ **Стартирай services**: `docker-compose up -d`
2. ✅ **Провери setup**: `./verify-setup.sh`
3. ✅ **Отвори API**: http://localhost:8000
4. ✅ **Виж docs**: http://localhost:8000/docs
5. ✅ **Прочети architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
6. ✅ **Deploy на production**: [deployments/railway/README.md](deployments/railway/README.md)

## ❓ Въпроси?

- Отвори issue на GitHub
- Прочети [README.md](README.md) за детайлна документация
- Виж [ARCHITECTURE.md](ARCHITECTURE.md) за system design
- Виж [MIGRATION.md](MIGRATION.md) ако upgrade-ваш от старата версия

---

**Добре дошъл в GPU Price Tracker! 🚀**

Професионалната multi-service архитектура за анализ на GPU цени в България.
