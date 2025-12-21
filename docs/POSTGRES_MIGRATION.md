# PostgreSQL Migration Guide

## Overview
This guide explains how to migrate from SQLite to PostgreSQL for production deployment.

## Prerequisites

1. **PostgreSQL Server** (version 12+)
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   
   # Docker
   docker run -d --name gpu_postgres \
     -e POSTGRES_DB=gpu_market \
     -e POSTGRES_USER=gpu_user \
     -e POSTGRES_PASSWORD=secure_password \
     -p 5432:5432 \
     postgres:15-alpine
   ```

2. **Python dependencies**
   ```bash
   pip install psycopg2-binary  # PostgreSQL adapter for SQLAlchemy
   ```

## Step-by-Step Migration

### 1. Create PostgreSQL Database

```bash
# Using psql
psql -U postgres
CREATE DATABASE gpu_market;
CREATE USER gpu_user WITH PASSWORD 'secure_password';
ALTER ROLE gpu_user SET client_encoding TO 'utf8';
ALTER ROLE gpu_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE gpu_user SET default_transaction_deferrable TO on;
ALTER ROLE gpu_user SET default_transaction_read_committed TO on;
GRANT ALL PRIVILEGES ON DATABASE gpu_market TO gpu_user;
\q
```

### 2. Update Environment Variables

```bash
# Copy .env.example to .env (if not already done)
cp .env.example .env

# Update .env with PostgreSQL credentials
DATABASE_URL=postgresql://gpu_user:secure_password@localhost:5432/gpu_market
ENVIRONMENT=production
```

### 3. Install PostgreSQL Python Driver

```bash
pip install psycopg2-binary
```

### 4. Run Database Initialization

```python
# Python script to initialize tables
python -c "from storage.db import init_db; init_db()"
```

Or use the provided migration script:

```bash
python scripts/migrate_to_postgres.py
```

### 5. Migrate Data (if existing SQLite data)

```bash
# Run data migration script
python scripts/migrate_data_sqlite_to_postgres.py
```

### 6. Update docker-compose.yml

For development with PostgreSQL:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: gpu_market
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
```

### 7. Update docker-compose.production.yml

Already configured! Just set environment variables:

```bash
export DB_USER=gpu_user
export DB_PASSWORD=secure_password_here
export REDIS_PASSWORD=secure_redis_password_here
docker-compose -f docker-compose.production.yml up -d
```

## Testing the Migration

### 1. Test Connection

```bash
# Test PostgreSQL connection
psql -h localhost -U gpu_user -d gpu_market -c "SELECT version();"
```

### 2. Run API Tests

```bash
pytest tests/test_storage.py -v
```

### 3. Verify Data Integrity

```bash
python scripts/verify_migration.py
```

## Backup Strategy

### Before Migration

```bash
# Backup SQLite database
cp gpu.db gpu.db.backup

# Backup PostgreSQL
pg_dump -U gpu_user -d gpu_market > gpu_market_backup.sql
```

### Scheduled Backups

Add to crontab (every day at 2 AM):

```bash
# PostgreSQL backup
0 2 * * * pg_dump -U gpu_user gpu_market | gzip > /backups/gpu_market_$(date +\%Y\%m\%d).sql.gz

# Keep only last 30 days
0 3 * * * find /backups -name "gpu_market_*.sql.gz" -mtime +30 -delete
```

## Rollback Plan

If something goes wrong:

```bash
# Restore from SQLite backup
cp gpu.db.backup gpu.db

# Update DATABASE_URL back to SQLite
export DATABASE_URL=sqlite:///./gpu.db

# Restart application
docker-compose restart api
```

## Performance Tuning (PostgreSQL)

### Connection Pooling

The updated `storage/db.py` already includes:
- `pool_size=5`: Maximum 5 connections in the pool
- `max_overflow=10`: Allow up to 10 extra connections
- `pool_pre_ping=True`: Test connections before using

Adjust these values based on your concurrent load.

### Query Optimization

Enable query logging:

```bash
# In PostgreSQL, temporarily enable query logging
psql -U postgres -d gpu_market
ALTER SYSTEM SET log_min_duration_statement = 0;
SELECT pg_reload_conf();
```

### Index Creation

Key indexes are created automatically. To verify:

```bash
psql -U gpu_user -d gpu_market
\d gpu_listing
\d gpu_price_history
```

## Monitoring

### PostgreSQL Health

```bash
# Check connections
psql -U gpu_user -d gpu_market -c "SELECT count(*) as total_connections FROM pg_stat_activity;"

# Check database size
psql -U gpu_user -d gpu_market -c "SELECT pg_size_pretty(pg_database_size('gpu_market'));"
```

### Application Logs

JSON structured logs will show PostgreSQL connection status:

```bash
tail -f logs/gpu_service.log | jq .
```

## Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check if port 5432 is open
sudo netstat -tlnp | grep 5432
```

### Permission Denied

```bash
# Reset PostgreSQL user password
psql -U postgres
ALTER USER gpu_user WITH PASSWORD 'new_secure_password';
\q
```

### Out of Memory

PostgreSQL using too much memory?

```bash
# Adjust in postgresql.conf
shared_buffers = 256MB  # Default: 40MB
effective_cache_size = 1GB  # Default: 4GB
```

## References

- [SQLAlchemy PostgreSQL](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Database Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
