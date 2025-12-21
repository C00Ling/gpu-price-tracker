# tests/test_core.py
import pytest
import time
from unittest.mock import Mock, patch
import statistics


# ============================================================
# Test core/filters.py
# ============================================================

class TestFilters:
    """Test filtering logic"""

    def test_normalize_model_name(self):
        """Test GPU model name normalization"""
        from core.filters import normalize_model_name

        # Test spacing normalization
        assert normalize_model_name("RTX3060TI") == "RTX 3060 TI"
        assert normalize_model_name("rx6600xt") == "RX 6600 XT"
        assert normalize_model_name("GTX  1660  SUPER") == "GTX 1660 SUPER"

        # Test uppercase
        assert normalize_model_name("rtx 4070") == "RTX 4070"
        assert normalize_model_name("Rx 7900 XtX") == "RX 7900 XTX"

    def test_is_suspicious_listing_broken_gpu(self):
        """Test filtering broken GPUs"""
        from core.filters import is_suspicious_listing

        # Broken GPU keywords
        is_suspicious, reason = is_suspicious_listing(
            "RTX 3060 счупена за части не работи",
            500,
            "RTX 3060",
            all_prices_for_model=[]
        )

        assert is_suspicious is True
        assert "blacklisted keyword" in reason.lower()

    def test_is_suspicious_listing_extremely_low_price(self):
        """Test filtering extremely low prices"""
        from core.filters import is_suspicious_listing

        # Extremely low price (< 50лв)
        is_suspicious, reason = is_suspicious_listing(
            "RTX 4090 Gaming",
            30,
            "RTX 4090",
            all_prices_for_model=[]
        )

        assert is_suspicious is True
        assert "extremely low" in reason.lower()

    def test_is_suspicious_listing_statistical_outlier_low(self):
        """Test statistical outlier detection (too low)"""
        from core.filters import is_suspicious_listing

        # Price that's a statistical outlier (too low)
        normal_prices = [1200.0, 1250.0, 1300.0, 1280.0, 1290.0]

        is_suspicious, reason = is_suspicious_listing(
            "RTX 4070 Gaming",
            200.0,  # Way too low
            "RTX 4070",
            all_prices_for_model=normal_prices
        )

        assert is_suspicious is True
        assert "outlier" in reason.lower()

    def test_is_suspicious_listing_statistical_outlier_high(self):
        """Test statistical outlier detection (too high)"""
        from core.filters import is_suspicious_listing

        # Price that's a statistical outlier (too high)
        normal_prices = [1200.0, 1250.0, 1300.0, 1280.0, 1290.0]

        is_suspicious, reason = is_suspicious_listing(
            "RTX 4070 Gaming",
            5000.0,  # Way too high
            "RTX 4070",
            all_prices_for_model=normal_prices
        )

        assert is_suspicious is True
        assert "outlier" in reason.lower() or "high" in reason.lower()

    def test_is_suspicious_listing_valid(self):
        """Test that valid listings pass"""
        from core.filters import is_suspicious_listing

        # Normal price
        normal_prices = [1200.0, 1250.0, 1300.0, 1280.0, 1290.0]

        is_suspicious, reason = is_suspicious_listing(
            "RTX 4070 Gaming 12GB",
            1275.0,  # Normal price
            "RTX 4070",
            all_prices_for_model=normal_prices
        )

        assert is_suspicious is False

    def test_filter_scraped_data(self, sample_prices_by_model):
        """Test filtering scraped data"""
        from core.filters import filter_scraped_data

        # Add some outliers
        test_data = dict(sample_prices_by_model)
        test_data["RTX 4090"].append(50)  # Too low
        test_data["RTX 4090"].append(10000)  # Too high

        filtered_data, stats = filter_scraped_data(test_data)

        # Should have filtered out some prices
        assert stats["total_filtered"] > 0
        assert stats["total_kept"] < sum(len(v) for v in test_data.values())

        # Filtered data should have fewer prices for RTX 4090
        assert len(filtered_data["RTX 4090"]) < len(test_data["RTX 4090"])


# ============================================================
# Test core/stats.py
# ============================================================

class TestStats:
    """Test statistics calculations"""

    def test_calculate_price_stats(self, sample_prices_by_model):
        """Test calculating price statistics"""
        from core.stats import calculate_price_stats

        stats = calculate_price_stats(sample_prices_by_model)

        # Should have stats for each model
        assert "RTX 4090" in stats
        assert "RTX 4070" in stats

        # Check structure
        rtx_4090_stats = stats["RTX 4090"]
        assert "min" in rtx_4090_stats
        assert "max" in rtx_4090_stats
        assert "median" in rtx_4090_stats
        assert "mean" in rtx_4090_stats
        assert "count" in rtx_4090_stats

    def test_stats_calculations_correct(self):
        """Test that stats calculations are mathematically correct"""
        from core.stats import calculate_price_stats

        test_data = {
            "TEST GPU": [100, 200, 300, 400, 500]
        }

        stats = calculate_price_stats(test_data)
        test_stats = stats["TEST GPU"]

        assert test_stats["min"] == 100
        assert test_stats["max"] == 500
        assert test_stats["median"] == 300
        assert test_stats["mean"] == 300  # (100+200+300+400+500)/5
        assert test_stats["count"] == 5

    def test_stats_single_price(self):
        """Test stats with single price"""
        from core.stats import calculate_price_stats

        test_data = {
            "TEST GPU": [250]
        }

        stats = calculate_price_stats(test_data)
        test_stats = stats["TEST GPU"]

        # All stats should equal the single price
        assert test_stats["min"] == 250
        assert test_stats["max"] == 250
        assert test_stats["median"] == 250
        assert test_stats["mean"] == 250
        assert test_stats["count"] == 1


# ============================================================
# Test core/value.py
# ============================================================

class TestValueAnalysis:
    """Test FPS/лв analysis"""

    def test_calculate_value(self, sample_prices_by_model, sample_benchmark_data):
        """Test calculating GPU value (FPS per лв)"""
        from core.value import calculate_value

        value_data = calculate_value(
            sample_prices_by_model,
            sample_benchmark_data
        )

        # Should return list of tuples
        assert isinstance(value_data, list)

        if len(value_data) > 0:
            # Check structure: (model, fps, price, fps_per_lv)
            first_item = value_data[0]
            assert len(first_item) == 4
            assert isinstance(first_item[0], str)  # model
            assert isinstance(first_item[1], (int, float))  # fps
            assert isinstance(first_item[2], (int, float))  # price
            assert isinstance(first_item[3], (int, float))  # fps_per_lv

            # Value should be sorted descending by fps_per_lv
            if len(value_data) > 1:
                assert value_data[0][3] >= value_data[1][3]

    def test_value_calculation_math(self):
        """Test that value calculations are correct"""
        from core.value import calculate_value

        prices = {
            "TEST GPU": [1000.0]
        }
        benchmarks = {
            "TEST GPU": 100.0
        }

        value_data = calculate_value(prices, benchmarks)

        assert len(value_data) == 1
        model, fps, price, fps_per_lv = value_data[0]

        assert model == "TEST GPU"
        assert fps == 100.0
        assert price == 1000.0
        assert fps_per_lv == 0.1  # 100 / 1000


# ============================================================
# Test core/rate_limiter.py
# ============================================================

class TestRateLimiter:
    """Test rate limiting logic"""

    def test_rate_limiter_basic(self):
        """Test basic rate limiting"""
        from core.rate_limiter import RateLimiter

        # Allow 2 calls per 1 second
        limiter = RateLimiter(calls=2, period=1)

        # First 2 calls should be immediate
        start = time.time()
        limiter.wait()
        limiter.wait()
        elapsed = time.time() - start

        # Should take almost no time
        assert elapsed < 0.1

    def test_rate_limiter_blocks_third_call(self):
        """Test that rate limiter blocks after limit"""
        from core.rate_limiter import RateLimiter

        # Allow 2 calls per 1 second
        limiter = RateLimiter(calls=2, period=1)

        # Make 2 calls
        limiter.wait()
        limiter.wait()

        # Third call should block for ~1 second
        start = time.time()
        limiter.wait()
        elapsed = time.time() - start

        # Should have waited at least 0.9 seconds
        assert elapsed >= 0.9

    def test_retry_on_failure_decorator(self):
        """Test retry decorator"""
        from core.rate_limiter import retry_on_failure

        attempt_count = [0]

        @retry_on_failure(max_retries=3, delay=0.1)
        def failing_function():
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = failing_function()

        assert result == "success"
        assert attempt_count[0] == 3  # Should have tried 3 times

    def test_retry_on_failure_max_retries(self):
        """Test retry decorator with max retries exceeded"""
        from core.rate_limiter import retry_on_failure

        @retry_on_failure(max_retries=2, delay=0.05)
        def always_failing():
            raise ValueError("Always fails")

        # Should raise after max retries
        with pytest.raises(ValueError):
            always_failing()


# ============================================================
# Test core/validation.py
# ============================================================

class TestValidation:
    """Test input validation"""

    def test_validate_price(self):
        """Test price validation"""
        from core.validation import validate_price

        # Valid prices
        assert validate_price(100) is True
        assert validate_price(1000.50) is True

        # Invalid prices
        assert validate_price(-50) is False
        assert validate_price(0) is False
        assert validate_price(None) is False

    def test_validate_model_name(self):
        """Test model name validation"""
        from core.validation import validate_model_name

        # Valid model names
        assert validate_model_name("RTX 4090") is True
        assert validate_model_name("RX 7900 XTX") is True

        # Invalid model names
        assert validate_model_name("") is False
        assert validate_model_name(None) is False
        assert validate_model_name("x") is False  # Too short


# ============================================================
# Test core/config.py
# ============================================================

class TestConfig:
    """Test configuration management"""

    def test_config_loads(self):
        """Test that config loads without errors"""
        from core.config import config

        # Should have loaded successfully
        assert config is not None

    def test_config_get_method(self):
        """Test config.get() method"""
        from core.config import config

        # Test getting existing value
        value = config.get("database.url")
        assert value is not None

        # Test getting with default
        value = config.get("nonexistent.key", default="default_value")
        assert value == "default_value"

    def test_config_has_required_keys(self):
        """Test that config has required keys"""
        from core.config import config

        # Required keys should exist
        assert config.get("database") is not None
        assert config.get("scraper") is not None
        assert config.get("api") is not None
