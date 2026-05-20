"""Embedding generation service using OpenAI Direct API."""
from typing import List
from openai import OpenAI
from app.core.config import settings
from app.services.infrastructure.logger import get_logger

logger = get_logger(__name__)

_client = None

def get_openai_client():
    """Get or create OpenAI client (Direct API)."""
    global _client
    if _client:
        return _client

    if settings.USE_LOCAL_AI:
        _client = OpenAI(
            api_key="ollama",
            base_url=settings.LOCAL_AI_STATION_URL,
        )
        logger.info("Using local Ollama for embeddings")
    elif not settings.OPENAI_API_KEY:
        logger.error("No OpenAI API Key configured.")
        return None
    else:
        _client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )
        logger.info("Using OpenAI Direct API")
    return _client

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for list of texts using OpenAI.
    """
    if not texts:
        return []
    
    client = get_openai_client()
    if not client:
        logger.error("No AI client available")
        raise RuntimeError("OpenAI configuration missing")
        
    try:
        # Determine model based on client type
        # OpenAI Direct
        model = (
            settings.OPENAI_EMBEDDING_MODEL
            if not settings.USE_LOCAL_AI
            else settings.OPENAI_EMBEDDING_MODEL or "nomic-embed-text"
        )
            
        response = client.embeddings.create(
            input=texts,
            model=model
        )
        
        # Extract embeddings in order
        data = sorted(response.data, key=lambda x: x.index)
        embeddings = [item.embedding for item in data]
        
        logger.debug(f"Generated embeddings for {len(texts)} texts using {model}")
        return embeddings
    
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise

def generate_query_embedding(query: str) -> List[float]:
    """
    Generate embedding for a query text.
    """
    embeddings = generate_embeddings([query])
    return embeddings[0] if embeddings else []
