# jobs/tasks.py
"""
Celery tasks for scheduled operations
"""
from typing import Optional
from jobs.celery_app import app
from core.logging import get_logger
from core.cache import cache
from storage.db import SessionLocal
from storage.repo import GPURepository
from ingest.pipeline import run_pipeline
import asyncio

logger = get_logger("tasks")


def broadcast_websocket(message_type: str, data: Optional[dict] = None):
    """Helper to broadcast WebSocket messages from sync context"""
    try:
        from core.websocket import manager
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        if message_type == "scrape_started":
            loop.run_until_complete(manager.broadcast_scrape_started())
        elif message_type == "scrape_completed":
            loop.run_until_complete(manager.broadcast_scrape_completed(data or {}))
        elif message_type == "stats_update":
            loop.run_until_complete(manager.broadcast_stats_update(data or {}))

        loop.close()
    except Exception as e:
        logger.error(f"WebSocket broadcast failed: {e}")


@app.task(name="jobs.tasks.scheduled_scrape", bind=True, max_retries=3)
def scheduled_scrape(self):
    """
    Scheduled task to scrape OLX and update database
    Runs every 6 hours
    """
    try:
        logger.info("🕐 Starting scheduled scrape task...")

        # Notify WebSocket clients that scraping started
        broadcast_websocket("scrape_started")

        # Run the scraping pipeline
        run_pipeline()

        # Get summary stats
        session = SessionLocal()
        try:
            repo = GPURepository(session)
            total_count = repo.get_total_count()
            models_count = len(repo.get_models())
            summary = {
                "total_listings": total_count,
                "unique_models": models_count
            }
        finally:
            session.close()

        # Invalidate all cache after new data
        cache.invalidate_pattern("stats:*")
        cache.invalidate_pattern("value:*")

        # Notify WebSocket clients that scraping completed
        broadcast_websocket("scrape_completed", summary)

        logger.info("✅ Scheduled scrape completed successfully")
        return {"status": "success", "message": "Scrape completed", "summary": summary}

    except Exception as e:
        logger.error(f"❌ Scheduled scrape failed: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@app.task(name="jobs.tasks.cleanup_cache")
def cleanup_cache():
    """
    Daily cache cleanup task
    Runs every day at 3 AM UTC
    """
    try:
        logger.info("🧹 Starting cache cleanup...")

        # Redis handles expiration automatically, but we can add custom logic here
        # For now, just log
        logger.info("✅ Cache cleanup completed")
        return {"status": "success"}

    except Exception as e:
        logger.error(f"❌ Cache cleanup failed: {e}")
        return {"status": "error", "message": str(e)}


@app.task(name="jobs.tasks.update_stats_cache")
def update_stats_cache():
    """
    Hourly task to refresh statistics cache
    Pre-warms cache for frequently accessed endpoints
    """
    try:
        logger.info("📊 Updating stats cache...")

        session = SessionLocal()
        try:
            repo = GPURepository(session)

            # Get all models stats
            models = repo.get_models()
            stats = {}
            for model in models:
                model_stats = repo.get_price_stats(model)
                if model_stats:
                    stats[model] = model_stats

            # Cache all models stats
            cache.set("stats:all_models", stats, ttl=3600)

            # Calculate and cache summary
            all_listings = repo.get_all_listings()
            if all_listings:
                # Convert to float explicitly to avoid SQLAlchemy type issues
                prices = [float(listing.price) for listing in all_listings]  # type: ignore
                avg_price = sum(prices) / len(prices)
                summary = {
                    "total_listings": len(all_listings),
                    "unique_models": len(set(l.model for l in all_listings)),
                    "avg_price": round(avg_price, 2)
                }
                cache.set("stats:summary", summary, ttl=3600)

                # Broadcast stats update via WebSocket
                broadcast_websocket("stats_update", summary)

            logger.info(f"✅ Stats cache updated for {len(models)} models")
            return {"status": "success", "models_count": len(models)}

        finally:
            session.close()

    except Exception as e:
        logger.error(f"❌ Stats cache update failed: {e}")
        return {"status": "error", "message": str(e)}


@app.task(name="jobs.tasks.check_price_drops", bind=True)
def check_price_drops(self, threshold_percent=10):
    """
    Check for significant price drops and trigger notifications

    Args:
        threshold_percent: Minimum price drop percentage to trigger notification
    """
    try:
        logger.info(f"💰 Checking for price drops (threshold: {threshold_percent}%)...")

        from storage.price_history import PriceHistoryTracker
        from core.notifications import notifier
        from core.websocket import manager

        session = SessionLocal()
        try:
            tracker = PriceHistoryTracker(session)

            # Detect price drops
            drops = tracker.detect_price_drops(threshold_percent=threshold_percent)

            if drops:
                logger.info(f"🎯 Found {len(drops)} price drops!")

                # Send notifications for each drop
                for model, old_price, new_price, drop_percent in drops:
                    # WebSocket broadcast
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        manager.broadcast_price_drop(model, old_price, new_price)
                    )

                    # Email/Telegram notifications
                    loop.run_until_complete(
                        notifier.notify_price_drop(model, old_price, new_price)
                    )
                    loop.close()

                    logger.info(
                        f"📢 Notified about {model}: "
                        f"{old_price:.2f}лв → {new_price:.2f}лв (-{drop_percent:.1f}%)"
                    )

            logger.info(f"✅ Price drop check completed - {len(drops)} drops found")
            return {"status": "success", "drops_found": len(drops)}

        finally:
            session.close()

    except Exception as e:
        logger.error(f"❌ Price drop check failed: {e}")
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes
