#!/usr/bin/env python3
"""
Migration script: SQLite → PostgreSQL

Usage:
    python scripts/migrate_to_postgres.py

This script will:
1. Export data from SQLite
2. Create PostgreSQL tables
3. Import data to PostgreSQL
4. Verify migration success
"""

import os
import sys
import sqlite3
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def log(message: str, level: str = "INFO"):
    """Simple logging"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def main():
    log("🚀 Starting SQLite → PostgreSQL Migration")
    
    # Get URLs
    sqlite_url = os.getenv("DATABASE_URL_SQLITE", "sqlite:///./gpu.db")
    postgres_url = os.getenv("DATABASE_URL")
    
    if not postgres_url or not postgres_url.startswith("postgresql"):
        log("❌ PostgreSQL DATABASE_URL not set", "ERROR")
        log("Set DATABASE_URL environment variable to: postgresql://user:password@host:5432/db", "ERROR")
        sys.exit(1)
    
    # Extract SQLite file path
    if sqlite_url.startswith("sqlite:///"):
        sqlite_file = sqlite_url.replace("sqlite:///", "")
    else:
        sqlite_file = "./gpu.db"
    
    if not Path(sqlite_file).exists():
        log(f"⚠️  SQLite database not found: {sqlite_file}", "WARNING")
        log("Skipping data migration (will create empty PostgreSQL tables)", "INFO")
        step_init_postgres(postgres_url)
        return
    
    log(f"📊 Source: SQLite - {sqlite_file}")
    log(f"📊 Target: PostgreSQL - {postgres_url.split('@')[1] if '@' in postgres_url else 'configured'}")
    
    try:
        # Step 1: Read SQLite schema and data
        log("Step 1: Reading SQLite data...")
        sqlite_data = step_read_sqlite(sqlite_file)
        log(f"✅ Read {len(sqlite_data)} tables from SQLite")
        
        # Step 2: Initialize PostgreSQL
        log("Step 2: Initializing PostgreSQL...")
        step_init_postgres(postgres_url)
        log("✅ PostgreSQL tables created")
        
        # Step 3: Migrate data (if any)
        if sqlite_data:
            log("Step 3: Migrating data...")
            step_migrate_data(postgres_url, sqlite_data)
            log("✅ Data migrated successfully")
        
        # Step 4: Verify
        log("Step 4: Verifying migration...")
        step_verify(postgres_url, sqlite_file)
        
        log("✅ Migration completed successfully!", "SUCCESS")
        
    except Exception as e:
        log(f"❌ Migration failed: {e}", "ERROR")
        log("Rollback your changes and check the error above", "ERROR")
        sys.exit(1)

def step_read_sqlite(sqlite_file: str) -> dict:
    """Read all data from SQLite"""
    try:
        conn = sqlite3.connect(sqlite_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        data = {}
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            data[table] = {
                'columns': [description[0] for description in cursor.description],
                'rows': [dict(row) for row in rows]
            }
            log(f"  - {table}: {len(rows)} records")
        
        conn.close()
        return data
    except Exception as e:
        raise Exception(f"Failed to read SQLite: {e}")

def step_init_postgres(postgres_url: str):
    """Initialize PostgreSQL with table schemas"""
    try:
        from storage.db import engine, Base, init_db
        
        # Create all tables
        init_db()
        
        log("  ✅ All tables created in PostgreSQL")
    except Exception as e:
        raise Exception(f"Failed to initialize PostgreSQL: {e}")

def step_migrate_data(postgres_url: str, sqlite_data: dict):
    """Migrate data from SQLite to PostgreSQL"""
    try:
        from storage.db import SessionLocal
        from storage.orm import GPU
        
        # Try to import optional models
        GPUPriceHistory = None
        try:
            from storage.orm import GPUPriceHistory as GPHModel  # type: ignore
            GPUPriceHistory = GPHModel
        except ImportError:
            pass
        
        session = SessionLocal()
        
        try:
            # Map table names to models (only include available models)
            model_map: dict = {
                'gpu': GPU,
            }
            if GPUPriceHistory:
                model_map['gpu_price_history'] = GPUPriceHistory
            
            for table_name, data in sqlite_data.items():
                if not data['rows']:
                    log(f"  - {table_name}: skipped (empty)")
                    continue
                
                model = model_map.get(table_name)
                if not model:
                    log(f"  - {table_name}: skipped (no model)")
                    continue
                
                # Insert data
                for row_data in data['rows']:
                    # Filter out None values and unknown columns
                    obj_data = {
                        k: v for k, v in row_data.items()
                        if k in [c.name for c in model.__table__.columns]
                    }
                    obj = model(**obj_data)
                    session.add(obj)
                
                session.commit()
                log(f"  ✅ {table_name}: {len(data['rows'])} records migrated")
        finally:
            session.close()
    except Exception as e:
        raise Exception(f"Failed to migrate data: {e}")

def step_verify(postgres_url: str, sqlite_file: str):
    """Verify migration success"""
    try:
        from storage.db import SessionLocal
        from storage.orm import GPU
        
        session = SessionLocal()
        
        try:
            # Check if we have data
            count = session.query(GPU).count()
            log(f"  📊 PostgreSQL GPU table: {count} records")
            
            if count > 0:
                first = session.query(GPU).first()
                if first is not None:
                    log(f"  📝 Sample record: {first.name} - {first.price}₺")
                else:
                    log("  ⚠️  Could not retrieve sample record", "WARNING")
        finally:
            session.close()
    except Exception as e:
        log(f"  ⚠️  Verification warning: {e}", "WARNING")

if __name__ == "__main__":
    main()
