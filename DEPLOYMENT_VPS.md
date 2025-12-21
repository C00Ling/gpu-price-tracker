# 🖥️ VPS Deployment Guide (DigitalOcean / Hetzner)

## За кого е това?
- Пълен контрол над сървъра
- По-евтино за дългосрочно (€5/месец)
- Може да хоства много проекти

---

## 📋 Option 1: DigitalOcean (Препоръчвам)

### 1. Създай Droplet
```
OS: Ubuntu 22.04 LTS
Plan: Basic ($6/month)
CPU: 1 vCPU
RAM: 1GB
Storage: 25GB SSD
```

### 2. Initial Server Setup

```bash
# SSH към сървъра
ssh root@your_server_ip

# Update system
apt update && apt upgrade -y

# Install essentials
apt install -y python3-pip python3-venv nginx git postgresql postgresql-contrib redis-server

# Create deploy user
adduser deploy
usermod -aG sudo deploy
su - deploy
```

### 3. Clone & Setup Project

```bash
cd /home/deploy
git clone https://github.com/yourusername/gpu_price_tracker.git
cd gpu_price_tracker

# Create venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Setup PostgreSQL

```bash
sudo -u postgres psql

# In PostgreSQL:
CREATE DATABASE gpu_market;
CREATE USER gpu_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE gpu_market TO gpu_user;
\q
```

### 5. Configure Environment

```bash
cp .env.example .env
nano .env

# Update:
ENVIRONMENT=production
DATABASE_URL=postgresql://gpu_user:secure_password_here@localhost:5432/gpu_market
REDIS_ENABLED=true
```

### 6. Setup Systemd Service

```bash
sudo nano /etc/systemd/system/gpu-api.service
```

```ini
[Unit]
Description=GPU Market Service API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=deploy
WorkingDirectory=/home/deploy/gpu_price_tracker
Environment="PATH=/home/deploy/gpu_price_tracker/.venv/bin"
ExecStart=/home/deploy/gpu_price_tracker/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable & start
sudo systemctl daemon-reload
sudo systemctl enable gpu-api
sudo systemctl start gpu-api
sudo systemctl status gpu-api
```

### 7. Setup Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/gpu-market
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend static files
    location /static/ {
        alias /home/deploy/gpu_price_tracker/static/;
    }

    # Frontend assets
    location /assets/ {
        alias /home/deploy/gpu_price_tracker/static/assets/;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/gpu-market /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. Setup SSL (Free HTTPS)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically!
```

### 9. Setup Celery Workers (Optional)

```bash
# Celery worker service
sudo nano /etc/systemd/system/celery-worker.service
```

```ini
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=deploy
WorkingDirectory=/home/deploy/gpu_price_tracker
Environment="PATH=/home/deploy/gpu_price_tracker/.venv/bin"
ExecStart=/home/deploy/gpu_price_tracker/.venv/bin/celery -A jobs.celery_app worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Celery beat service
sudo nano /etc/systemd/system/celery-beat.service
```

```ini
[Unit]
Description=Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=simple
User=deploy
WorkingDirectory=/home/deploy/gpu_price_tracker
Environment="PATH=/home/deploy/gpu_price_tracker/.venv/bin"
ExecStart=/home/deploy/gpu_price_tracker/.venv/bin/celery -A jobs.celery_app beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
```

### 10. Setup Automated Backups

```bash
# Create backup script
nano /home/deploy/backup-db.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/deploy/backups"
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
pg_dump -U gpu_user gpu_market > $BACKUP_DIR/gpu_market_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "gpu_market_*.sql" -mtime +30 -delete
```

```bash
chmod +x /home/deploy/backup-db.sh

# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /home/deploy/backup-db.sh
```

---

## 🔄 Deploy Updates

```bash
cd /home/deploy/gpu_price_tracker
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart gpu-api
```

---

## 📊 Monitoring

### Check logs
```bash
# API logs
sudo journalctl -u gpu-api -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Celery logs
sudo journalctl -u celery-worker -f
```

### System resources
```bash
# CPU & Memory
htop

# Disk space
df -h

# Active connections
ss -tuln
```

---

## 🔐 Security Hardening

```bash
# Firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable

# Fail2ban (защита от brute force)
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

---

## 💰 Cost Comparison

### Hetzner (Евтино)
- €4.15/месец
- 2 vCPU, 4GB RAM
- 40GB SSD

### DigitalOcean
- $6/месец
- 1 vCPU, 1GB RAM
- 25GB SSD

### Linode
- $5/месец
- 1 vCPU, 1GB RAM
- 25GB SSD

---

## ✅ Checklist

- [ ] Сървър създаден
- [ ] SSH достъп работи
- [ ] PostgreSQL инсталиран
- [ ] Redis инсталиран
- [ ] Nginx конфигуриран
- [ ] SSL сертификат setup
- [ ] Systemd service running
- [ ] Backups configured
- [ ] Firewall enabled
- [ ] Monitoring setup

