"""IP-based rate limiter middleware for API protection."""
import time
from collections import defaultdict
from fastapi import Request, HTTPException
from typing import Dict, List


class RateLimiter:
    """
    Simple in-memory rate limiter.
    Tracks requests per IP and blocks if limit exceeded.
    """
    
    def __init__(self, requests_per_minute: int = 30, burst_limit: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Max requests allowed per minute per IP
            burst_limit: Max requests allowed in a 5-second burst
        """
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    def _clean_old_requests(self, ip: str, window_seconds: int = 60):
        """Remove requests older than the time window."""
        now = time.time()
        self.requests[ip] = [t for t in self.requests[ip] if now - t < window_seconds]
    
    def _check_burst(self, ip: str) -> bool:
        """Check if IP is bursting (too many requests in 5 seconds)."""
        now = time.time()
        recent = [t for t in self.requests[ip] if now - t < 5]
        return len(recent) >= self.burst_limit
    
    def check(self, request: Request) -> None:
        """
        Check if request should be allowed.
        
        Args:
            request: FastAPI request object
            
        Raises:
            HTTPException: If rate limit exceeded (429 Too Many Requests)
        """
        # Get client IP (handle proxy scenarios)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        # Clean old requests
        self._clean_old_requests(ip)
        
        # Check burst limit first (stricter)
        if self._check_burst(ip):
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down.",
                headers={"Retry-After": "5"}
            )
        
        # Check minute limit
        if len(self.requests[ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {self.requests_per_minute} requests per minute.",
                headers={"Retry-After": "60"}
            )
        
        # Record this request
        self.requests[ip].append(time.time())
    
    def get_remaining(self, request: Request) -> dict:
        """Get remaining requests for an IP (useful for headers)."""
        ip = request.client.host if request.client else "unknown"
        self._clean_old_requests(ip)
        used = len(self.requests[ip])
        return {
            "limit": self.requests_per_minute,
            "remaining": max(0, self.requests_per_minute - used),
            "reset_in_seconds": 60
        }


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=30, burst_limit=10)
