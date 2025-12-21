#!/bin/bash

# ============================================
# GPU Market Service - Production Deployment
# ============================================

set -e

echo "🚀 GPU Market Service - Production Deployment"
echo "=============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
fi

# 1. Check prerequisites
info "Checking prerequisites..."

command -v docker >/dev/null 2>&1 || error "Docker is not installed"
command -v docker-compose >/dev/null 2>&1 || error "Docker Compose is not installed"
command -v git >/dev/null 2>&1 || error "Git is not installed"

info "✅ All prerequisites met"

# 2. Setup environment
info "Setting up environment..."

if [ ! -f .env.production ]; then
    warn ".env.production not found, creating from template..."
    cat > .env.production << EOF
# Database
DB_USER=gpu_user
DB_PASSWORD=$(openssl rand -base64 32)
DB_NAME=gpu_market

# Redis
REDIS_PASSWORD=$(openssl rand -base64 32)

# Application
SECRET_KEY=$(openssl rand -base64 32)
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000

# Celery
CELERY_BROKER_URL=redis://:REDIS_PASSWORD@redis:6379/0
CELERY_RESULT_BACKEND=redis://:REDIS_PASSWORD@redis:6379/0

# Scraper
SCRAPER_USE_TOR=true
SCRAPER_MAX_PAGES=5
SCRAPER_RATE_LIMIT_REQUESTS_PER_MINUTE=10

# Monitoring
GRAFANA_PASSWORD=$(openssl rand -base64 16)

# Domain (update this!)
DOMAIN=gpumarket.bg
EOF
    warn "⚠️  Please edit .env.production and update DOMAIN and other settings!"
    read -p "Press enter to continue after editing .env.production..."
fi

# Source environment
set -a
source .env.production
set +a

info "✅ Environment configured"

# 3. Setup SSL with Let's Encrypt
info "Setting up SSL certificates..."

if [ ! -d "./ssl" ]; then
    mkdir -p ssl
    
    read -p "Do you want to generate SSL certificates with Let's Encrypt? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Installing Certbot..."
        sudo apt-get update
        sudo apt-get install -y certbot
        
        info "Obtaining SSL certificate for ${DOMAIN}..."
        sudo certbot certonly --standalone \
            -d ${DOMAIN} \
            -d www.${DOMAIN} \
            --email admin@${DOMAIN} \
            --agree-tos \
            --non-interactive
        
        # Copy certificates
        sudo cp /etc/letsencrypt/live/${DOMAIN}/fullchain.pem ssl/
        sudo cp /etc/letsencrypt/live/${DOMAIN}/privkey.pem ssl/
        sudo chown -R $USER:$USER ssl/
        
        # Setup auto-renewal
        sudo crontab -l > /tmp/mycron || true
        echo "0 0 * * 0 certbot renew --quiet && cp /etc/letsencrypt/live/${DOMAIN}/* /opt/gpu-market/ssl/" >> /tmp/mycron
        sudo crontab /tmp/mycron
        rm /tmp/mycron
        
        info "✅ SSL certificates configured"
    else
        warn "⚠️  Skipping SSL setup. Please add certificates manually to ./ssl/"
    fi
else
    info "✅ SSL directory exists"
fi

# 4. Initialize database
info "Initializing database..."

# Start only postgres first
docker-compose -f docker-compose.production.yml up -d postgres redis

info "Waiting for database to be ready..."
sleep 10

# Run migrations (assuming you've set up Alembic)
if [ -d "migrations" ]; then
    info "Running database migrations..."
    docker-compose -f docker-compose.production.yml run --rm api alembic upgrade head
else
    warn "⚠️  No migrations directory found. Creating database schema..."
    docker-compose -f docker-compose.production.yml run --rm api python -c "from storage.db import init_db; init_db()"
fi

info "✅ Database initialized"

# 5. Start all services
info "Starting all services..."

docker-compose -f docker-compose.production.yml up -d

info "Waiting for services to start..."
sleep 15

# 6. Health checks
info "Running health checks..."

for i in {1..10}; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        info "✅ API is healthy"
        break
    fi
    
    if [ $i -eq 10 ]; then
        error "❌ API health check failed after 10 attempts"
    fi
    
    warn "Waiting for API... (attempt $i/10)"
    sleep 3
done

# Check Redis
if docker-compose -f docker-compose.production.yml exec -T redis redis-cli -a ${REDIS_PASSWORD} ping | grep -q PONG; then
    info "✅ Redis is healthy"
else
    error "❌ Redis health check failed"
fi

# Check PostgreSQL
if docker-compose -f docker-compose.production.yml exec -T postgres pg_isready -U ${DB_USER}; then
    info "✅ PostgreSQL is healthy"
else
    error "❌ PostgreSQL health check failed"
fi

# 7. Initial data scrape
read -p "Do you want to run initial data scrape? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    info "Running initial scrape..."
    docker-compose -f docker-compose.production.yml exec -T api python -m ingest.pipeline
    info "✅ Initial scrape completed"
fi

# 8. Setup firewall
read -p "Do you want to configure firewall rules? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    info "Configuring firewall..."
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 22/tcp
    sudo ufw enable
    info "✅ Firewall configured"
fi

# 9. Setup monitoring
info "Setting up monitoring..."

# Add cron job for health monitoring
(crontab -l 2>/dev/null; echo "*/5 * * * * curl -f http://localhost:8000/health || echo 'GPU Market health check failed' | mail -s 'Alert' admin@${DOMAIN}") | crontab -

info "✅ Monitoring configured"

# 10. Summary
echo ""
echo "=============================================="
echo "🎉 Deployment Complete!"
echo "=============================================="
echo ""
info "Services:"
echo "  🌐 Website:    https://${DOMAIN}"
echo "  📖 API Docs:   https://${DOMAIN}/docs"
echo "  🎨 Dashboard:  https://${DOMAIN}/dashboard"
echo "  📊 Grafana:    http://localhost:3000 (admin/${GRAFANA_PASSWORD})"
echo "  🔍 Prometheus: http://localhost:9090"
echo ""
info "Management Commands:"
echo "  View logs:     docker-compose -f docker-compose.production.yml logs -f"
echo "  Restart:       docker-compose -f docker-compose.production.yml restart"
echo "  Stop:          docker-compose -f docker-compose.production.yml down"
echo "  Update:        git pull && docker-compose -f docker-compose.production.yml up -d --build"
echo ""
info "Next Steps:"
echo "  1. Configure DNS to point ${DOMAIN} to this server"
echo "  2. Test all endpoints: https://${DOMAIN}/docs"
echo "  3. Set up monitoring alerts"
echo "  4. Configure backup strategy"
echo "  5. Add team members to Grafana/Prometheus"
echo ""
warn "⚠️  Important: Save your passwords from .env.production!"
echo ""