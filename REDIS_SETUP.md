# 🔴 Redis Setup Guide for Railway

## Защо е нужен Redis?

Scraper и API services са в отделни Docker контейнери на Railway. За да споделят rejected listings и други cached данни, трябва общ storage - **Redis**.

## 📋 Setup Instructions

### 1. Добави Redis в Railway

1. Отвори Railway dashboard: https://railway.app/
2. Избери проекта **GPU Price Tracker**
3. Кликни **New** → **Database** → **Add Redis**
4. Redis ще се създаде автоматично

### 2. Свържи Redis към Services

Railway автоматично inject-ва `REDIS_URL` environment variable към всички services в проекта.

**Няма нужда да добавяш ръчно variables!** Кодът вече е конфигуриран да използва `REDIS_URL`.

### 3. Redeploy Services

След като добавиш Redis:

1. **API Service** → **Settings** → **Redeploy**
2. **Scraper Service** → **Settings** → **Redeploy**

Или просто push-ни тези промени към GitHub - Railway ще redeploy автоматично.

### 4. Провери Logs

След redeploy, виж logs-овете:

**Scraper logs:**
```
✅ Redis cache connected successfully
💾 Saved 847 rejected listings to cache
```

**API logs:**
```
✅ Redis cache connected successfully
```

## ✅ Verification

Отвори frontend-а и виж `/rejected` страницата - трябва да видиш стотици rejected listings!

## 🔍 Troubleshooting

### "Redis not installed" warning
- Добави `redis==5.2.2` в `requirements.txt` (вече направено)

### "Redis connection failed"
- Увери се че Redis service работи в Railway dashboard
- Провери че `REDIS_URL` е inject-нат (Railway го прави автоматично)

### Все още няма rejected listings
- Изчакай scraper-а да завърши (виж logs)
- Провери че и двата services използват същия Redis (трябва да е автоматично)

## 📊 Expected Result

След успешен setup:
- ✅ Scraper записва rejected listings в Redis
- ✅ API чете от същия Redis
- ✅ Frontend показва стотици rejected обяви с категории
- ✅ Страницата `/rejected` работи перфектно
