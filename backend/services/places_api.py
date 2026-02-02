"""Google Places API integration with usage tracking."""
import googlemaps
from datetime import datetime
from sqlalchemy.orm import Session
import json

from app.config import settings
from app.database import APIUsage, Business, Search


class PlacesAPIError(Exception):
    """Custom exception for Places API errors."""
    pass


class APILimitExceeded(Exception):
    """Raised when monthly API limit is reached."""
    pass


class PlacesService:
    """Service for interacting with Google Places API."""
    
    def __init__(self, db: Session):
        self.db = db
        if not settings.GOOGLE_MAPS_API_KEY:
            raise PlacesAPIError("Google Maps API key not configured")
        self.client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    
    def _get_current_month(self) -> str:
        """Get current month string for tracking."""
        return datetime.utcnow().strftime("%Y-%m")
    
    def _check_api_limit(self) -> tuple[int, int]:
        """Check if we're within API limits. Returns (current_count, limit)."""
        month = self._get_current_month()
        usage = self.db.query(APIUsage).filter(APIUsage.month == month).first()
        
        current_count = usage.call_count if usage else 0
        return current_count, settings.MONTHLY_API_LIMIT
    
    def _increment_api_usage(self, count: int = 1):
        """Increment API usage counter."""
        month = self._get_current_month()
        usage = self.db.query(APIUsage).filter(APIUsage.month == month).first()
        
        if usage:
            usage.call_count += count
            usage.last_updated = datetime.utcnow()
        else:
            usage = APIUsage(month=month, call_count=count)
            self.db.add(usage)
        
        self.db.commit()
    
    def get_usage_stats(self) -> dict:
        """Get current API usage statistics."""
        current, limit = self._check_api_limit()
        return {
            "month": self._get_current_month(),
            "calls_used": current,
            "calls_limit": limit,
            "calls_remaining": max(0, limit - current),
            "percentage_used": round((current / limit) * 100, 1) if limit > 0 else 0
        }
    
    def search_businesses(
        self,
        query: str,
        location: str,
        radius_km: int = 10,
        max_results: int = 10
    ) -> dict:
        """
        Search for businesses using Google Places Text Search.
        
        Args:
            query: Business type to search for (e.g., "dentists", "restaurants")
            location: Location string (e.g., "Cape Town, South Africa")
            radius_km: Search radius in kilometers
            max_results: Maximum number of businesses to return (limits API calls)
            
        Returns:
            Dictionary with search results and metadata
        """
        # Check API limit
        current, limit = self._check_api_limit()
        if current >= limit:
            raise APILimitExceeded(
                f"Monthly API limit reached ({current}/{limit}). "
                f"Limit resets next month."
            )
        
        # First, geocode the location to get coordinates
        try:
            geocode_result = self.client.geocode(location)
            self._increment_api_usage(1)
        except Exception as e:
            raise PlacesAPIError(f"Failed to geocode location: {str(e)}")
        
        if not geocode_result:
            raise PlacesAPIError(f"Could not find location: {location}")
        
        lat = geocode_result[0]["geometry"]["location"]["lat"]
        lng = geocode_result[0]["geometry"]["location"]["lng"]
        
        # Build the search query
        search_query = f"{query} in {location}"
        radius_meters = radius_km * 1000
        
        # Perform the text search
        try:
            results = self.client.places(
                query=search_query,
                location=(lat, lng),
                radius=radius_meters
            )
            self._increment_api_usage(1)
        except Exception as e:
            raise PlacesAPIError(f"Places search failed: {str(e)}")
        
        # Create search record
        search_record = Search(
            query=query,
            location=location,
            radius_km=radius_km,
            results_count=len(results.get("results", []))
        )
        self.db.add(search_record)
        self.db.commit()
        
        # Process and store results (limit to max_results)
        businesses = []
        places_to_process = results.get("results", [])[:max_results]  # Limit results
        
        for place in places_to_process:
            # Check if we already have this business
            existing = self.db.query(Business).filter(
                Business.place_id == place.get("place_id")
            ).first()
            
            if existing:
                businesses.append(existing.to_dict())
                continue
            
            # Get additional details for website and phone
            # Note: This costs an additional API call per place
            details = None
            if current + 2 < limit:  # Only if we have room in the budget
                try:
                    details_response = self.client.place(
                        place.get("place_id"),
                        fields=["formatted_phone_number", "website", "url"]
                    )
                    details = details_response.get("result", {})
                    self._increment_api_usage(1)
                    current += 1
                except:
                    pass  # Skip details if it fails
            
            # Create business record
            business = Business(
                place_id=place.get("place_id"),
                name=place.get("name"),
                address=place.get("formatted_address"),
                phone=details.get("formatted_phone_number") if details else None,
                website=details.get("website") if details else None,
                rating=place.get("rating"),
                review_count=place.get("user_ratings_total"),
                business_types=json.dumps(place.get("types", [])),
                latitude=place.get("geometry", {}).get("location", {}).get("lat"),
                longitude=place.get("geometry", {}).get("location", {}).get("lng"),
                search_id=search_record.id
            )
            self.db.add(business)
            businesses.append(business.to_dict())
        
        self.db.commit()
        
        return {
            "search_id": search_record.id,
            "query": query,
            "location": location,
            "radius_km": radius_km,
            "total_results": len(businesses),
            "businesses": businesses,
            "api_usage": self.get_usage_stats()
        }
