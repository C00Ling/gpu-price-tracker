import json
import hashlib
import logging
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
    logger.warning("Redis not installed. Caching disabled. Install with: pip install redis")

class Cache:
    def __init__(self):
        self.enabled = bool(config.get("redis.enabled", False)) and REDIS_AVAILABLE
        self.client: Optional[redis.Redis] = None
        
        if self.enabled:
            try:
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
                logger.info("✅ Redis cache connected")
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed: {e}. Caching disabled.")
                self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        if not self.enabled or not self.client:
            return None
        try:
            value = self.client.get(key)
            if value:
                return json.loads(cast(str, value))
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not self.enabled or not self.client:
            return False
        try:
            default_ttl = config.get("redis.cache_ttl", 3600)
            expire = int(ttl if ttl is not None else default_ttl)
            serialized = json.dumps(value, default=str)
            self.client.set(key, serialized, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        if not self.enabled or not self.client:
            return 0
        try:
            keys = cast(List[str], self.client.keys(pattern))
            if keys:
                return int(cast(Any, self.client.delete(*keys)))
            return 0
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
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