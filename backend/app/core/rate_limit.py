"""
Simple in-memory rate limiter for auth endpoints.
Prevents brute force and abuse of verification/MFA endpoints.
"""
import time
import logging
from collections import defaultdict
from typing import Tuple

logger = logging.getLogger(__name__)

# Key -> list of timestamps
_auth_rate_store: dict[str, list[float]] = defaultdict(list)
# Cleanup threshold: remove entries older than 1 hour
_CLEANUP_AGE = 3600
# Default: 10 attempts per minute per key (IP or email)
_DEFAULT_MAX_ATTEMPTS = 10
_DEFAULT_WINDOW_SECONDS = 60


def _cleanup_old_entries(store: dict, max_age: float = _CLEANUP_AGE) -> None:
    """Remove expired entries to prevent memory growth."""
    now = time.monotonic()
    keys_to_remove = []
    for key, timestamps in store.items():
        cutoff = now - max_age
        new_ts = [t for t in timestamps if t > cutoff]
        if not new_ts:
            keys_to_remove.append(key)
        else:
            store[key] = new_ts
    for k in keys_to_remove:
        del store[k]


def check_rate_limit(
    key: str,
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    window_seconds: int = _DEFAULT_WINDOW_SECONDS,
) -> Tuple[bool, str]:
    """
    Check if key has exceeded rate limit.
    Returns (allowed, error_message).
    """
    _cleanup_old_entries(_auth_rate_store)
    now = time.monotonic()
    cutoff = now - window_seconds
    timestamps = _auth_rate_store[key]
    # Keep only recent attempts
    recent = [t for t in timestamps if t > cutoff]
    if len(recent) >= max_attempts:
        return False, f"Too many attempts. Please try again in {window_seconds} seconds."
    recent.append(now)
    _auth_rate_store[key] = recent
    return True, ""


def record_attempt(key: str) -> None:
    """Record an attempt (called when check_rate_limit returns True)."""
    # Already recorded in check_rate_limit
    pass
