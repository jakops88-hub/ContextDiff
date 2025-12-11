"""
Caching service for LLM responses.

Implements deterministic caching based on content hash to avoid
redundant API calls for identical requests.
"""

import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class ResponseCache:
    """
    In-memory cache for LLM responses.
    
    For production deployment, replace with Redis or Memcached.
    Uses SHA-256 hash of input parameters as cache key.
    """
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time-to-live for cache entries in seconds (default: 1 hour).
            max_size: Maximum number of entries before cleanup (default: 1000).
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        
        logger.info(f"ResponseCache initialized: TTL={ttl_seconds}s, max_size={max_size}")
    
    def _generate_key(
        self,
        original_text: str,
        generated_text: str,
        sensitivity: str
    ) -> str:
        """
        Generate deterministic cache key from inputs.
        
        Uses SHA-256 hash of concatenated inputs to create unique key.
        
        Args:
            original_text: Original text content.
            generated_text: Generated text content.
            sensitivity: Sensitivity level.
            
        Returns:
            Hex string cache key.
        """
        # Concatenate inputs in deterministic order
        cache_input = f"{original_text}|{generated_text}|{sensitivity}"
        
        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(cache_input.encode('utf-8'))
        cache_key = hash_obj.hexdigest()
        
        return cache_key
    
    def get(
        self,
        original_text: str,
        generated_text: str,
        sensitivity: str
    ) -> Optional[dict]:
        """
        Retrieve cached response if available and not expired.
        
        Args:
            original_text: Original text content.
            generated_text: Generated text content.
            sensitivity: Sensitivity level.
            
        Returns:
            Cached response dictionary or None if not found/expired.
        """
        cache_key = self._generate_key(original_text, generated_text, sensitivity)
        
        if cache_key not in self._cache:
            self.misses += 1
            logger.debug(f"Cache miss: {cache_key[:16]}...")
            return None
        
        entry = self._cache[cache_key]
        
        # Check expiration
        if datetime.now() > entry["expires_at"]:
            # Expired, remove and return None
            del self._cache[cache_key]
            self.misses += 1
            logger.debug(f"Cache expired: {cache_key[:16]}...")
            return None
        
        # Valid cache hit
        self.hits += 1
        logger.info(
            f"Cache HIT: {cache_key[:16]}... "
            f"(hit_rate: {self.get_hit_rate():.1%})"
        )
        
        return entry["data"]
    
    def set(
        self,
        original_text: str,
        generated_text: str,
        sensitivity: str,
        response_data: dict
    ) -> None:
        """
        Store response in cache with expiration.
        
        Args:
            original_text: Original text content.
            generated_text: Generated text content.
            sensitivity: Sensitivity level.
            response_data: Response dictionary to cache.
        """
        # Check if cleanup needed
        if len(self._cache) >= self.max_size:
            self._cleanup()
        
        cache_key = self._generate_key(original_text, generated_text, sensitivity)
        expires_at = datetime.now() + timedelta(seconds=self.ttl_seconds)
        
        self._cache[cache_key] = {
            "data": response_data,
            "expires_at": expires_at,
            "created_at": datetime.now()
        }
        
        logger.debug(f"Cache SET: {cache_key[:16]}... (expires in {self.ttl_seconds}s)")
    
    def _cleanup(self) -> None:
        """
        Remove expired entries and oldest entries if over capacity.
        
        Called automatically when cache reaches max_size.
        """
        now = datetime.now()
        
        # Remove expired entries
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        logger.info(f"Cache cleanup: Removed {len(expired_keys)} expired entries")
        
        # If still over capacity, remove oldest entries
        if len(self._cache) >= self.max_size:
            # Sort by creation time
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1]["created_at"]
            )
            
            # Remove oldest 20%
            remove_count = max(1, len(sorted_entries) // 5)
            for key, _ in sorted_entries[:remove_count]:
                del self._cache[key]
            
            logger.info(f"Cache cleanup: Removed {remove_count} oldest entries")
    
    def clear(self) -> None:
        """Clear all cache entries."""
        entry_count = len(self._cache)
        self._cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info(f"Cache cleared: {entry_count} entries removed")
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics.
        """
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.get_hit_rate(),
            "ttl_seconds": self.ttl_seconds
        }
    
    def get_hit_rate(self) -> float:
        """
        Calculate cache hit rate.
        
        Returns:
            Hit rate as decimal (0.0-1.0).
        """
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total


# Global cache instance (singleton pattern)
_global_cache: Optional[ResponseCache] = None


def get_cache() -> ResponseCache:
    """
    Get or create global cache instance.
    
    Returns:
        Global ResponseCache instance.
    """
    global _global_cache
    
    if _global_cache is None:
        _global_cache = ResponseCache(
            ttl_seconds=3600,  # 1 hour
            max_size=1000      # 1000 entries
        )
    
    return _global_cache


def clear_cache() -> None:
    """Clear the global cache."""
    cache = get_cache()
    cache.clear()
