"""Felles LLM-klient for LangChain – støtter Ollama/Mistral lokalt og OpenAI i sky."""
from langchain_openai import ChatOpenAI
from app.core.config import settings


def get_chat_llm(*, temperature: float = 0.3, model: str | None = None) -> ChatOpenAI:
    if settings.USE_LOCAL_AI:
        return ChatOpenAI(
            model=model or settings.LOCAL_MODEL_NAME,
            api_key="ollama",
            base_url=settings.LOCAL_AI_STATION_URL,
            temperature=temperature,
        )
    return ChatOpenAI(
        model=model or settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        temperature=temperature,
    )
