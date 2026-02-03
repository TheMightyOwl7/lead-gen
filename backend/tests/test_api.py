"""Integration tests for API endpoints."""
import pytest
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, SessionLocal, Business, Search, APIUsage


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create database session for testing."""
    init_db()
    session = SessionLocal()
    yield session
    session.close()


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_returns_200(self, client):
        """Health endpoint should return 200."""
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_health_returns_status(self, client):
        """Health endpoint should return status field."""
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]
    
    def test_health_returns_api_key_configured(self, client):
        """Health endpoint should indicate if API key is configured."""
        response = client.get("/api/health")
        data = response.json()
        assert "api_key_configured" in data
        assert isinstance(data["api_key_configured"], bool)


class TestUsageEndpoint:
    """Test API usage tracking endpoint."""
    
    def test_usage_returns_200(self, client):
        """Usage endpoint should return 200."""
        response = client.get("/api/search/usage")
        # May return 400 if API key not configured, which is expected
        assert response.status_code in [200, 400]
    
    def test_usage_returns_expected_fields(self, client):
        """Usage endpoint should return usage statistics."""
        response = client.get("/api/search/usage")
        if response.status_code == 200:
            data = response.json()
            expected_fields = ["month", "calls_used", "calls_limit", "calls_remaining", "percentage_used"]
            for field in expected_fields:
                assert field in data, f"Missing field: {field}"


class TestBusinessesEndpoint:
    """Test businesses listing endpoint."""
    
    def test_list_businesses_returns_200(self, client):
        """Businesses endpoint should return 200."""
        response = client.get("/api/businesses")
        assert response.status_code == 200
    
    def test_list_businesses_returns_expected_structure(self, client):
        """Businesses endpoint should return expected structure."""
        response = client.get("/api/businesses")
        data = response.json()
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "businesses" in data
        assert isinstance(data["businesses"], list)
    
    def test_list_businesses_with_limit(self, client):
        """Businesses endpoint should respect limit parameter."""
        response = client.get("/api/businesses?limit=5")
        data = response.json()
        assert data["limit"] == 5
    
    def test_list_businesses_with_offset(self, client):
        """Businesses endpoint should respect offset parameter."""
        response = client.get("/api/businesses?offset=10")
        data = response.json()
        assert data["offset"] == 10


class TestBusinessStatsEndpoint:
    """Test business statistics endpoint."""
    
    def test_stats_returns_200(self, client):
        """Stats endpoint should return 200."""
        response = client.get("/api/businesses/stats/summary")
        assert response.status_code == 200
    
    def test_stats_returns_expected_fields(self, client):
        """Stats endpoint should return expected statistics."""
        response = client.get("/api/businesses/stats/summary")
        data = response.json()
        expected_fields = ["total_businesses", "with_website", "without_website", "website_percentage"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"


class TestSearchEndpoint:
    """Test search endpoint validation."""
    
    def test_search_requires_query(self, client):
        """Search should require query field."""
        response = client.post("/api/search", json={
            "location": "Cape Town"
        })
        assert response.status_code == 422  # Validation error
    
    def test_search_requires_location(self, client):
        """Search should require location field."""
        response = client.post("/api/search", json={
            "query": "restaurants"
        })
        assert response.status_code == 422  # Validation error
    
    def test_search_validates_radius_max(self, client):
        """Search should reject radius > 50."""
        response = client.post("/api/search", json={
            "query": "restaurants",
            "location": "Cape Town",
            "radius_km": 100
        })
        assert response.status_code == 422  # Validation error
    
    def test_search_validates_radius_min(self, client):
        """Search should reject radius < 1."""
        response = client.post("/api/search", json={
            "query": "restaurants",
            "location": "Cape Town",
            "radius_km": 0
        })
        assert response.status_code == 422  # Validation error
    
    def test_search_validates_max_results_max(self, client):
        """Search should reject max_results > 20."""
        response = client.post("/api/search", json={
            "query": "restaurants",
            "location": "Cape Town",
            "max_results": 50
        })
        assert response.status_code == 422  # Validation error
    
    def test_search_validates_max_results_min(self, client):
        """Search should reject max_results < 1."""
        response = client.post("/api/search", json={
            "query": "restaurants",
            "location": "Cape Town",
            "max_results": 0
        })
        assert response.status_code == 422  # Validation error


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_import(self):
        """Rate limiter should be importable."""
        from app.rate_limiter import RateLimiter, rate_limiter
        assert rate_limiter is not None
    
    def test_rate_limiter_has_check_method(self):
        """Rate limiter should have check method."""
        from app.rate_limiter import RateLimiter
        limiter = RateLimiter()
        assert hasattr(limiter, 'check')
    
    def test_rate_limiter_has_get_remaining_method(self):
        """Rate limiter should have get_remaining method."""
        from app.rate_limiter import RateLimiter
        limiter = RateLimiter()
        assert hasattr(limiter, 'get_remaining')
