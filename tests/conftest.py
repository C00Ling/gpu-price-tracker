# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from storage.orm import Base
from api.dependencies import get_db
from storage.repo import GPURepository


# ============================================================
# Database Fixtures
# ============================================================

@pytest.fixture(scope="function")
def test_db_engine():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a new database session for each test"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_repo(test_db_session):
    """Create a repository instance for testing"""
    return GPURepository(test_db_session)


# ============================================================
# FastAPI Client Fixture
# ============================================================

@pytest.fixture(scope="function")
def client(test_db_session):
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================
# Sample Data Fixtures
# ============================================================

@pytest.fixture
def sample_gpu_data():
    """Sample GPU listings for testing"""
    return [
        {
            "model": "RTX 4090",
            "price": 3500,
            "source": "OLX"
        },
        {
            "model": "RTX 4090",
            "price": 3600,
            "source": "OLX"
        },
        {
            "model": "RTX 4070",
            "price": 1200,
            "source": "OLX"
        },
        {
            "model": "RTX 4070",
            "price": 1300,
            "source": "OLX"
        },
        {
            "model": "RX 7900 XTX",
            "price": 1800,
            "source": "OLX"
        },
    ]


@pytest.fixture
def sample_prices_by_model():
    """Sample price data grouped by model"""
    return {
        "RTX 4090": [3500, 3600, 3550, 3700],
        "RTX 4070": [1200, 1250, 1300, 1280],
        "RTX 3060": [500, 520, 480, 550],
        "RX 6600": [350, 380, 360, 370],
    }


@pytest.fixture
def sample_benchmark_data():
    """Sample GPU benchmark data"""
    return {
        "RTX 4090": 185.0,
        "RTX 4070": 110.0,
        "RTX 3060": 75.0,
        "RX 6600": 75.0,
    }


@pytest.fixture
def mock_olx_html():
    """Mock OLX HTML response for scraper testing"""
    return """
    <html>
        <body>
            <a href="/d/ad/test-ad-1" data-cy="listing-card">
                <h4>RTX 4070 12GB Gaming</h4>
                <p>1 299 лв</p>
            </a>
            <a href="/d/ad/test-ad-2" data-cy="listing-card">
                <h6>RTX 3060 TI 8GB</h6>
                <p>650 лв</p>
            </a>
            <a href="/d/ad/test-ad-3" data-cy="listing-card">
                <h4>RX 6600 XT</h4>
                <p>420 лв</p>
            </a>
        </body>
    </html>
    """


@pytest.fixture
def mock_broken_gpu_listing():
    """Mock listing for broken GPU (should be filtered)"""
    return {
        "title": "RTX 3060 счупена за части",
        "price": 50,
        "description": "Не работи, за части"
    }


@pytest.fixture
def mock_suspicious_listing():
    """Mock listing with suspicious price (outlier)"""
    return {
        "title": "RTX 4090 спешно",
        "price": 200,  # Too low for RTX 4090
        "description": "Срочно продавам"
    }


# ============================================================
# Mock Request/Response Fixtures
# ============================================================

@pytest.fixture
def mock_requests_response():
    """Mock requests.Response object"""
    class MockResponse:
        def __init__(self, content, status_code=200):
            self.content = content
            self.status_code = status_code
            self.text = content.decode() if isinstance(content, bytes) else content

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

        def json(self):
            import json
            return json.loads(self.text)

    return MockResponse


# ============================================================
# Configuration Fixtures
# ============================================================

@pytest.fixture
def test_config():
    """Test configuration overrides"""
    return {
        "database": {
            "url": "sqlite:///:memory:",
            "echo": False
        },
        "scraper": {
            "max_pages": 1,
            "use_tor": False,
            "rate_limit": {
                "requests_per_minute": 100,
                "delay_between_pages": 0
            }
        },
        "logging": {
            "level": "ERROR",
            "console_output": False
        }
    }
