"""
Tests for ingest/scraper.py - GPU model extraction and scraping logic
"""
import pytest
from ingest.scraper import GPUScraper


class TestGPUExtraction:
    """Test GPU model extraction from listing titles"""

    @pytest.fixture
    def scraper(self):
        """Create scraper instance for tests"""
        return GPUScraper(use_tor=False)

    # ===== NVIDIA RTX =====
    def test_extract_rtx_basic(self, scraper):
        """Test basic RTX extraction"""
        # Note: MODEL_CORRECTIONS changes "RTX 3060" → "RTX 3060 TI"
        assert scraper.extract_gpu_model("RTX 3060") == "RTX 3060 TI"
        assert scraper.extract_gpu_model("RTX3060") == "RTX 3060 TI"
        assert scraper.extract_gpu_model("nvidia rtx 3060") == "RTX 3060 TI"

    def test_extract_rtx_ti(self, scraper):
        """Test RTX TI extraction"""
        assert scraper.extract_gpu_model("RTX 3060 TI") == "RTX 3060 TI"
        assert scraper.extract_gpu_model("RTX3060TI") == "RTX 3060 TI"
        assert scraper.extract_gpu_model("GeForce RTX 3060 Ti") == "RTX 3060 TI"

    def test_extract_rtx_super(self, scraper):
        """Test RTX SUPER extraction"""
        assert scraper.extract_gpu_model("RTX 2060 SUPER") == "RTX 2060 SUPER"
        assert scraper.extract_gpu_model("RTX4070 SUPER") == "RTX 4070 SUPER"
        
    def test_extract_rtx_from_real_titles(self, scraper):
        """Test RTX extraction from real OLX-style titles"""
        titles = [
            "Продавам RTX 3060 12GB в отлично състояние",
            "NVIDIA GeForce RTX 3060 Ti 8GB - нова",
            "RTX 4070 SUPER gaming видео карта",
            "rtx 3080 10gb founders edition",
        ]
        expected = ["RTX 3060 TI", "RTX 3060 TI", "RTX 4070 SUPER", "RTX 3080"]
        
        for title, exp in zip(titles, expected):
            assert scraper.extract_gpu_model(title) == exp

    # ===== NVIDIA GTX =====
    def test_extract_gtx_basic(self, scraper):
        """Test basic GTX extraction"""
        assert scraper.extract_gpu_model("GTX 1660") == "GTX 1660 SUPER"
        assert scraper.extract_gpu_model("GTX1660") == "GTX 1660 SUPER"
        assert scraper.extract_gpu_model("gtx 1060") == "GTX 1060 6GB"

    def test_extract_gtx_ti(self, scraper):
        """Test GTX TI extraction"""
        assert scraper.extract_gpu_model("GTX 1080 TI") == "GTX 1080 TI"
        assert scraper.extract_gpu_model("GTX1080TI") == "GTX 1080 TI"

    def test_extract_gtx_super(self, scraper):
        """Test GTX SUPER extraction"""
        assert scraper.extract_gpu_model("GTX 1660 SUPER") == "GTX 1660 SUPER"
        assert scraper.extract_gpu_model("GTX1650SUPER") == "GTX 1650 SUPER"

    def test_extract_gtx_from_real_titles(self, scraper):
        """Test GTX extraction from real OLX-style titles"""
        titles = [
            "Продавам GTX 1080 Ti 11GB",
            "nvidia gtx 1660 super 6gb oc",
            "GTX 1060 6GB gaming",
        ]
        expected = ["GTX 1080 TI", "GTX 1660 SUPER", "GTX 1060 6GB"]
        
        for title, exp in zip(titles, expected):
            assert scraper.extract_gpu_model(title) == exp

    # ===== AMD RX =====
    def test_extract_rx_basic(self, scraper):
        """Test basic RX extraction"""
        assert scraper.extract_gpu_model("RX 6600") == "RX 6600"
        assert scraper.extract_gpu_model("RX6600") == "RX 6600"
        assert scraper.extract_gpu_model("rx 7900") == "RX 7900 XT"

    def test_extract_rx_xt(self, scraper):
        """Test RX XT extraction"""
        assert scraper.extract_gpu_model("RX 6600 XT") == "RX 6600 XT"
        assert scraper.extract_gpu_model("RX6600XT") == "RX 6600 XT"

    def test_extract_rx_xtx(self, scraper):
        """Test RX XTX extraction (fixed: XTX before XT in regex)"""
        assert scraper.extract_gpu_model("RX 7900 XTX") == "RX 7900 XTX"
        assert scraper.extract_gpu_model("RX7900XTX") == "RX 7900 XTX"

    def test_extract_rx_gre(self, scraper):
        """Test RX GRE extraction (newly added variant)"""
        assert scraper.extract_gpu_model("RX 7900 GRE") == "RX 7900 GRE"
        assert scraper.extract_gpu_model("RX7900GRE") == "RX 7900 GRE"
        assert scraper.extract_gpu_model("AMD Radeon RX 7900 GRE") == "RX 7900 GRE"

    def test_extract_rx_from_real_titles(self, scraper):
        """Test RX extraction from real OLX-style titles"""
        titles = [
            "AMD RX 6600 XT 8GB видео карта",
            "RADEON RX 7900 XTX 24GB",
            "rx 6800 xt gaming",
            "RX 7900 GRE 16GB AMD Radeon",
        ]
        expected = ["RX 6600 XT", "RX 7900 XTX", "RX 6800 XT", "RX 7900 GRE"]
        
        for title, exp in zip(titles, expected):
            assert scraper.extract_gpu_model(title) == exp

    # ===== Intel ARC =====
    def test_extract_arc_a_series(self, scraper):
        """Test Intel ARC A-series extraction"""
        assert scraper.extract_gpu_model("ARC A750") == "ARC A750"
        assert scraper.extract_gpu_model("ARCA770") == "ARC A770"
        assert scraper.extract_gpu_model("Intel Arc A380") == "ARC A380"

    def test_extract_arc_b_series(self, scraper):
        """Test Intel ARC B-series extraction"""
        assert scraper.extract_gpu_model("ARC B580") == "ARC B580"
        assert scraper.extract_gpu_model("ARCB570") == "ARC B570"
        assert scraper.extract_gpu_model("Intel Arc B580") == "ARC B580"

    def test_extract_arc_from_real_titles(self, scraper):
        """Test ARC extraction from real OLX-style titles"""
        titles = [
            "Intel Arc A750 8GB нова",
            "ARC A770 16GB gaming",
            "Intel ARC B580 Limited Edition",
        ]
        expected = ["ARC A750", "ARC A770", "ARC B580"]
        
        for title, exp in zip(titles, expected):
            assert scraper.extract_gpu_model(title) == exp

    # ===== AMD VEGA =====
    def test_extract_vega(self, scraper):
        """Test AMD VEGA extraction"""
        assert scraper.extract_gpu_model("RX VEGA 64") == "VEGA 64"
        assert scraper.extract_gpu_model("VEGA 56") == "VEGA 56"
        assert scraper.extract_gpu_model("AMD Radeon Vega 64") == "VEGA 64"

    # ===== Non-existent Models =====
    def test_extract_nonexistent_gtx_super(self, scraper):
        """Test extraction and normalization of non-existent GTX SUPER"""
        # GTX 10-series never had SUPER variants
        assert scraper.extract_gpu_model("GTX 1080 SUPER") == "GTX 1080"
        assert scraper.extract_gpu_model("GTX 1070 SUPER") == "GTX 1070"

    def test_extract_nonexistent_rtx_super(self, scraper):
        """Test extraction and normalization of non-existent RTX SUPER"""
        # RTX 30-series has no SUPER variants
        assert scraper.extract_gpu_model("RTX 3080 SUPER") == "RTX 3080"
        assert scraper.extract_gpu_model("RTX 3070 SUPER") == "RTX 3070"

    # ===== Edge Cases =====
    def test_extract_no_match(self, scraper):
        """Test titles with no GPU model"""
        assert scraper.extract_gpu_model("Продавам компютър") is None
        assert scraper.extract_gpu_model("Gaming setup") is None
        assert scraper.extract_gpu_model("") is None

    def test_extract_with_noise(self, scraper):
        """Test extraction with noisy/complex titles"""
        titles = [
            "!!! ПРОМОЦИЯ !!! RTX 3060 12GB НОВА !!!",
            "Видео карта NVIDIA GeForce RTX 3060 Ti OC Edition 8GB GDDR6",
            "🎮 Gaming GPU - RX 6600 XT 8GB - КАТО НОВА 🎮",
            "GTX 1660 SUPER 6GB + охлаждане + кутия",
        ]
        expected = ["RTX 3060 TI", "RTX 3060 TI", "RX 6600 XT", "GTX 1660 SUPER"]
        
        for title, exp in zip(titles, expected):
            assert scraper.extract_gpu_model(title) == exp

    def test_extract_cyrillic_titles(self, scraper):
        """Test extraction from Cyrillic titles"""
        titles = [
            "Продавам RTX 3060 в отлично състояние",
            "Геймърска GTX 1660 SUPER",
        ]
        expected = ["RTX 3060 TI", "GTX 1660 SUPER"]
        
        for title, exp in zip(titles, expected):
            assert scraper.extract_gpu_model(title) == exp

    def test_extract_multiple_models_takes_first(self, scraper):
        """Test that when multiple models exist, first match by pattern order"""
        title = "Upgrade от GTX 1060 на RTX 3060"
        result = scraper.extract_gpu_model(title)
        # RTX pattern comes before GTX, so should match RTX first
        assert result == "RTX 3060 TI"


class TestGPUScraper:
    """Test GPUScraper class functionality"""

    def test_scraper_initialization(self):
        """Test scraper initializes correctly"""
        scraper = GPUScraper(use_tor=False)
        assert scraper.use_tor is False
        assert scraper.gpu_prices == {}
        assert isinstance(scraper.gpu_benchmarks, dict)

    def test_scraper_with_tor(self):
        """Test scraper initialization with TOR"""
        scraper = GPUScraper(use_tor=True)
        assert scraper.use_tor is True
        assert scraper.tor_proxy is not None

    def test_add_benchmark_data(self):
        """Test adding benchmark data"""
        scraper = GPUScraper(use_tor=False)
        benchmark_data = {
            "RTX 3060": 97.0,
            "RX 6600 XT": 110.0,
        }
        scraper.add_benchmark_data(benchmark_data)
        assert scraper.gpu_benchmarks == benchmark_data


# Run tests with: pytest tests/test_scraper.py -v
