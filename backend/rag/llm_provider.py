"""
LLM Provider

Factory for creating LLM instances. Supports Groq (default)
and OpenAI, selectable via the LLM_PROVIDER environment variable.
Streaming is enabled by default for real-time token delivery.
"""

from langchain_core.language_models import BaseChatModel

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def get_llm(
    temperature: float | None = None,
    max_tokens: int | None = None,
    streaming: bool = True
) -> BaseChatModel:
    """
    Create an LLM instance based on the configured provider.

    Args:
        temperature: Override default temperature (0.0 to 1.0).
        max_tokens: Override default max tokens.
        streaming: Whether to enable token streaming.

    Returns:
        A LangChain BaseChatModel instance (ChatGroq or ChatOpenAI).

    Raises:
        ValueError: If LLM_PROVIDER is not 'groq' or 'openai'.
        ValueError: If the required API key is not set.
    """
    temp = temperature if temperature is not None else settings.DEFAULT_TEMPERATURE
    tokens = max_tokens if max_tokens is not None else settings.DEFAULT_MAX_TOKENS
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment variables")

        from langchain_groq import ChatGroq
        llm = ChatGroq(
            model=settings.LLM_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=temp,
            max_tokens=tokens,
            streaming=streaming,
        )
        logger.info(f"Created Groq LLM: {settings.LLM_MODEL} (temp={temp}, max_tokens={tokens})")

    elif provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")

        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=temp,
            max_tokens=tokens,
            streaming=streaming,
        )
        logger.info(f"Created OpenAI LLM: {settings.LLM_MODEL} (temp={temp}, max_tokens={tokens})")

    else:
        raise ValueError(
            f"Unsupported LLM provider: '{provider}'. "
            f"Use 'groq' or 'openai'."
        )

    return llm
