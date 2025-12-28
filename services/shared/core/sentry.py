"""
Sentry Error Monitoring Integration
Provides production error tracking and performance monitoring
"""
import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import os
from core.logging import get_logger

# Conditionally import FastAPI integration (only available in API service)
try:
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

logger = get_logger("sentry")


def init_sentry():
    """
    Initialize Sentry error monitoring

    Environment variables:
        SENTRY_DSN: Sentry Data Source Name (required for monitoring)
        ENVIRONMENT: Deployment environment (production, staging, development)
        RELEASE: Application version/git commit hash
    """
    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        logger.info("⚠️  Sentry DSN not configured - error monitoring disabled")
        return

    environment = os.getenv("ENVIRONMENT", "development")
    release = os.getenv("RELEASE", "unknown")

    try:
        # Build integrations list based on available packages
        integrations = [SqlalchemyIntegration()]

        if FASTAPI_AVAILABLE:
            integrations.append(
                FastApiIntegration(
                    transaction_style="endpoint",  # Group by endpoint path
                    failed_request_status_codes=[500, 501, 502, 503, 504]
                )
            )

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            release=release,

            # Integrations
            integrations=integrations,

            # Performance monitoring
            traces_sample_rate=1.0 if environment == "development" else 0.1,  # 10% in production

            # Error sampling
            sample_rate=1.0,  # Capture 100% of errors

            # Request data
            send_default_pii=False,  # Don't send PII (emails, IPs, etc.)
            max_breadcrumbs=50,      # Context trail before error

            # Performance thresholds
            profiles_sample_rate=0.1 if environment == "production" else 0,  # Profile 10% in prod

            # Filter out common noise
            before_send=filter_sentry_events,
        )

        logger.info(f"✅ Sentry initialized (env={environment}, release={release})")

    except Exception as e:
        logger.error(f"❌ Failed to initialize Sentry: {e}")


def filter_sentry_events(event, hint):
    """
    Filter out noisy/irrelevant errors before sending to Sentry

    Args:
        event: Sentry event dictionary
        hint: Additional context (exception, log record, etc.)

    Returns:
        event if should be sent, None to drop
    """
    # Don't report certain HTTP status codes
    if "request" in event:
        status_code = event.get("request", {}).get("status_code")
        if status_code in [404, 401, 403]:  # Expected client errors
            return None

    # Filter out database connection errors during startup (expected in Railway)
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        error_msg = str(exc_value).lower()

        # Don't report expected database warmup errors
        if "connection refused" in error_msg or "could not connect" in error_msg:
            return None

    return event


def capture_scraper_error(error: Exception, context: dict = None):
    """
    Capture scraper-specific errors with additional context

    Args:
        error: The exception that occurred
        context: Additional context (page number, search term, etc.)
    """
    if not sentry_sdk.Hub.current.client:
        return  # Sentry not initialized

    with sentry_sdk.push_scope() as scope:
        scope.set_context("scraper", context or {})
        scope.set_tag("component", "scraper")
        sentry_sdk.capture_exception(error)


def capture_api_error(error: Exception, endpoint: str, context: dict = None):
    """
    Capture API-specific errors with additional context

    Args:
        error: The exception that occurred
        endpoint: API endpoint path
        context: Additional context (user input, query params, etc.)
    """
    if not sentry_sdk.Hub.current.client:
        return  # Sentry not initialized

    with sentry_sdk.push_scope() as scope:
        scope.set_context("api", {"endpoint": endpoint, **(context or {})})
        scope.set_tag("component", "api")
        sentry_sdk.capture_exception(error)
