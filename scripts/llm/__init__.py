"""LLM adapters package for multi-provider AI integration (FUTURE).

This package provides a unified interface for interacting with multiple Large
Language Model (LLM) providers including OpenAI, Anthropic, Google Gemini, and
Ollama. It implements the adapter pattern to abstract away provider-specific
APIs and provide consistent messaging across all platforms.

Package Architecture:
    **Base Infrastructure** (base_adapter.py):
        - BaseLLMAdapter: Abstract base class for all adapters
        - LLMMessage: Standardized message format (role + content)
        - LLMResponse: Standardized response format
        - LLMProvider: Enum of supported providers
    
    **Provider Adapters** (future implementations):
        - openai_adapter.py: OpenAI GPT models (GPT-4, GPT-3.5-turbo)
        - anthropic_adapter.py: Anthropic Claude models
        - google_adapter.py: Google Gemini models
        - ollama_adapter.py: Local Ollama models
    
    **Factory Function**:
        - get_adapter(): Provider-agnostic adapter instantiation

Design Patterns:
    **Adapter Pattern**: Each provider (OpenAI, Anthropic, etc.) implements
    the same BaseLLMAdapter interface, allowing seamless switching between
    providers without code changes.
    
    **Lazy Loading**: Provider-specific SDKs are imported only when that
    provider is requested, avoiding unnecessary dependencies.
    
    **Environment Configuration**: Provider selection and API keys are
    configured via environment variables (.env file), not hardcoded.

Current Status:
    **PARTIALLY IMPLEMENTED**
    
    - ✅ Base classes defined (BaseLLMAdapter, LLMMessage, etc.)
    - ✅ Factory function implemented (get_adapter)
    - ⏳ Provider adapters pending implementation
    - ⏳ RAG integration pending

Public API:
    **Factory Functions**:
        - get_adapter: Create adapter for specified provider
        - list_available_providers: List all supported providers
    
    **Base Classes** (for extending):
        - BaseLLMAdapter: Abstract base for custom adapters
        - LLMMessage: Message structure for conversations
        - LLMResponse: Standardized response format
        - LLMProvider: Enum of provider identifiers

Environment Variables:
    The package expects these variables in .env:
        - LLM_PROVIDER: Provider name (openai, anthropic, google, ollama)
        - OPENAI_API_KEY: OpenAI API key (if using OpenAI)
        - ANTHROPIC_API_KEY: Anthropic API key (if using Anthropic)
        - GOOGLE_API_KEY: Google API key (if using Gemini)
        - OLLAMA_BASE_URL: Ollama server URL (if using Ollama)

Example:
    >>> # Get default adapter from environment (future)
    >>> from scripts.llm import get_adapter
    >>> 
    >>> # Create adapter (reads LLM_PROVIDER from .env)
    >>> adapter = await get_adapter()  # doctest: +SKIP
    >>> 
    >>> # Send message
    >>> from scripts.llm import LLMMessage
    >>> messages = [
    ...     LLMMessage(role='user', content='What is tuberculosis?')
    ... ]  # doctest: +SKIP
    >>> response = await adapter.chat(messages)  # doctest: +SKIP
    >>> print(response.content)  # doctest: +SKIP
    >>> 
    >>> # Switch provider programmatically
    >>> anthropic_adapter = await get_adapter(provider='anthropic')  # doctest: +SKIP

Notes:
    - Requires async/await for all adapter operations
    - API keys must be set in environment variables
    - Future: Will integrate with scripts.session for conversation history
    - Future: Will integrate with scripts.vector_db for RAG queries

See Also:
    scripts.llm.base_adapter: Abstract base class and types
    scripts.session: Session management (uses LLM for queries)
    scripts.vector_db: Vector storage (provides context for RAG)
    requirements.txt: Provider SDK dependencies
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
