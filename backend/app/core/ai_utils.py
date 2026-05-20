from typing import Tuple
from openai import AsyncOpenAI
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_ai_client() -> Tuple[AsyncOpenAI, str]:
    """
    Returns a configured AsyncOpenAI client and the model name to use.
    Respects settings.USE_LOCAL_AI.
    """
    if settings.USE_LOCAL_AI:
        client = AsyncOpenAI(
            api_key="not-needed",
            base_url=settings.LOCAL_AI_STATION_URL
        )
        model = settings.LOCAL_MODEL_NAME
        logger.debug(f"Using Local AI at {settings.LOCAL_AI_STATION_URL} with model {model}")
        return client, model
    
    # Default to OpenAI
    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1")
    )
    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    return client, model
