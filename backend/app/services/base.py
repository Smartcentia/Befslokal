import logging
from typing import Any, Dict, Optional

class BaseService:
    """
    Base class for all domain services.
    Provides standardized logging and error handling hooks.
    """
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(self, *args, **kwargs) -> Any:
        """
        Execute the main logic of the service.
        Subclasses should override specific methods, but this remains a common entry point if needed.
        """
        raise NotImplementedError("Subclasses must implement execution logic.")

    def log_error(self, message: str, error: Optional[Exception] = None):
        if error:
            self.logger.error(f"{message}: {str(error)}", exc_info=True)
        else:
            self.logger.error(message)

    def log_info(self, message: str):
        self.logger.info(message)
