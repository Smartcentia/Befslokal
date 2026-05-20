import operator
from functools import wraps
import asyncio
import logging
from typing import Any, Callable, Optional, Dict

logger = logging.getLogger("GracefulDegradation")

# Simple in-memory cache for fallback patterns
_fallback_cache: Dict[str, Any] = {}

def graceful_degradation(
    fallback_value: Any = None,
    fallback_func: Optional[Callable] = None,
    timeout: float = 5.0,
    log_warning: bool = True
):
    """
    Decorator to apply graceful degradation pattern.
    If the function fails or times out, it uses a fallback.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Execute with timeout
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except (asyncio.TimeoutError, Exception) as e:
                if log_warning:
                    logger.warning(f"Function {func.__name__} failed or timed out: {e}. Using fallback.")
                
                if fallback_func:
                    res = fallback_func(*args, **kwargs)
                    if asyncio.iscoroutine(res):
                        return await res
                    return res
                return fallback_value
        return wrapper
    return decorator

def get_cached_data(key: str, ttl: int = 3600) -> Any:
    return _fallback_cache.get(key)

def set_cached_data(key: str, data: Any, ttl: int = 3600):
    _fallback_cache[key] = data
