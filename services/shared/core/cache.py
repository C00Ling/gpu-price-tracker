import json
import hashlib
import logging
import os
import time
from pathlib import Path
from functools import wraps
from typing import Optional, Any, Callable, cast, List, Union

from core.config import config
from core.logging import get_logger

logger = get_logger("cache")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed. Using file-based cache fallback.")

class Cache:
    def __init__(self):
        # Check for REDIS_URL environment variable (Railway, Heroku, etc.)
        redis_url = os.getenv("REDIS_URL")
        redis_enabled = bool(config.get("redis.enabled", False)) or bool(redis_url)

        self.enabled = redis_enabled and REDIS_AVAILABLE
        self.client: Optional[redis.Redis] = None
        self.use_file_cache = False
        self.cache_dir = Path("cache")

        if self.enabled:
            try:
                # Prefer REDIS_URL if available (Railway, Heroku)
                if redis_url:
                    logger.info("🔗 Connecting to Redis using REDIS_URL...")
                    self.client = redis.from_url(
                        redis_url,
                        decode_responses=True,
                        socket_timeout=5,
                        socket_connect_timeout=5
                    )
                else:
                    # Fallback to individual config values
                    logger.info("🔗 Connecting to Redis using config values...")
                    self.client = redis.Redis(
                        host=str(config.get("redis.host", "localhost")),
                        port=int(config.get("redis.port", 6379)),
                        db=int(config.get("redis.db", 0)),
                        password=cast(Optional[str], config.get("redis.password")),
                        decode_responses=True,
                        socket_timeout=5,
                        socket_connect_timeout=5
                    )

                self.client.ping()
                logger.info("✅ Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed: {e}. Falling back to file-based cache.")
                self.enabled = False
                self.use_file_cache = True
        else:
            # If Redis not configured, use file-based cache for development
            self.use_file_cache = True
            logger.info("📁 Using file-based cache (Redis not configured)")

        # Setup file cache directory
        if self.use_file_cache:
            self.cache_dir.mkdir(exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key"""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[Any]:
        # Try Redis first
        if self.enabled and self.client:
            try:
                value = self.client.get(key)
                if value:
                    return json.loads(cast(str, value))
                return None
            except Exception as e:
                logger.error(f"Redis get error: {e}")

        # Fallback to file cache
        if self.use_file_cache:
            try:
                file_path = self._get_file_path(key)
                if not file_path.exists():
                    return None

                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Check TTL
                if 'expires_at' in data and data['expires_at'] < time.time():
                    file_path.unlink()  # Delete expired cache
                    return None

                return data.get('value')
            except Exception as e:
                logger.error(f"File cache get error: {e}")
                return None

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        # Try Redis first
        if self.enabled and self.client:
            try:
                default_ttl = config.get("redis.cache_ttl", 3600)
                expire = int(ttl if ttl is not None else default_ttl)
                serialized = json.dumps(value, default=str)
                self.client.set(key, serialized, ex=expire)
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")

        # Fallback to file cache
        if self.use_file_cache:
            try:
                file_path = self._get_file_path(key)
                default_ttl = config.get("redis.cache_ttl", 3600) if hasattr(config, 'get') else 3600
                expire_time = time.time() + (ttl if ttl is not None else default_ttl)

                data = {
                    'key': key,
                    'value': value,
                    'expires_at': expire_time
                }

                with open(file_path, 'w') as f:
                    json.dump(data, f, default=str)

                return True
            except Exception as e:
                logger.error(f"File cache set error: {e}")
                return False

        return False

    def invalidate_pattern(self, pattern: str) -> int:
        # Try Redis first
        if self.enabled and self.client:
            try:
                keys = cast(List[str], self.client.keys(pattern))
                if keys:
                    return int(cast(Any, self.client.delete(*keys)))
                return 0
            except Exception as e:
                logger.error(f"Redis invalidate error: {e}")

        # File cache doesn't support pattern matching easily
        if self.use_file_cache:
            logger.warning("Pattern invalidation not supported in file cache")
            return 0

        return 0

cache = Cache()

def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache.enabled:
                return func(*args, **kwargs)
            
            key_parts = [key_prefix, func.__name__]
            if args: key_parts.append("_".join(str(a) for a in args))
            if kwargs: key_parts.append("_".join(f"{k}={v}" for k, v in sorted(kwargs.items())))
            
            cache_key = ":".join(filter(None, key_parts))
            if len(cache_key) > 200:
                cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(cache_key.encode()).hexdigest()}"
            
            cached_val = cache.get(cache_key)
            if cached_val is not None: return cached_val
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator