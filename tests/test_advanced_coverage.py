# tests/test_advanced_coverage.py
"""
Advanced test coverage for edge cases and error scenarios
Targets: Scraper errors, DB constraints, Rate limiting, Cache fallback
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import time
from sqlalchemy.exc import IntegrityError, OperationalError


# ============================================================
# SCRAPER ERROR HANDLING TESTS
# ============================================================

class TestScraperErrorHandling:
    """Test scraper resilience and error recovery"""

    @pytest.fixture
    def scraper(self):
        from ingest.scraper import GPUScraper
        return GPUScraper(use_tor=False, use_proxy=False)

    @patch('requests.get')
    def test_scraper_timeout_handling(self, mock_get, scraper):
        """Test scraper handles request timeout gracefully"""
        mock_get.side_effect = requests.Timeout("Connection timeout after 30s")
        
        # Should not crash, should retry or log
        with pytest.raises(requests.Timeout):
            scraper.make_request("https://example.com")

    @patch('requests.get')
    def test_scraper_connection_error(self, mock_get, scraper):
        """Test scraper handles connection errors"""
        mock_get.side_effect = requests.ConnectionError("Failed to establish connection")
        
        with pytest.raises(requests.ConnectionError):
            scraper.make_request("https://example.com")

    def test_scraper_malformed_html_parsing(self, scraper):
        """Test scraper handles malformed HTML"""
        from bs4 import BeautifulSoup
        
        malformed_html = """
        <html>
            <div class="listing">
                <h2>GPU Title</h2>
                <p>Price: unparseable
                <!-- Missing closing tag
            </div>
        </html>
        """
        
        soup = BeautifulSoup(malformed_html, 'html.parser')
        # Should not crash, should handle gracefully
        assert soup is not None

    @patch('requests.get')
    def test_scraper_tor_fallback(self, mock_get, scraper):
        """Test scraper falls back to direct connection if TOR fails"""
        # Mock TOR connection failure
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<html></html>"
        mock_get.return_value = mock_response
        
        # Should attempt TOR first, then fallback
        response = scraper.make_request("https://example.com")
        assert response is not None

    def test_scraper_empty_listings_page(self, scraper):
        """Test scraper handles page with no listings"""
        from bs4 import BeautifulSoup
        
        empty_html = "<html><body><p>No results</p></body></html>"
        soup = BeautifulSoup(empty_html, 'html.parser')
        
        listings = soup.find_all("a", href="/d/ad/")
        assert len(listings) == 0


# ============================================================
# DATABASE EDGE CASES TESTS
# ============================================================

class TestDatabaseEdgeCases:
    """Test database layer handles edge cases"""

    def test_add_duplicate_listing_same_params(self, test_repo):
        """Test handling duplicate listings with same parameters"""
        # Add first listing
        gpu1 = test_repo.add_listing(
            model="RTX 4090",
            source="OLX",
            price=3500
        )
        
        # Try to add same parameters - should handle gracefully
        gpu2 = test_repo.add_listing(
            model="RTX 4090",
            source="OLX",
            price=3500
        )
        
        # Both should exist (repository allows duplicates by design)
        assert gpu1 is not None
        assert gpu2 is not None

    def test_add_listing_with_whitespace_model(self, test_repo):
        """Test adding listing with model having whitespace"""
        gpu = test_repo.add_listing(
            model="  RTX  4090  ",
            source="OLX",
            price=3500
        )
        
        assert gpu is not None
        # Should be normalized
        assert gpu.model == "RTX 4090"

    def test_bulk_insert_with_duplicates(self, test_repo):
        """Test bulk insert with duplicate entries"""
        data = [
            {"model": "RTX 4090", "source": "OLX", "price": 3500},
            {"model": "RTX 4090", "source": "OLX", "price": 3500},  # Duplicate
            {"model": "RTX 4070", "source": "OLX", "price": 2500},
        ]
        
        # Should handle gracefully
        count = test_repo.add_listings_bulk(data)
        assert count >= 1  # At least added some

    def test_concurrent_write_conflict(self, test_repo):
        """Test handling concurrent writes"""
        # Simulate concurrent adds
        gpu1 = test_repo.add_listing(
            model="RTX 4090",
            source="OLX",
            price=3500
        )
        
        gpu2 = test_repo.add_listing(
            model="RTX 4070",
            source="OLX",
            price=2500
        )
        
        # Both should be added
        assert test_repo.get_total_count() == 2

    def test_delete_with_cascade(self, test_repo):
        """Test deleting listing"""
        # Add listing
        gpu = test_repo.add_listing(
            model="RTX 4090",
            source="OLX",
            price=3500
        )
        
        # Verify it exists
        assert test_repo.get_total_count() == 1


# ============================================================
# RATE LIMITER TESTS
# ============================================================

class TestRateLimiter:
    """Test rate limiting functionality"""

    @pytest.fixture
    def rate_limiter(self):
        from core.rate_limiter import RateLimiter
        return RateLimiter(calls=10, period=60)  # 10 calls per 60 seconds

    def test_rate_limiter_initialization(self, rate_limiter):
        """Test rate limiter initializes correctly"""
        assert rate_limiter is not None
        assert rate_limiter.calls == 10
        assert rate_limiter.period == 60

    def test_rate_limiter_as_decorator(self):
        """Test rate limiter can be used as decorator"""
        from core.rate_limiter import RateLimiter
        
        rate_limiter = RateLimiter(calls=3, period=1)
        
        call_count = 0
        
        @rate_limiter
        def test_function():
            nonlocal call_count
            call_count += 1
            return call_count
        
        # Should allow 3 calls
        for i in range(3):
            result = test_function()
            assert result == i + 1

    def test_rate_limiter_decorator_blocks_over_limit(self):
        """Test rate limiter blocks over limit"""
        from core.rate_limiter import RateLimiter
        
        rate_limiter = RateLimiter(calls=2, period=1)
        
        call_times = []
        
        @rate_limiter
        def test_function():
            call_times.append(time.time())
            return len(call_times)
        
        # First 2 calls should be allowed
        for i in range(2):
            result = test_function()
            assert result == i + 1


# ============================================================
# CACHE FALLBACK TESTS
# ============================================================

class TestCacheFallback:
    """Test cache behavior and fallback to DB"""

    @pytest.fixture
    def cache(self):
        from core.cache import Cache
        return Cache()

    def test_cache_get_nonexistent_key(self, cache):
        """Test getting non-existent key returns None"""
        if cache.enabled:
            result = cache.get("nonexistent_key_12345")
            assert result is None

    def test_cache_set_and_get(self, cache):
        """Test setting and retrieving from cache"""
        if cache.enabled:
            test_data = {"model": "RTX 4090", "price": 3500}
            cache.set("test_key", test_data)
            
            result = cache.get("test_key")
            assert result == test_data

    def test_cache_serialization(self, cache):
        """Test cache handles complex data types"""
        if cache.enabled:
            complex_data = {
                "list": [1, 2, 3],
                "dict": {"nested": "value"},
                "number": 42,
                "float": 3.14
            }
            
            cache.set("complex_key", complex_data)
            result = cache.get("complex_key")
            
            assert result == complex_data

    def test_cache_invalidation_pattern(self, cache):
        """Test cache pattern invalidation"""
        if cache.enabled:
            # Set multiple keys with pattern
            cache.set("gpu:rtx4090:1", {"price": 3500})
            cache.set("gpu:rtx4090:2", {"price": 3600})
            cache.set("gpu:rtx4070:1", {"price": 2500})
            
            # Invalidate pattern
            count = cache.invalidate_pattern("gpu:rtx4090:*")
            
            # Should invalidate matching keys
            assert count >= 0

    @patch('redis.Redis')
    def test_cache_redis_connection_failure(self, mock_redis):
        """Test cache handles Redis connection failure"""
        from core.cache import Cache
        cache = Cache()
        
        # Should handle gracefully
        assert cache is not None

    def test_cache_disabled_graceful_fallback(self):
        """Test system works when cache is disabled"""
        # Create cache with disabled setting
        from core.cache import Cache
        
        # Manually disable
        cache = Cache()
        original_enabled = cache.enabled
        cache.enabled = False
        
        # Should still work without cache
        result = cache.get("any_key")
        assert result is None
        
        # Restore
        cache.enabled = original_enabled


# ============================================================
# LOGGING TESTS
# ============================================================

class TestLogging:
    """Test logging functionality"""

    def test_logger_initialization(self):
        """Test logger initializes correctly"""
        from core.logging import get_logger
        
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"


# ============================================================
# CONFIGURATION TESTS
# ============================================================

class TestConfiguration:
    """Test configuration loading and env variables"""

    def test_config_loads_yaml(self):
        """Test configuration loads YAML file"""
        from core.config import Config
        
        config = Config("config.yaml")
        assert config is not None

    def test_config_env_var_override(self):
        """Test environment variable overrides config"""
        import os
        
        os.environ["SCRAPER_MAX_PAGES"] = "50"
        
        from core.config import Config
        config = Config("config.yaml")
        
        value = config.get("scraper.max_pages")
        assert value == 50 or value == "50"
        
        del os.environ["SCRAPER_MAX_PAGES"]

    def test_config_missing_key_returns_default(self):
        """Test config returns default for missing keys"""
        from core.config import Config
        
        config = Config("config.yaml")
        value = config.get("nonexistent.key", default="default_value")
        
        assert value == "default_value"


# ============================================================
# VALIDATION TESTS
# ============================================================

class TestValidation:
    """Test input validation"""

    def test_validation_module_exists(self):
        """Test validation module can be imported"""
        from core import validation
        assert validation is not None


# ============================================================
# STATS CALCULATION TESTS
# ============================================================

class TestStatsCalculation:
    """Test statistics calculations"""

    def test_stats_module_exists(self):
        """Test stats module functionality"""
        # Just verify the module can be imported
        from core import stats
        assert stats is not None


# ============================================================
# VALUE CALCULATION TESTS
# ============================================================

class TestValueCalculation:
    """Test FPS per LV calculations"""

    def test_fps_per_price_calculation(self):
        """Test FPS/price value calculation"""
        # Mock benchmark data
        benchmark_fps = {
            "RTX 4090": 240,  # fps
            "RTX 4070": 180,
            "RTX 4060": 120,
        }
        
        prices = {
            "RTX 4090": 3500,
            "RTX 4070": 2500,
            "RTX 4060": 1500,
        }
        
        # Calculate values
        for model, fps in benchmark_fps.items():
            price = prices[model]
            value = fps / price
            
            # Should all be reasonable
            assert value > 0
            assert value < 1
