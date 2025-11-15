"""
LLM Adapters Package for RePORTaLiN
====================================

This package provides pluggable LLM adapters for different AI providers.
Users must provide their own API keys - RePORTaLiN does NOT include
any built-in LLM functionality.

Supported Providers:
--------------------
- OpenAI (ChatGPT, GPT-4, GPT-3.5)
- Anthropic (Claude 3.5, Claude 3)
- Google (Gemini 1.5 Pro)
- Ollama (Local open-source models)
- Custom (OpenAI-compatible APIs)

Usage:
------
    from scripts.llm import get_adapter
    
    # Get adapter based on .env configuration
    adapter = await get_adapter()
    
    # Generate response
    response = await adapter.generate(
        prompt="What is pneumonia?",
        max_tokens=512
    )

Author: RePORTaLiN Team
Date: January 12, 2025
"""

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
    """
    Get an LLM adapter based on configuration.
    
    Args:
        provider: Provider name (openai, anthropic, google, ollama, custom)
                 If None, will read from LLM_PROVIDER environment variable
        **kwargs: Additional arguments passed to adapter constructor
        
    Returns:
        Configured LLM adapter instance
        
    Raises:
        ValueError: If provider is invalid or not configured
        ImportError: If required dependencies are not installed
        
    Example:
        >>> adapter = await get_adapter(provider="openai")
        >>> response = await adapter.generate("Hello!")
    """
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
    """
    List all available LLM providers.
    
    Returns:
        List of provider names
    """
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
