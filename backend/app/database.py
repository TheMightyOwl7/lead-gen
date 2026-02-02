"""SQLite database setup with SQLAlchemy."""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

from .config import settings

# Create engine - for SQLite, check_same_thread=False is needed for FastAPI
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Search(Base):
    """Track search history and API usage."""
    __tablename__ = "searches"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)  # e.g., "dentists"
    location = Column(String, nullable=False)  # e.g., "Cape Town, South Africa"
    radius_km = Column(Integer, default=10)
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Business(Base):
    """Discovered businesses from Google Places."""
    __tablename__ = "businesses"
    
    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String, unique=True, index=True)  # Google's unique ID
    name = Column(String, nullable=False)
    address = Column(String)
    phone = Column(String)
    website = Column(String)
    rating = Column(Float)
    review_count = Column(Integer)
    business_types = Column(String)  # JSON array of types
    latitude = Column(Float)
    longitude = Column(Float)
    search_id = Column(Integer)  # Which search found this
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for JSON response."""
        return {
            "id": self.id,
            "place_id": self.place_id,
            "name": self.name,
            "address": self.address,
            "phone": self.phone,
            "website": self.website,
            "rating": self.rating,
            "review_count": self.review_count,
            "business_types": json.loads(self.business_types) if self.business_types else [],
            "latitude": self.latitude,
            "longitude": self.longitude,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class APIUsage(Base):
    """Track API usage to stay within free tier."""
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    month = Column(String, nullable=False)  # Format: "2024-01"
    call_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
