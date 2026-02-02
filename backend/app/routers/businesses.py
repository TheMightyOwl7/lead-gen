"""Business API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db, Business

router = APIRouter(prefix="/api/businesses", tags=["businesses"])


@router.get("")
def list_businesses(
    search_id: Optional[int] = None,
    has_website: Optional[bool] = None,
    min_rating: Optional[float] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List stored businesses with optional filters.
    
    - **search_id**: Filter by search ID
    - **has_website**: Filter by whether business has a website
    - **min_rating**: Minimum Google rating
    - **limit**: Max results to return
    - **offset**: Pagination offset
    """
    query = db.query(Business)
    
    if search_id:
        query = query.filter(Business.search_id == search_id)
    
    if has_website is not None:
        if has_website:
            query = query.filter(Business.website.isnot(None), Business.website != "")
        else:
            query = query.filter((Business.website.is_(None)) | (Business.website == ""))
    
    if min_rating:
        query = query.filter(Business.rating >= min_rating)
    
    total = query.count()
    businesses = query.order_by(Business.rating.desc().nullslast()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "businesses": [b.to_dict() for b in businesses]
    }


@router.get("/{business_id}")
def get_business(business_id: int, db: Session = Depends(get_db)):
    """Get a specific business by ID."""
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business.to_dict()


@router.get("/stats/summary")
def get_stats(db: Session = Depends(get_db)):
    """Get summary statistics about stored businesses."""
    total = db.query(Business).count()
    with_website = db.query(Business).filter(
        Business.website.isnot(None), 
        Business.website != ""
    ).count()
    without_website = total - with_website
    
    return {
        "total_businesses": total,
        "with_website": with_website,
        "without_website": without_website,
        "website_percentage": round((with_website / total) * 100, 1) if total > 0 else 0
    }
