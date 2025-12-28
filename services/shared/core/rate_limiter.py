import time
from functools import wraps
from collections import deque
from typing import Callable, Any
from core.logging import get_logger

logger = get_logger("rate_limiter")


class RateLimiter:
    """
    Token bucket rate limiter
    
    Използва се за ограничаване на броя заявки в даден период
    """
    
    def __init__(self, calls: int, period: int):
        """
        Args:
            calls: Максимален брой заявки
            period: Период в секунди
        """
        self.calls = calls
        self.period = period
        self.timestamps = deque(maxlen=calls)
        logger.info(f"RateLimiter initialized: {calls} calls per {period}s")
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator за rate limiting"""
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            now = time.time()
            
            # Премахни старите timestamps
            while self.timestamps and now - self.timestamps[0] > self.period:
                self.timestamps.popleft()
            
            # Проверка дали сме достигнали лимита
            if len(self.timestamps) >= self.calls:
                sleep_time = self.period - (now - self.timestamps[0])
                if sleep_time > 0:
                    logger.warning(
                        f"Rate limit reached. Sleeping for {sleep_time:.2f}s"
                    )
                    time.sleep(sleep_time)
                    # Изчистваме старите timestamps след sleep
                    now = time.time()
                    while self.timestamps and now - self.timestamps[0] > self.period:
                        self.timestamps.popleft()
            
            # Добавяме нов timestamp
            self.timestamps.append(now)
            
            # Изпълняваме функцията
            return func(*args, **kwargs)
        
        return wrapper
    
    def wait(self):
        """Изчаква ако е необходимо"""
        now = time.time()

        while self.timestamps and now - self.timestamps[0] > self.period:
            self.timestamps.popleft()

        if len(self.timestamps) >= self.calls:
            sleep_time = self.period - (now - self.timestamps[0])
            if sleep_time > 0:
                logger.debug(f"Rate limiter waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)
                # Update now after sleeping
                now = time.time()
                # Clean old timestamps again
                while self.timestamps and now - self.timestamps[0] > self.period:
                    self.timestamps.popleft()

        # Record this action
        self.timestamps.append(now)


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 5.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry decorator с exponential backoff

    Args:
        max_retries: Максимален брой опити
        delay: Начално забавяне в секунди (може да е float за по-прецизен контрол)
        backoff: Множител за exponential backoff
        exceptions: Tuple of exceptions за retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            current_delay = delay
            
            while attempt < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_retries}). "
                        f"Retrying in {current_delay}s... Error: {e}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        
        return wrapper
    
    return decorator


# Pre-configured rate limiters
requests_limiter = RateLimiter(calls=10, period=60)  # 10 requests per minute
page_limiter = RateLimiter(calls=1, period=5)  # 1 page every 5 seconds