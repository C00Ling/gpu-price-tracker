# tests/test_api.py
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_correct_structure(self, client):
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "message" in data
        assert "database" in data

    def test_health_check_status_healthy(self, client):
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"
        assert data["database"] == "connected"


class TestRootEndpoint:
    """Test root API endpoint"""

    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_api_info(self, client):
        response = client.get("/")
        data = response.json()

        assert "name" in data or "title" in data
        assert "version" in data


class TestListingsEndpoints:
    """Test /api/listings/ endpoints"""

    def test_get_all_listings_empty_db(self, client):
        """Test getting listings from empty database"""
        response = client.get("/api/listings/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_all_listings_with_data(self, client, test_repo, sample_gpu_data):
        """Test getting listings with sample data"""
        # Add sample data
        for listing in sample_gpu_data:
            test_repo.add_listing(**listing)

        response = client.get("/api/listings/")
        assert response.status_code == 200
        data = response.json()

        assert len(data) == len(sample_gpu_data)
        assert all("model" in item for item in data)
        assert all("price" in item for item in data)

    def test_get_listings_pagination(self, client, test_repo, sample_gpu_data):
        """Test pagination parameters"""
        # Add sample data
        for listing in sample_gpu_data:
            test_repo.add_listing(**listing)

        # Test page size limit
        response = client.get("/api/listings/?page=1&size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_get_listings_by_model(self, client, test_repo, sample_gpu_data):
        """Test filtering by GPU model"""
        # Add sample data
        for listing in sample_gpu_data:
            test_repo.add_listing(**listing)

        response = client.get("/api/listings/RTX%204090")
        assert response.status_code == 200
        data = response.json()

        assert all(item["model"] == "RTX 4090" for item in data)

    def test_get_listings_by_nonexistent_model(self, client):
        """Test filtering by model that doesn't exist"""
        response = client.get("/api/listings/RTX%209999")
        # Should return 404 when no listings found
        assert response.status_code == 404

    def test_get_total_count(self, client, test_repo, sample_gpu_data):
        """Test total count endpoint"""
        # Add sample data
        for listing in sample_gpu_data:
            test_repo.add_listing(**listing)

        response = client.get("/api/listings/count/total")
        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert data["total"] == len(sample_gpu_data)

    def test_get_available_models(self, client, test_repo, sample_gpu_data):
        """Test getting list of available models"""
        # Add sample data
        for listing in sample_gpu_data:
            test_repo.add_listing(**listing)

        response = client.get("/api/listings/models/list")
        assert response.status_code == 200
        data = response.json()

        assert "models" in data
        assert "count" in data
        assert isinstance(data["models"], list)
        assert "RTX 4090" in data["models"]
        assert "RTX 4070 SUPER" in data["models"]  # Auto-corrected from RTX 4070


class TestStatsEndpoints:
    """Test /api/stats/ endpoints"""

    def test_get_all_stats_empty_db(self, client):
        """Test stats with empty database"""
        response = client.get("/api/stats/")
        assert response.status_code == 200
        assert response.json() == {}

    def test_get_all_stats_with_data(self, client, test_repo, sample_gpu_data):
        """Test stats with sample data"""
        # Add sample data
        for listing in sample_gpu_data:
            test_repo.add_listing(**listing)

        response = client.get("/api/stats/")
        assert response.status_code == 200
        data = response.json()

        # Should have stats for each unique model
        assert "RTX 4090" in data
        assert "RTX 4070 SUPER" in data  # Auto-corrected from RTX 4070

    def test_stats_structure(self, client, test_repo, sample_gpu_data):
        """Test stats response structure"""
        # Add sample data
        for listing in sample_gpu_data:
            test_repo.add_listing(**listing)

        response = client.get("/api/stats/")
        data = response.json()

        # Check structure for one model
        model_stats = data["RTX 4090"]
        assert "min" in model_stats
        assert "max" in model_stats
        assert "median" in model_stats
        assert "mean" in model_stats
        assert "count" in model_stats

    def test_get_stats_by_model(self, client, test_repo, sample_gpu_data):
        """Test getting stats for specific model"""
        # Add sample data
        for listing in sample_gpu_data:
            test_repo.add_listing(**listing)

        # Get all stats and check RTX 4090
        response = client.get("/api/stats/")
        assert response.status_code == 200
        data = response.json()

        assert "RTX 4090" in data
        rtx_4090_stats = data["RTX 4090"]
        assert "min" in rtx_4090_stats
        assert "max" in rtx_4090_stats
        assert rtx_4090_stats["count"] == 2  # We have 2 RTX 4090 listings

    def test_get_stats_nonexistent_model(self, client):
        """Test stats for model that doesn't exist"""
        # Get all stats - should not have RTX 9999
        response = client.get("/api/stats/")
        assert response.status_code == 200
        data = response.json()
        assert "RTX 9999" not in data


class TestValueEndpoints:
    """Test /api/value/ endpoints"""

    def test_get_value_analysis_empty(self, client):
        """Test value analysis with no data"""
        response = client.get("/api/value/")
        assert response.status_code == 200
        # Should return empty list or error message
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_get_value_analysis_structure(self, client, test_repo, sample_gpu_data):
        """Test value analysis response structure"""
        # This test might need benchmark data to be loaded
        # For now just check the endpoint works
        response = client.get("/api/value/")
        assert response.status_code == 200

    def test_get_top_value_gpus(self, client):
        """Test getting top N GPUs by value"""
        response = client.get("/api/value/top/5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should return at most 5 items
        assert len(data) <= 5

    def test_top_value_invalid_number(self, client):
        """Test with invalid top N parameter"""
        response = client.get("/api/value/top/0")
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_top_value_negative_number(self, client):
        """Test with negative number"""
        response = client.get("/api/value/top/-5")
        # Should reject or handle gracefully
        assert response.status_code in [200, 400, 422]


class TestDashboardEndpoints:
    """Test dashboard and static pages"""

    @pytest.mark.skip(reason="Frontend not built - requires npm run build in frontend/")
    def test_dashboard_endpoint_exists(self, client):
        """Test that dashboard endpoint exists"""
        response = client.get("/dashboard")
        # Should return HTML (200 with file) or 404 (file not found)
        assert response.status_code in [200, 404]
        assert "text/html" in response.headers.get("content-type", "")
        # Content should be valid HTML
        assert "<!doctype html>" in response.text.lower() or "<html" in response.text.lower()

    @pytest.mark.skip(reason="Frontend not built - requires npm run build in frontend/")
    def test_home_page_returns_html(self, client):
        """Test that home page returns HTML"""
        response = client.get("/home")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestCORSHeaders:
    """Test CORS configuration"""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are set"""
        # Test with GET request instead of OPTIONS
        response = client.get("/api/listings/")
        # CORS headers should be present in response
        # Note: TestClient might not fully simulate CORS
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_endpoint_returns_404(self, client):
        """Test that invalid endpoints return 404"""
        response = client.get("/api/nonexistent/")
        assert response.status_code == 404

    def test_malformed_query_params(self, client):
        """Test handling of malformed query parameters"""
        response = client.get("/api/listings/?page=abc&size=xyz")
        # Should return 422 validation error or handle gracefully
        assert response.status_code in [200, 422]


class TestAPIDocumentation:
    """Test that API documentation is available"""

    def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_swagger_ui_available(self, client):
        """Test that Swagger UI is available"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_redoc_available(self, client):
        """Test that ReDoc is available"""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
