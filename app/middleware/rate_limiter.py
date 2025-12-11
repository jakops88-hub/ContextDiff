"""
Rate limiting middleware for API protection.

Implements token bucket algorithm with in-memory storage.
For production, replace with Redis-backed solution.
"""

import time
from typing import Dict, Tuple
from collections import defaultdict
from threading import Lock

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": 60
            },
            headers={"Retry-After": "60"}
        )


class TokenBucket:
    """
    Token bucket implementation for rate limiting.
    
    Attributes:
        capacity: Maximum number of tokens in the bucket.
        refill_rate: Tokens added per second.
        tokens: Current token count.
        last_refill: Timestamp of last refill.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum tokens in bucket.
            refill_rate: Tokens to add per second.
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self.lock = Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens from bucket.
        
        Args:
            tokens: Number of tokens to consume.
            
        Returns:
            True if tokens consumed successfully, False otherwise.
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def _refill(self):
        """Refill bucket based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        self.tokens = min(
            self.capacity,
            self.tokens + (elapsed * self.refill_rate)
        )
        
        self.last_refill = now
    
    def get_status(self) -> Tuple[float, int]:
        """
        Get current bucket status.
        
        Returns:
            Tuple of (current_tokens, capacity).
        """
        with self.lock:
            self._refill()
            return (self.tokens, self.capacity)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm.
    
    Configuration:
        - Default: 60 requests per minute per IP
        - Configurable via environment variables
    
    Note: Uses in-memory storage. For distributed systems,
    replace with Redis or similar external store.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application instance.
            requests_per_minute: Maximum requests per minute per client.
            burst_size: Additional burst capacity above rate limit.
        """
        super().__init__(app)
        
        # Convert to tokens per second
        self.capacity = requests_per_minute + burst_size
        self.refill_rate = requests_per_minute / 60.0
        
        # Storage for client buckets (IP -> TokenBucket)
        self.buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(self.capacity, self.refill_rate)
        )
        
        # Cleanup old buckets periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.
        
        Args:
            request: Incoming HTTP request.
            call_next: Next middleware in chain.
            
        Returns:
            Response from application or rate limit error.
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded.
        """
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = self._get_client_ip(request)
        
        # Get or create bucket for client
        bucket = self.buckets[client_ip]
        
        # Attempt to consume token
        if not bucket.consume():
            raise RateLimitExceeded()
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        tokens_remaining, capacity = bucket.get_status()
        response.headers["X-RateLimit-Limit"] = str(capacity)
        response.headers["X-RateLimit-Remaining"] = str(int(tokens_remaining))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
        
        # Periodic cleanup of old buckets
        self._cleanup_old_buckets()
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request.
        
        Handles X-Forwarded-For header for proxied requests.
        
        Args:
            request: HTTP request object.
            
        Returns:
            Client IP address as string.
        """
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_buckets(self):
        """
        Remove inactive client buckets to prevent memory bloat.
        
        Runs every cleanup_interval seconds.
        """
        now = time.time()
        
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        # Remove buckets that haven't been used recently
        inactive_clients = [
            ip for ip, bucket in self.buckets.items()
            if now - bucket.last_refill > self.cleanup_interval
        ]
        
        for ip in inactive_clients:
            del self.buckets[ip]
        
        self.last_cleanup = now
