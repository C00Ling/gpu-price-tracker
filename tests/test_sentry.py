"""
Tests for Sentry error monitoring integration
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from core.sentry import init_sentry, filter_sentry_events, capture_scraper_error, capture_api_error


class TestSentryInitialization:
    """Test Sentry initialization with various configurations"""

    @patch('core.sentry.sentry_sdk')
    def test_init_sentry_without_dsn(self, mock_sentry, caplog):
        """Should skip initialization when SENTRY_DSN is not set"""
        with patch.dict(os.environ, {}, clear=True):
            init_sentry()

            # Should not call sentry_sdk.init()
            mock_sentry.init.assert_not_called()

            # Should log warning
            assert "Sentry DSN not configured" in caplog.text

    @patch('core.sentry.sentry_sdk')
    def test_init_sentry_with_dsn(self, mock_sentry):
        """Should initialize Sentry when SENTRY_DSN is provided"""
        test_dsn = "https://example@sentry.io/123"

        with patch.dict(os.environ, {
            'SENTRY_DSN': test_dsn,
            'ENVIRONMENT': 'production',
            'RELEASE': 'v1.0.0'
        }):
            init_sentry()

            # Should call sentry_sdk.init() with correct parameters
            mock_sentry.init.assert_called_once()
            call_kwargs = mock_sentry.init.call_args.kwargs

            assert call_kwargs['dsn'] == test_dsn
            assert call_kwargs['environment'] == 'production'
            assert call_kwargs['release'] == 'v1.0.0'
            assert call_kwargs['sample_rate'] == 1.0
            assert 'integrations' in call_kwargs

    @patch('core.sentry.sentry_sdk')
    def test_init_sentry_development_vs_production(self, mock_sentry):
        """Should use different sample rates for development vs production"""
        test_dsn = "https://example@sentry.io/123"

        # Development
        with patch.dict(os.environ, {
            'SENTRY_DSN': test_dsn,
            'ENVIRONMENT': 'development'
        }):
            init_sentry()
            dev_call = mock_sentry.init.call_args.kwargs
            assert dev_call['traces_sample_rate'] == 1.0  # 100% tracing in dev
            assert dev_call['profiles_sample_rate'] == 0  # No profiling in dev

        mock_sentry.reset_mock()

        # Production
        with patch.dict(os.environ, {
            'SENTRY_DSN': test_dsn,
            'ENVIRONMENT': 'production'
        }):
            init_sentry()
            prod_call = mock_sentry.init.call_args.kwargs
            assert prod_call['traces_sample_rate'] == 0.1  # 10% tracing in prod
            assert prod_call['profiles_sample_rate'] == 0.1  # 10% profiling in prod


class TestSentryEventFiltering:
    """Test event filtering to reduce noise"""

    def test_filter_404_errors(self):
        """Should filter out 404 errors (expected client errors)"""
        event = {
            "request": {
                "status_code": 404
            }
        }
        hint = {}

        result = filter_sentry_events(event, hint)
        assert result is None  # Filtered out

    def test_filter_401_errors(self):
        """Should filter out 401 errors (expected client errors)"""
        event = {
            "request": {
                "status_code": 401
            }
        }
        hint = {}

        result = filter_sentry_events(event, hint)
        assert result is None  # Filtered out

    def test_allow_500_errors(self):
        """Should allow 500 errors (server errors)"""
        event = {
            "request": {
                "status_code": 500
            }
        }
        hint = {}

        result = filter_sentry_events(event, hint)
        assert result == event  # Not filtered

    def test_filter_database_connection_errors(self):
        """Should filter out expected database warmup errors"""
        exc = Exception("connection refused")
        event = {}
        hint = {
            "exc_info": (Exception, exc, None)
        }

        result = filter_sentry_events(event, hint)
        assert result is None  # Filtered out

    def test_allow_other_database_errors(self):
        """Should allow unexpected database errors"""
        exc = Exception("unique constraint violation")
        event = {}
        hint = {
            "exc_info": (Exception, exc, None)
        }

        result = filter_sentry_events(event, hint)
        assert result == event  # Not filtered


class TestSentryErrorCapture:
    """Test error capture helpers"""

    @patch('core.sentry.sentry_sdk')
    def test_capture_scraper_error_with_context(self, mock_sentry):
        """Should capture scraper errors with additional context"""
        # Mock Sentry hub
        mock_hub = MagicMock()
        mock_hub.client = True  # Sentry is initialized
        mock_sentry.Hub.current = mock_hub

        mock_scope = MagicMock()
        mock_sentry.push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
        mock_sentry.push_scope.return_value.__exit__ = MagicMock(return_value=False)

        error = Exception("Scraping failed")
        context = {
            "page": 5,
            "search_term": "rtx 4090"
        }

        capture_scraper_error(error, context)

        # Should set scraper context and tag
        mock_scope.set_context.assert_called_once_with("scraper", context)
        mock_scope.set_tag.assert_called_once_with("component", "scraper")
        mock_sentry.capture_exception.assert_called_once_with(error)

    @patch('core.sentry.sentry_sdk')
    def test_capture_api_error_with_endpoint(self, mock_sentry):
        """Should capture API errors with endpoint information"""
        # Mock Sentry hub
        mock_hub = MagicMock()
        mock_hub.client = True  # Sentry is initialized
        mock_sentry.Hub.current = mock_hub

        mock_scope = MagicMock()
        mock_sentry.push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
        mock_sentry.push_scope.return_value.__exit__ = MagicMock(return_value=False)

        error = Exception("Database query failed")
        endpoint = "/api/stats"
        context = {
            "model": "RTX 4090"
        }

        capture_api_error(error, endpoint, context)

        # Should set API context with endpoint and tag
        expected_context = {"endpoint": endpoint, "model": "RTX 4090"}
        mock_scope.set_context.assert_called_once_with("api", expected_context)
        mock_scope.set_tag.assert_called_once_with("component", "api")
        mock_sentry.capture_exception.assert_called_once_with(error)

    @patch('core.sentry.sentry_sdk')
    def test_capture_error_when_sentry_not_initialized(self, mock_sentry):
        """Should gracefully handle errors when Sentry is not initialized"""
        # Mock Sentry hub with no client (not initialized)
        mock_hub = MagicMock()
        mock_hub.client = None  # Sentry not initialized
        mock_sentry.Hub.current = mock_hub

        error = Exception("Some error")

        # Should not crash when Sentry is not initialized
        capture_scraper_error(error, {})
        capture_api_error(error, "/api/test", {})

        # Should not attempt to capture exceptions
        mock_sentry.capture_exception.assert_not_called()


class TestSentryIntegrations:
    """Test Sentry integration configurations"""

    @patch('core.sentry.sentry_sdk')
    def test_fastapi_integration_configured(self, mock_sentry):
        """Should configure FastAPI integration correctly"""
        from core.sentry import init_sentry

        test_dsn = "https://example@sentry.io/123"

        with patch.dict(os.environ, {'SENTRY_DSN': test_dsn}):
            init_sentry()

            call_kwargs = mock_sentry.init.call_args.kwargs
            integrations = call_kwargs['integrations']

            # Should have at least 2 integrations (SQLAlchemy, FastAPI)
            assert len(integrations) >= 2

            # Check that we have both integrations
            integration_names = [type(i).__name__ for i in integrations]
            assert 'SqlalchemyIntegration' in integration_names
            assert 'FastApiIntegration' in integration_names

    @patch('core.sentry.sentry_sdk')
    def test_pii_not_sent_by_default(self, mock_sentry):
        """Should not send PII (Personally Identifiable Information) by default"""
        test_dsn = "https://example@sentry.io/123"

        with patch.dict(os.environ, {'SENTRY_DSN': test_dsn}):
            init_sentry()

            call_kwargs = mock_sentry.init.call_args.kwargs

            # Should explicitly disable PII
            assert call_kwargs['send_default_pii'] is False
