"""LLM adapters package for AI provider integration."""

from typing import Optional
import logging
import os

from .base_adapter import (
    BaseLLMAdapter,
    LLMMessage,
    LLMResponse,
    LLMProvider
)

# Lazy imports to avoid loading all dependencies
_ADAPTERS = {}

logger = logging.getLogger(__name__)


# ============================================================================
# Public API
# ============================================================================

async def get_adapter(
    provider: Optional[str] = None,
    **kwargs
) -> BaseLLMAdapter:
    """Get an LLM adapter based on configuration."""
    # Get provider from environment if not specified
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "").lower()
    
    if not provider:
        raise ValueError(
            "LLM provider not specified. Set LLM_PROVIDER in .env file or "
            "pass provider argument to get_adapter()"
        )
    
    # Validate provider
    try:
        provider_enum = LLMProvider(provider)
    except ValueError:
        valid_providers = [p.value for p in LLMProvider]
        raise ValueError(
            f"Invalid LLM provider: {provider}. "
            f"Must be one of: {', '.join(valid_providers)}"
        )
    
    # Import and instantiate adapter
    if provider_enum == LLMProvider.OPENAI:
        from .openai_adapter import OpenAIAdapter
        return OpenAIAdapter(**kwargs)
    
    elif provider_enum == LLMProvider.ANTHROPIC:
        from .anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter(**kwargs)
    
    elif provider_enum == LLMProvider.GOOGLE:
        from .google_adapter import GoogleAdapter
        return GoogleAdapter(**kwargs)
    
    elif provider_enum == LLMProvider.OLLAMA:
        from .ollama_adapter import OllamaAdapter
        return OllamaAdapter(**kwargs)
    
    elif provider_enum == LLMProvider.CUSTOM:
        from .openai_adapter import OpenAIAdapter
        # Custom provider uses OpenAI adapter with custom base URL
        return OpenAIAdapter(**kwargs)
    
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def list_available_providers() -> list[str]:
    """List all available LLM providers."""
    return [p.value for p in LLMProvider]


# ============================================================================
# Package Exports
# ============================================================================

__all__ = [
    # Main API
    "get_adapter",
    "list_available_providers",
    
    # Base classes
    "BaseLLMAdapter",
    "LLMMessage",
    "LLMResponse",
    "LLMProvider",
]
