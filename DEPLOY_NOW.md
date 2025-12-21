# 🚀 Deploy to Railway - Step by Step

Проектът е готов! Следвай тези стъпки:

---

## ✅ Вече готово (направено от мен):
- ✅ Git repo инициализиран
- ✅ Всички файлове commit-нати
- ✅ Railway конфигурация създадена
- ✅ 124 теста минават
- ✅ Production ready

---

## 📝 Следващи стъпки (ТИ):

### 1️⃣ Създай GitHub Repository (2 минути)

#### Отвори GitHub:
```
https://github.com/new
```

#### Попълни:
- **Repository name:** `gpu-price-tracker`
- **Description:** "GPU Market Service - Price tracking & analytics for Bulgarian market"
- **Visibility:** Public (или Private ако искаш)
- **DON'T initialize** with README/gitignore (вече имаме!)

#### Click "Create repository"

---

### 2️⃣ Push към GitHub (30 секунди)

Копирай командите от GitHub (ще са примерно така):

```bash
cd /home/petar/Desktop/gpu_price_tracker

# Добави remote (ЗАМЕНИ с ТВОЯ username!)
git remote add origin https://github.com/ТВОЯ-USERNAME/gpu-price-tracker.git

# Push
git push -u origin main
```

Ще ти иска GitHub credentials.

**✅ Проверка:** Refresh GitHub page - трябва да видиш всички файлове!

---

### 3️⃣ Deploy на Railway (3 минути)

#### A. Отвори Railway:
```
https://railway.app
```

#### B. Sign Up / Login:
- Click "Login"
- Избери "Login with GitHub"
- Авторизирай Railway да вижда repos

#### C. Create New Project:
1. Click "New Project"
2. Click "Deploy from GitHub repo"
3. Избери `gpu-price-tracker`
4. Railway започва автоматичен build!

#### D. Добави PostgreSQL:
1. В Railway dashboard → Click "New"
2. Click "Database" → "Add PostgreSQL"
3. PostgreSQL се създава автоматично!
4. Railway автоматично добавя `DATABASE_URL`

#### E. Добави Redis (Optional):
1. Click "New" → "Database" → "Add Redis"
2. Railway добавя `REDIS_URL`

#### F. Конфигурирай Environment Variables:
1. Click на API service → "Variables"
2. Добави:

```env
ENVIRONMENT=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_ENABLED=true
REDIS_URL=${{Redis.REDIS_URL}}
PORT=${{PORT}}

# Scraper settings
SCRAPER_MAX_PAGES=5
SCRAPER_DELAY=2

# Optional: Secret key
SECRET_KEY=your-super-secret-key-here-change-me
```

#### G. Deploy!
Railway автоматично deploy-ва! Виж Logs tab за прогрес.

---

### 4️⃣ Get Your URL! (1 минута)

#### A. Generate Domain:
1. Click на API service
2. Click "Settings"
3. Scroll до "Domains"
4. Click "Generate Domain"

#### B. URL ще е примерно:
```
https://gpu-price-tracker-production-xxxx.up.railway.app
```

#### C. Тествай!
```bash
# Health check
curl https://твоя-url.railway.app/health

# API docs
https://твоя-url.railway.app/docs

# Dashboard
https://твоя-url.railway.app/dashboard
```

---

## 🎉 SUCCESS!

Ако всичко работи - **ГОТОВО!** Проектът е live!

---

## 🔧 Optional: Custom Domain

Ако искаш да използваш твой домейн (напр. `gpu-tracker.com`):

1. Railway → Settings → Domains → "Custom Domain"
2. Въведи домейна
3. Update DNS:
   ```
   CNAME @ твоя-url.railway.app
   ```
4. Изчакай DNS propagation (5-30 мин)

---

## 🔄 Future Updates

Всеки път като промениш код:

```bash
git add .
git commit -m "Update feature X"
git push
```

Railway автоматично deploy-ва новата версия! 🚀

---

## 📊 Monitor

Railway Dashboard показва:
- ✅ Logs (real-time)
- ✅ Metrics (CPU, RAM, Network)
- ✅ Deployments history
- ✅ Database stats

---

## 💰 Cost

### Free Tier:
- $5 credit/месец
- Достатъчно за тестване
- ~500 часа runtime

### Hobby:
- $5/месец + usage
- Unlimited builds
- Better performance

---

## 🆘 Troubleshooting

### Build fails:
- Check Logs tab
- Verify requirements.txt
- Check Python version

### Database connection error:
- Verify PostgreSQL service running
- Check DATABASE_URL variable set

### Out of credits:
- Add payment method
- Upgrade to Hobby plan

---

## 📞 Support

- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app
- GitHub Issues: твоя-repo/issues

---

## 🎯 Next Steps After Deploy

1. ✅ Пусни първи scrape:
   ```bash
   # SSH to Railway (or use Railway CLI)
   python -m ingest.pipeline
   ```

2. ✅ Setup Celery worker за auto-scraping (optional)

3. ✅ Setup monitoring (Sentry, etc.)

4. ✅ Add custom domain

5. ✅ Share with the world! 🌍

---

**Built with ❤️ - Deployed in 10 minutes!**
