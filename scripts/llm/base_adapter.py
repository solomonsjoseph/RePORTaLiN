"""
Base LLM Adapter Interface for RePORTaLiN
==========================================

This module defines the abstract base class for all LLM adapters in the
RePORTaLiN system. It provides a consistent interface for interacting with
different LLM providers (OpenAI, Anthropic, Google, Ollama, etc.).

Architecture:
-------------
- Abstract base class using ABC (Abstract Base Class)
- Type hints for all methods and parameters (PEP 484/526)
- Consistent error handling across all providers
- Streaming support for real-time responses
- Token usage tracking for cost monitoring

Usage:
------
    from scripts.llm.openai_adapter import OpenAIAdapter
    
    adapter = OpenAIAdapter(api_key="sk-...", model="gpt-4")
    response = await adapter.generate(
        prompt="What is pneumonia?",
        max_tokens=512,
        temperature=0.7
    )

Author: RePORTaLiN Team
Date: January 12, 2025
License: See project LICENSE file
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncIterator, Any
from dataclasses import dataclass
from enum import Enum

# Import enhanced logging system
from scripts.utils import logging_system as log

# Setup enhanced logger for LLM operations
log.setup_logging(
    module_name="scripts.llm.base_adapter",
    log_level="INFO"
)


# ============================================================================
# Data Classes for Type Safety
# ============================================================================

@dataclass
class LLMMessage:
    """
    Represents a single message in a conversation.
    
    Attributes:
        role: The role of the message sender ('system', 'user', 'assistant')
        content: The actual message content
        metadata: Optional metadata (e.g., timestamps, annotations)
    """
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        """Validate message after initialization."""
        valid_roles = {'system', 'user', 'assistant'}
        if self.role not in valid_roles:
            raise ValueError(f"Invalid role: {self.role}. Must be one of {valid_roles}")


@dataclass
class LLMResponse:
    """
    Represents a response from an LLM.
    
    Attributes:
        content: The generated text response
        model: The model that generated the response
        provider: The LLM provider (openai, anthropic, google, ollama, custom)
        usage: Token usage statistics
        finish_reason: Reason for completion ('stop', 'length', 'content_filter')
        metadata: Additional provider-specific metadata
    """
    content: str
    model: str
    provider: str
    usage: Dict[str, int]  # {'prompt_tokens': X, 'completion_tokens': Y, 'total_tokens': Z}
    finish_reason: str
    metadata: Optional[Dict[str, Any]] = None


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    CUSTOM = "custom"


# ============================================================================
# Abstract Base Adapter
# ============================================================================

class BaseLLMAdapter(ABC):
    """
    Abstract base class for all LLM adapters.
    
    This class defines the interface that all LLM adapters must implement.
    It ensures consistency across different providers while allowing for
    provider-specific customizations.
    
    Attributes:
        api_key: API key for authentication (None for local models like Ollama)
        model: Model identifier (e.g., 'gpt-4', 'claude-3-5-sonnet')
        base_url: Optional custom API endpoint
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "",
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3
    ) -> None:
        """
        Initialize the LLM adapter.
        
        Args:
            api_key: API key for authentication
            model: Model identifier
            base_url: Optional custom API endpoint
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Validate configuration
        self._validate_config()
        
        log.info(f"Initialized {self.provider.value} adapter with model: {model}")
    
    @property
    @abstractmethod
    def provider(self) -> LLMProvider:
        """Return the provider type."""
        pass
    
    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate adapter configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            system_prompt: Optional system prompt for context
            stop_sequences: Optional list of sequences to stop generation
            
        Returns:
            LLMResponse object with generated content and metadata
            
        Raises:
            Exception: If API call fails after retries
        """
        pass
    
    @abstractmethod
    async def generate_chat(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None
    ) -> LLMResponse:
        """
        Generate a response from a conversation history.
        
        Args:
            messages: List of conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            stop_sequences: Optional list of sequences to stop generation
            
        Returns:
            LLMResponse object with generated content and metadata
            
        Raises:
            Exception: If API call fails after retries
        """
        pass
    
    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> AsyncIterator[str]:
        """
        Stream a response from the LLM.
        
        Args:
            prompt: The user prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            system_prompt: Optional system prompt for context
            stop_sequences: Optional list of sequences to stop generation
            
        Yields:
            Chunks of generated text as they arrive
            
        Raises:
            Exception: If API call fails after retries
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Number of tokens
        """
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate that the adapter can connect to the LLM service.
        
        Returns:
            True if connection is valid, False otherwise
        """
        pass
    
    def __repr__(self) -> str:
        """Return a string representation of the adapter."""
        return (
            f"{self.__class__.__name__}("
            f"provider={self.provider.value}, "
            f"model={self.model}, "
            f"base_url={self.base_url})"
        )
