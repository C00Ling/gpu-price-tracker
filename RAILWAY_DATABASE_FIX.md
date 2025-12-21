# 🔧 Railway Database Fix - СПЕШНО!

## ❌ Проблем:
Dashboard е празен защото данните изчезват при всеки redeploy.

## 🎯 Причина:
Използва се SQLite (file-based) вместо PostgreSQL (persistent).

## ✅ Решение:
Добави `DATABASE_URL` environment variable в Railway.

---

## 📋 Стъпки (2 минути):

### 1️⃣ Отвори Railway Dashboard
```
https://railway.app
```

### 2️⃣ Click на "web" service

### 3️⃣ Click на "Variables" tab (горе)

### 4️⃣ Добави тази variable:

**Variable Name:**
```
DATABASE_URL
```

**Variable Value:**
```
${{Postgres.DATABASE_URL}}
```

**ВАЖНО:** Използвай ТОЧНО `${{Postgres.DATABASE_URL}}` - Railway ще го замени автоматично с PostgreSQL connection string!

### 5️⃣ Click "Add" или "Deploy" бутона

Railway ще redeploy-не автоматично (~2 минути).

---

## 6️⃣ След redeploy:

### Пусни scraper отново:
```bash
curl -X POST https://gpubg.up.railway.app/api/trigger-scrape
```

### Провери данните след 3-5 минути:
```bash
curl https://gpubg.up.railway.app/health
```

Трябва да видиш:
```json
{
  "status": "healthy",
  "models_available": 66  ← ТРЯБВА ДА Е > 0!
}
```

---

## 🎉 След това:

Dashboard-ът ще работи с реални данни:
```
https://gpubg.up.railway.app/dashboard
```

---

## ⚠️ Забележки:

1. **PostgreSQL service трябва да е Online** в Railway
2. Данните СЕГА ще се **запазват при redeploy**
3. SQLite се използва само локално за development

---

## 🆘 Ако нещо не работи:

1. Провери Railway logs за грешки
2. Увери се че Postgres service е Online
3. Провери че DATABASE_URL е точно `${{Postgres.DATABASE_URL}}`

---

**Направи това СЕГА и проектът ще работи перфектно!** 🚀
