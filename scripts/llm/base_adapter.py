"""Base LLM adapter interface for RePORTaLiN."""

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
    """Represents a single message in a conversation."""
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
    """Represents a response from an LLM."""
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
    """Abstract base class for all LLM adapters."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "",
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3
    ) -> None:
        """Initialize the LLM adapter."""
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
        """Validate adapter configuration."""
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
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def generate_chat(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None
    ) -> LLMResponse:
        """Generate a response from a conversation history."""
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
        """Stream a response from the LLM."""
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate that the adapter can connect to the LLM service."""
        pass
    
    def __repr__(self) -> str:
        """Return a string representation of the adapter."""
        return (
            f"{self.__class__.__name__}("
            f"provider={self.provider.value}, "
            f"model={self.model}, "
            f"base_url={self.base_url})"
        )
