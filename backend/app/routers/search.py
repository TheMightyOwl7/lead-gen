"""Search API endpoints."""
import sys
from pathlib import Path

# Ensure backend is in path
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db, Search, Business
from app.rate_limiter import rate_limiter
from services.places_api import PlacesService, PlacesAPIError, APILimitExceeded

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchRequest(BaseModel):
    """Request model for business search."""
    query: str  # e.g., "dentists", "plumbers", "restaurants"
    location: str  # e.g., "Cape Town, South Africa"
    radius_km: int = Field(default=10, ge=1, le=50, description="Radius in km (1-50)")
    max_results: int = Field(default=10, ge=1, le=20, description="Max results (1-20)")


class SearchResponse(BaseModel):
    """Response model for search results."""
    search_id: int
    query: str
    location: str
    radius_km: int
    total_results: int
    businesses: list
    api_usage: dict


@router.post("", response_model=SearchResponse)
def search_businesses(request: SearchRequest, req: Request, db: Session = Depends(get_db)):
    """
    Search for businesses in a location.
    
    - **query**: Type of business (e.g., "dentists", "restaurants", "plumbers")
    - **location**: Location to search (e.g., "Cape Town, South Africa", "New York, NY")
    - **radius_km**: Search radius in kilometers (default: 10)
    """
    # Check rate limit before processing
    rate_limiter.check(req)
    
    try:
        service = PlacesService(db)
        results = service.search_businesses(
            query=request.query,
            location=request.location,
            radius_km=request.radius_km,
            max_results=request.max_results
        )
        return results
    except APILimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except PlacesAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/usage")
def get_api_usage(db: Session = Depends(get_db)):
    """Get current API usage statistics."""
    try:
        service = PlacesService(db)
        return service.get_usage_stats()
    except PlacesAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
def get_search_history(
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db)
):
    """Get recent search history."""
    searches = db.query(Search).order_by(Search.created_at.desc()).limit(limit).all()
    return [
        {
            "id": s.id,
            "query": s.query,
            "location": s.location,
            "radius_km": s.radius_km,
            "results_count": s.results_count,
            "created_at": s.created_at.isoformat()
        }
        for s in searches
    ]
