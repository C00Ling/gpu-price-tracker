"""
Scraper Worker Service
Autonomous cron-based worker for GPU data collection
Runs independently from API service
"""
import sys
import os
import signal
import time
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from ingest.pipeline import run_pipeline
from storage.db import init_db
from core.logging import get_logger
from core.sentry import init_sentry, capture_scraper_error

# Setup logger
logger = get_logger("scraper_worker")

# Graceful shutdown handling
shutdown_requested = False


def handle_shutdown_signal(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info(f"🛑 Received shutdown signal {signum}")
    logger.info("🕐 Will complete current scraping and then shutdown...")
    shutdown_requested = True


# Register signal handlers for graceful shutdown
signal.signal(signal.SIGTERM, handle_shutdown_signal)
signal.signal(signal.SIGINT, handle_shutdown_signal)


def check_database_connection(max_retries=10, retry_interval=5):
    """Check if database is accessible"""
    logger.info("🗄️  Checking database connection...")

    for attempt in range(1, max_retries + 1):
        try:
            init_db()
            logger.info("✅ Database connection established")
            return True
        except Exception as e:
            if attempt < max_retries:
                logger.warning(
                    f"⏳ Database not ready (attempt {attempt}/{max_retries}): {e}"
                )
                logger.info(f"   Retrying in {retry_interval}s...")
                time.sleep(retry_interval)
            else:
                logger.error(f"❌ Database connection failed after {max_retries} attempts")
                return False

    return False


def run_single_scrape():
    """Run a single scraping cycle"""
    logger.info("=" * 70)
    logger.info("🔍 STARTING SCRAPING CYCLE")
    logger.info(f"⏰ Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 70)

    start_time = time.time()

    try:
        # Run the pipeline (with retry logic built-in)
        success = run_pipeline(ws_manager=None)  # No WebSocket in worker mode

        duration = time.time() - start_time

        if success:
            logger.info("=" * 70)
            logger.info(f"✅ SCRAPING COMPLETED SUCCESSFULLY (took {duration:.1f}s)")
            logger.info("=" * 70)
            return True
        else:
            logger.warning("=" * 70)
            logger.warning(f"⚠️  SCRAPING COMPLETED WITH WARNINGS (took {duration:.1f}s)")
            logger.warning("=" * 70)
            return False

    except Exception as e:
        duration = time.time() - start_time
        logger.error("=" * 70)
        logger.error(f"❌ SCRAPING FAILED: {e} (took {duration:.1f}s)")
        logger.error("=" * 70)

        # Capture error in Sentry
        capture_scraper_error(e, context={
            "mode": "worker",
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        })

        return False


def run_worker_daemon():
    """Run as a long-lived daemon with periodic scraping"""
    logger.info("=" * 70)
    logger.info("🤖 SCRAPER WORKER DAEMON MODE")
    logger.info("=" * 70)

    # Get scraping interval from environment (default: 6 hours)
    scrape_interval = int(os.getenv("SCRAPE_INTERVAL_SECONDS", "21600"))  # 6 hours
    logger.info(f"⏰ Scraping interval: {scrape_interval}s ({scrape_interval/3600:.1f}h)")

    cycle_count = 0

    while not shutdown_requested:
        cycle_count += 1
        logger.info(f"🔄 Scraping cycle #{cycle_count}")

        run_single_scrape()

        if shutdown_requested:
            logger.info("🛑 Shutdown requested, exiting daemon loop")
            break

        # Wait for next cycle
        logger.info(f"😴 Sleeping for {scrape_interval}s until next cycle...")

        # Sleep in small intervals to allow quick shutdown
        sleep_intervals = scrape_interval // 10
        for i in range(sleep_intervals):
            if shutdown_requested:
                logger.info("🛑 Shutdown requested during sleep, exiting")
                break
            time.sleep(10)

        # Sleep remaining time
        remaining_sleep = scrape_interval % 10
        if remaining_sleep > 0 and not shutdown_requested:
            time.sleep(remaining_sleep)

    logger.info("👋 Worker daemon shutting down gracefully")


def run_worker_oneshot():
    """Run a single scraping cycle and exit (for cron mode)"""
    logger.info("=" * 70)
    logger.info("🎯 SCRAPER WORKER ONE-SHOT MODE")
    logger.info("=" * 70)

    success = run_single_scrape()

    if success:
        logger.info("👋 One-shot scraping completed successfully, exiting")
        sys.exit(0)
    else:
        logger.warning("👋 One-shot scraping completed with warnings/errors, exiting")
        sys.exit(1)


def main():
    """Main entry point"""
    logger.info("=" * 70)
    logger.info("🚀 SCRAPER WORKER SERVICE STARTING")
    logger.info("=" * 70)
    logger.info(f"📝 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"🔧 Mode: {os.getenv('WORKER_MODE', 'oneshot')}")

    # Initialize Sentry error monitoring
    init_sentry()

    # Check database connection
    if not check_database_connection():
        logger.error("❌ Cannot proceed without database connection")
        sys.exit(1)

    # Determine worker mode
    mode = os.getenv("WORKER_MODE", "oneshot").lower()

    if mode == "daemon":
        logger.info("🤖 Starting in DAEMON mode (continuous scraping)")
        run_worker_daemon()
    else:
        logger.info("🎯 Starting in ONE-SHOT mode (single scrape + exit)")
        run_worker_oneshot()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⚠️  Worker stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Worker crashed: {e}", exc_info=True)

        # Capture critical error
        capture_scraper_error(e, context={
            "mode": "crash",
            "timestamp": datetime.now().isoformat()
        })

        sys.exit(1)
