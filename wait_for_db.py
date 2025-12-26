#!/usr/bin/env python3
"""
Wait for PostgreSQL to be ready before running migrations.
Retries connection for up to 30 seconds.
"""
import sys
import time
import psycopg2
from urllib.parse import urlparse
import os

def wait_for_postgres(max_retries=30, retry_delay=1):
    """Wait for PostgreSQL to accept connections."""

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set!")
        return False

    # Parse connection string
    parsed = urlparse(database_url)

    print(f"⏳ Waiting for PostgreSQL at {parsed.hostname}:{parsed.port or 5432}...")

    for attempt in range(1, max_retries + 1):
        try:
            # Try to connect
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:],  # Remove leading slash
                connect_timeout=3
            )
            conn.close()
            print(f"✅ PostgreSQL is ready! (took {attempt}s)")
            return True

        except psycopg2.OperationalError as e:
            if attempt < max_retries:
                print(f"   Attempt {attempt}/{max_retries}: Not ready yet, retrying...")
                time.sleep(retry_delay)
            else:
                print(f"❌ PostgreSQL not ready after {max_retries}s")
                print(f"   Error: {e}")
                return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    return False

if __name__ == "__main__":
    success = wait_for_postgres()
    sys.exit(0 if success else 1)
