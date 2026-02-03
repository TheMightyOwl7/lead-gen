"""Unit tests for the Business model and lead scoring."""
import pytest
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import Business


class TestLeadScoring:
    """Test lead score calculation logic."""
    
    def test_no_website_gives_50_points(self):
        """Business without website should get +50 points."""
        business = Business(
            name="Test Business",
            website=None,
            rating=None,
            review_count=None,
            phone=None
        )
        assert business.calculate_lead_score() == 50
    
    def test_with_website_gives_0_for_that_criterion(self):
        """Business with website should not get website bonus."""
        business = Business(
            name="Test Business",
            website="https://example.com",
            rating=None,
            review_count=None,
            phone=None
        )
        assert business.calculate_lead_score() == 0
    
    def test_high_rating_gives_20_points(self):
        """Rating >= 4.0 should give +20 points."""
        business = Business(
            name="Test Business",
            website="https://example.com",
            rating=4.5,
            review_count=None,
            phone=None
        )
        assert business.calculate_lead_score() == 20
    
    def test_low_rating_gives_no_bonus(self):
        """Rating < 4.0 should not give rating bonus."""
        business = Business(
            name="Test Business",
            website="https://example.com",
            rating=3.9,
            review_count=None,
            phone=None
        )
        assert business.calculate_lead_score() == 0
    
    def test_many_reviews_gives_15_points(self):
        """Review count >= 100 should give +15 points."""
        business = Business(
            name="Test Business",
            website="https://example.com",
            rating=None,
            review_count=150,
            phone=None
        )
        assert business.calculate_lead_score() == 15
    
    def test_few_reviews_gives_no_bonus(self):
        """Review count < 100 should not give review bonus."""
        business = Business(
            name="Test Business",
            website="https://example.com",
            rating=None,
            review_count=50,
            phone=None
        )
        assert business.calculate_lead_score() == 0
    
    def test_has_phone_gives_15_points(self):
        """Having a phone number should give +15 points."""
        business = Business(
            name="Test Business",
            website="https://example.com",
            rating=None,
            review_count=None,
            phone="+1234567890"
        )
        assert business.calculate_lead_score() == 15
    
    def test_max_score_is_100(self):
        """Perfect lead should score 100 points."""
        business = Business(
            name="Perfect Lead",
            website=None,  # +50
            rating=4.8,    # +20
            review_count=200,  # +15
            phone="+1234567890"  # +15
        )
        assert business.calculate_lead_score() == 100
    
    def test_to_dict_includes_lead_score(self):
        """to_dict() should include lead_score field."""
        business = Business(
            id=1,
            place_id="test_place_id",
            name="Test Business",
            website=None,
            rating=4.5,
            review_count=100,
            phone="+123",
            business_types="[]"
        )
        result = business.to_dict()
        assert "lead_score" in result
        assert result["lead_score"] == 100  # 50 + 20 + 15 + 15


class TestBusinessModel:
    """Test Business model general functionality."""
    
    def test_to_dict_returns_expected_fields(self):
        """to_dict should return all expected fields."""
        business = Business(
            id=1,
            place_id="abc123",
            name="Test Business",
            address="123 Test St",
            phone="+1234567890",
            website="https://test.com",
            rating=4.5,
            review_count=100,
            business_types='["restaurant", "food"]',
            latitude=12.34,
            longitude=56.78
        )
        result = business.to_dict()
        
        expected_keys = [
            "id", "place_id", "name", "address", "phone",
            "website", "rating", "review_count", "business_types",
            "latitude", "longitude", "lead_score", "created_at"
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
    
    def test_business_types_parsed_as_list(self):
        """business_types JSON should be parsed to list."""
        business = Business(
            name="Test",
            business_types='["restaurant", "cafe"]'
        )
        result = business.to_dict()
        assert result["business_types"] == ["restaurant", "cafe"]
    
    def test_empty_business_types_returns_empty_list(self):
        """Empty business_types should return empty list."""
        business = Business(name="Test", business_types=None)
        result = business.to_dict()
        assert result["business_types"] == []
