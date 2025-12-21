# 🚀 Quick Start Guide

Това е кратко ръководство за стартиране на GPU Market Service на локална машина.

## 📋 Предварителни изисквания

- Python 3.11+
- pip
- Git (optional)

## ⚡ Бърз старт (1 минута)

### 1. Клонирай проекта (ако още не е)
```bash
git clone https://github.com/yourusername/gpu_price_tracker.git
cd gpu_price_tracker
```

### 2. Пусни автоматичния setup
```bash
./quickstart.sh
```

Това ще:
- ✅ Създаде virtual environment
- ✅ Инсталира dependencies
- ✅ Създаде SQLite database
- ✅ Пусне тестовете

### 3. Стартирай API сървъра
```bash
source .venv/bin/activate  # Активирай venv ако не е
python main.py
```

### 4. Отвори браузър
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8000/dashboard
- **Health Check**: http://localhost:8000/health

## 🎯 Основни команди

### Стартиране на API
```bash
python main.py
# или
uvicorn main:app --reload
```

### Пускане на scraper
```bash
python -m ingest.pipeline
```

### Тестове
```bash
# Всички тестове
pytest tests/ -v

# Конкретен файл
pytest tests/test_api.py -v

# С coverage
pytest tests/ --cov=. --cov-report=html
```

### Celery worker (за background tasks)
```bash
# Терминал 1: Redis
docker run -p 6379:6379 redis:alpine

# Терминал 2: Celery worker
celery -A jobs.celery_app worker --loglevel=info

# Терминал 3: Celery beat (scheduler)
celery -A jobs.celery_app beat --loglevel=info
```

## 🐳 Docker (препоръчва се за production)

### Development mode
```bash
docker-compose up
```

### Production mode
```bash
docker-compose -f docker-compose.production.yml up -d
```

## 📚 Пълна документация

За повече детайли вижте [README.md](README.md)

## 🆘 Troubleshooting

### Import errors
```bash
# Увери се че venv е активиран
source .venv/bin/activate

# Инсталирай dependencies отново
pip install -r requirements.txt
```

### Database errors
```bash
# Изтрий и създай отново
rm gpu.db
python -c "from storage.db import init_db; init_db()"
```

### Port вече е зает
```bash
# Провери кой процес използва порт 8000
lsof -i :8000

# Убий процеса
kill -9 <PID>
```

## ✅ Проверка че всичко работи

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. API endpoint
curl http://localhost:8000/api/listings/

# 3. Stats
curl http://localhost:8000/api/stats/
```

Ако всичко работи - готово! 🎉
