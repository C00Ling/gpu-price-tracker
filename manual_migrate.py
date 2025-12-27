#!/usr/bin/env python3
"""Manual database migration script for Railway"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from storage.db_setup import init_db
from storage.models import Base
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Manually create all database tables"""
    try:
        # Get database URL from environment
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL not set!")
            sys.exit(1)

        logger.info(f"Connecting to database...")
        engine = create_engine(db_url)

        # Drop all tables (fresh start)
        logger.info("Dropping all existing tables...")
        Base.metadata.drop_all(engine)

        # Create all tables
        logger.info("Creating all tables...")
        Base.metadata.create_all(engine)

        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result]
            logger.info(f"Created tables: {tables}")

        logger.info("✅ Database migration completed successfully!")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
