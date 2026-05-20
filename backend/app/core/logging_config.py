"""
Centralized logging configuration (Fix 4 - CODE_REVIEW_30-01).
Use logger instead of print() for structured, level-based logging.
"""
import logging
import sys


def setup_logging(environment: str = "production") -> None:
    """Configure logging for the application."""
    log_level = logging.DEBUG if environment == "development" else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("app").setLevel(log_level)
