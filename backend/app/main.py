"""FastAPI application entry point."""
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.config import settings
from app.routers import search, businesses

# Initialize FastAPI app
app = FastAPI(
    title="Lead Generation Tool",
    description="Find local businesses using Google Places API",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router)
app.include_router(businesses.router)

# Serve frontend static files
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


@app.on_event("startup")
def startup():
    """Initialize database on startup."""
    init_db()
    
    # Validate configuration
    errors = settings.validate()
    if errors:
        print("⚠️  Configuration warnings:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ Configuration validated")
    
    print(f"📊 Monthly API limit: {settings.MONTHLY_API_LIMIT} calls")


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    errors = settings.validate()
    return {
        "status": "healthy" if not errors else "degraded",
        "config_errors": errors,
        "api_key_configured": bool(settings.GOOGLE_MAPS_API_KEY)
    }
