"""Base LLM adapter interface for multi-provider LLM integration.

Defines abstract base class and data structures for unified LLM provider access
(OpenAI, Anthropic, Google, Ollama, custom). Provides type-safe message/response
handling, connection validation, token counting, and async streaming support.
Foundation for extensible, provider-agnostic LLM integration in RePORTaLiN.

**Architecture:**
```
BaseLLMAdapter (Abstract)
    ↓
Provider-Specific Adapters (OpenAIAdapter, AnthropicAdapter, etc.)
    ↓
LLM API (OpenAI, Anthropic, Google, Ollama)
```

**Key Components:**

1. **LLMMessage**: Type-safe conversation message with role validation
2. **LLMResponse**: Standardized LLM response with usage tracking
3. **LLMProvider**: Enum of supported providers (extensible)
4. **BaseLLMAdapter**: Abstract base defining adapter contract

**Capabilities:**

- **Multi-Provider Support**: Unified interface for OpenAI, Anthropic, Google, Ollama
- **Type Safety**: Dataclasses for messages/responses, enum for providers
- **Async Support**: All generation methods are async (await-able)
- **Streaming**: AsyncIterator-based streaming for real-time responses
- **Connection Validation**: validate_connection() for health checks
- **Token Counting**: Provider-specific token counting
- **Retry Logic**: max_retries configuration for resilience
- **Metadata**: Optional metadata dict for all messages/responses

**Supported Providers:**

- **OpenAI**: GPT-3.5, GPT-4, GPT-4-turbo (via OpenAI API)
- **Anthropic**: Claude 2, Claude 3 (via Anthropic API)
- **Google**: PaLM, Gemini (via Google AI API)
- **Ollama**: Local models (llama2, mistral, etc.)
- **Custom**: Extensible for custom providers

**Usage Patterns:**

Subclass BaseLLMAdapter for custom provider:
    >>> from scripts.llm.base_adapter import BaseLLMAdapter, LLMProvider, LLMResponse, LLMMessage
    >>> from typing import AsyncIterator
    >>> 
    >>> class CustomAdapter(BaseLLMAdapter):  # doctest: +SKIP
    ...     @property
    ...     def provider(self) -> LLMProvider:
    ...         return LLMProvider.CUSTOM
    ...     
    ...     def _validate_config(self) -> None:
    ...         if not self.api_key:
    ...             raise ValueError("API key required")
    ...     
    ...     async def generate(self, prompt: str, **kwargs) -> LLMResponse:
    ...         # Implementation
    ...         pass
    ...     
    ...     async def generate_chat(self, messages: list, **kwargs) -> LLMResponse:
    ...         # Implementation
    ...         pass
    ...     
    ...     async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
    ...         # Implementation
    ...         pass
    ...     
    ...     async def count_tokens(self, text: str) -> int:
    ...         # Implementation
    ...         pass
    ...     
    ...     async def validate_connection(self) -> bool:
    ...         # Implementation
    ...         pass

Create and use adapter (example):
    >>> # Actual usage with implemented adapter:
    >>> # adapter = OpenAIAdapter(api_key="sk-...", model="gpt-4")  # doctest: +SKIP
    >>> # 
    >>> # # Single prompt generation
    >>> # response = await adapter.generate(
    >>> #     prompt="Explain clinical trial data management",
    >>> #     max_tokens=500,
    >>> #     temperature=0.5
    >>> # )  # doctest: +SKIP
    >>> # print(response.content)  # doctest: +SKIP
    >>> # 
    >>> # # Chat conversation
    >>> # messages = [
    >>> #     LLMMessage(role="system", content="You are a helpful assistant"),
    >>> #     LLMMessage(role="user", content="What is TB?")
    >>> # ]  # doctest: +SKIP
    >>> # response = await adapter.generate_chat(messages, max_tokens=200)  # doctest: +SKIP
    >>> # 
    >>> # # Streaming generation
    >>> # async for chunk in adapter.stream_generate(
    >>> #     prompt="Describe data privacy regulations",
    >>> #     max_tokens=1000
    >>> # ):
    >>> #     print(chunk, end='', flush=True)  # doctest: +SKIP

Message validation:
    >>> msg = LLMMessage(role="user", content="Hello")
    >>> msg.role
    'user'
    >>> # Invalid role raises ValueError:
    >>> # LLMMessage(role="invalid", content="test")  # Raises ValueError

**Dependencies:**
- abc: Abstract base class support
- dataclasses: Type-safe data structures
- enum: Provider enumeration
- typing: Type hints (AsyncIterator, Optional, etc.)
- logging_system: Centralized logging

**Error Handling:**
- ValueError: Invalid LLMMessage role, invalid provider configuration
- NotImplementedError: Abstract methods called without implementation
- Provider-specific errors: Handled by concrete adapter implementations

**Configuration:**

Initialization parameters (BaseLLMAdapter):
- api_key: Provider API key (optional for local models)
- model: Model identifier (e.g., "gpt-4", "claude-3-opus")
- base_url: Custom API endpoint (optional)
- timeout: Request timeout in seconds (default: 60)
- max_retries: Retry attempts for failed requests (default: 3)

Generation parameters:
- max_tokens: Maximum response tokens (default: 1024)
- temperature: Sampling temperature 0.0-1.0 (default: 0.7)
- system_prompt: System message (for generate())
- stop_sequences: Stop generation sequences

See Also:
    Future implementations: scripts.llm.openai_adapter, scripts.llm.anthropic_adapter

Note:
    All generation methods are async—must be awaited or used in async context.
    Concrete adapters must implement all abstract methods. Provider enum
    extensible for new providers. Metadata dicts are optional for custom tracking.
    Token counting is provider-specific—implementation varies by model.
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
    """Single message in LLM conversation with role validation.
    
    Type-safe representation of a conversation message (system, user, assistant).
    Used in generate_chat() for multi-turn conversations. Validates role on
    initialization via __post_init__.
    
    Attributes:
        role (str): Message role. Must be 'system', 'user', or 'assistant'.
        content (str): Message text content.
        metadata (Optional[Dict[str, Any]]): Optional metadata for tracking.
            Default: None.
    
    Raises:
        ValueError: If role not in {'system', 'user', 'assistant'}.
    
    Example:
        Create valid messages:
            >>> from scripts.llm.base_adapter import LLMMessage
            >>> msg = LLMMessage(role="user", content="What is TB?")
            >>> msg.role
            'user'
            >>> msg.content
            'What is TB?'
        
        With metadata:
            >>> msg = LLMMessage(
            ...     role="assistant",
            ...     content="TB is tuberculosis.",
            ...     metadata={"confidence": 0.95}
            ... )
            >>> msg.metadata['confidence']
            0.95
        
        Invalid role raises error:
            >>> try:
            ...     LLMMessage(role="invalid", content="test")
            ... except ValueError as e:
            ...     print("Error:", e)
            Error: Invalid role: invalid. Must be one of {'system', 'user', 'assistant'}
    
    Note:
        role validation happens in __post_init__ (after __init__). Metadata
        dict is mutable—copy before modifying if sharing across messages.
        Used as List[LLMMessage] in generate_chat().
    """
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        """Validate message role after initialization.
        
        Checks that role is one of {'system', 'user', 'assistant'}. Called
        automatically by dataclass after __init__.
        
        Raises:
            ValueError: If role not in valid set.
        
        Example:
            Automatic validation on creation:
                >>> msg = LLMMessage(role="user", content="test")  # Valid, no error
                >>> # LLMMessage(role="bot", content="test")  # Raises ValueError
        
        Note:
            Called by dataclass machinery, not manually invoked. Part of
            dataclass initialization chain.
        """
        valid_roles = {'system', 'user', 'assistant'}
        if self.role not in valid_roles:
            raise ValueError(f"Invalid role: {self.role}. Must be one of {valid_roles}")


@dataclass
class LLMResponse:
    """Standardized LLM response with usage tracking and metadata.
    
    Unified response format across all LLM providers. Contains generated content,
    model info, token usage, finish reason, and optional metadata. Returned by
    generate() and generate_chat() methods.
    
    Attributes:
        content (str): Generated text response.
        model (str): Model identifier (e.g., "gpt-4", "claude-3-opus").
        provider (str): Provider name (e.g., "openai", "anthropic").
        usage (Dict[str, int]): Token usage dict with keys:
            - 'prompt_tokens': Input tokens
            - 'completion_tokens': Generated tokens
            - 'total_tokens': Sum of prompt + completion
        finish_reason (str): Why generation stopped (e.g., "stop", "length",
            "content_filter"). Provider-specific.
        metadata (Optional[Dict[str, Any]]): Optional metadata (latency, etc.).
            Default: None.
    
    Example:
        Create response (typically by adapter):
            >>> from scripts.llm.base_adapter import LLMResponse
            >>> response = LLMResponse(
            ...     content="TB is tuberculosis, a bacterial infection.",
            ...     model="gpt-4",
            ...     provider="openai",
            ...     usage={'prompt_tokens': 15, 'completion_tokens': 10, 'total_tokens': 25},
            ...     finish_reason="stop"
            ... )
            >>> response.content
            'TB is tuberculosis, a bacterial infection.'
            >>> response.usage['total_tokens']
            25
        
        With metadata:
            >>> response = LLMResponse(
            ...     content="Sample response",
            ...     model="claude-3",
            ...     provider="anthropic",
            ...     usage={'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15},
            ...     finish_reason="stop",
            ...     metadata={"latency_ms": 234, "cached": False}
            ... )
            >>> response.metadata['latency_ms']
            234
    
    Note:
        usage dict structure is standardized but token counts may vary by provider.
        finish_reason values differ by provider: OpenAI uses "stop", "length",
        "content_filter"; Anthropic uses "end_turn", "max_tokens", etc. Metadata
        dict is mutable—copy before modifying if sharing.
    """
    content: str
    model: str
    provider: str
    usage: Dict[str, int]  # {'prompt_tokens': X, 'completion_tokens': Y, 'total_tokens': Z}
    finish_reason: str
    metadata: Optional[Dict[str, Any]] = None


class LLMProvider(str, Enum):
    """Enumeration of supported LLM providers.
    
    String-based enum for type-safe provider identification. Used in adapter's
    provider property. Extensible for new providers.
    
    Attributes:
        OPENAI: OpenAI API (GPT-3.5, GPT-4, etc.)
        ANTHROPIC: Anthropic API (Claude 2, Claude 3, etc.)
        GOOGLE: Google AI API (PaLM, Gemini, etc.)
        OLLAMA: Ollama local models (llama2, mistral, etc.)
        CUSTOM: Custom/third-party providers
    
    Example:
        Use in adapter:
            >>> from scripts.llm.base_adapter import LLMProvider
            >>> provider = LLMProvider.OPENAI
            >>> provider.value
            'openai'
            >>> provider == "openai"  # String comparison works
            True
        
        Iteration:
            >>> providers = [p.value for p in LLMProvider]
            >>> 'openai' in providers
            True
            >>> 'anthropic' in providers
            True
    
    Note:
        Inherits from str and Enum—can be compared directly to strings.
        Add new providers by adding enum members (e.g., COHERE = "cohere").
    """
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    CUSTOM = "custom"


# ============================================================================
# Abstract Base Adapter
# ============================================================================

class BaseLLMAdapter(ABC):
    """Abstract base class for unified LLM provider adapters.
    
    Defines contract for provider-specific LLM adapters (OpenAI, Anthropic, Google,
    Ollama, custom). Provides initialization, configuration validation, and abstract
    methods for generation, chat, streaming, token counting, and connection validation.
    Subclass and implement all abstract methods to create custom adapter.
    
    **Required Implementations:**
    
    All subclasses must implement:
    1. provider (property): Return LLMProvider enum value
    2. _validate_config(): Validate provider-specific configuration
    3. generate(): Single-prompt generation
    4. generate_chat(): Multi-turn conversation generation
    5. stream_generate(): Streaming generation (AsyncIterator)
    6. count_tokens(): Token counting for provider's tokenizer
    7. validate_connection(): Health check / API connection test
    
    Attributes:
        api_key (Optional[str]): Provider API key (None for local models).
        model (str): Model identifier (e.g., "gpt-4", "claude-3-opus").
        base_url (Optional[str]): Custom API endpoint (None for default).
        timeout (int): Request timeout in seconds.
        max_retries (int): Retry attempts for failed requests.
    
    Example:
        Subclass for custom provider:
            >>> from scripts.llm.base_adapter import BaseLLMAdapter, LLMProvider, LLMResponse, LLMMessage
            >>> from typing import AsyncIterator
            >>> 
            >>> class MyAdapter(BaseLLMAdapter):  # doctest: +SKIP
            ...     @property
            ...     def provider(self) -> LLMProvider:
            ...         return LLMProvider.CUSTOM
            ...     
            ...     def _validate_config(self) -> None:
            ...         if not self.api_key:
            ...             raise ValueError("API key required")
            ...     
            ...     async def generate(self, prompt: str, **kwargs) -> LLMResponse:
            ...         # Call provider API
            ...         return LLMResponse(...)
            ...     
            ...     async def generate_chat(self, messages, **kwargs) -> LLMResponse:
            ...         # Call provider chat API
            ...         return LLMResponse(...)
            ...     
            ...     async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
            ...         # Yield chunks
            ...         yield "chunk1"
            ...         yield "chunk2"
            ...     
            ...     async def count_tokens(self, text: str) -> int:
            ...         # Use provider tokenizer
            ...         return len(text.split())  # Simplified
            ...     
            ...     async def validate_connection(self) -> bool:
            ...         # Test API connection
            ...         return True
        
        Use adapter:
            >>> # adapter = MyAdapter(api_key="sk-...", model="my-model")  # doctest: +SKIP
            >>> # response = await adapter.generate("Hello")  # doctest: +SKIP
    
    Note:
        All generation methods are async—must be awaited. _validate_config()
        called during __init__—raise ValueError for invalid config. Logs
        initialization message (info level) via logging_system.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "",
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3
    ) -> None:
        """Initialize LLM adapter with configuration and validation.
        
        Sets configuration attributes and calls _validate_config() to verify
        provider-specific requirements. Logs initialization message.
        
        Args:
            api_key (Optional[str], optional): Provider API key. Required for
                cloud providers (OpenAI, Anthropic, Google); optional for local
                (Ollama). Default: None.
            model (str, optional): Model identifier. Examples: "gpt-4",
                "claude-3-opus", "llama2". Default: "" (must be set by subclass).
            base_url (Optional[str], optional): Custom API endpoint URL. If None,
                uses provider default. Useful for proxies or custom deployments.
                Default: None.
            timeout (int, optional): Request timeout in seconds. Applies to all
                API calls. Default: 60.
            max_retries (int, optional): Maximum retry attempts for failed
                requests (network errors, rate limits). Default: 3.
        
        Raises:
            ValueError: If _validate_config() detects invalid configuration
                (missing API key, invalid model, etc.). Provider-specific.
        
        Example:
            Initialize adapter (via subclass):
                >>> # adapter = OpenAIAdapter(  # doctest: +SKIP
                >>> #     api_key="sk-...",
                >>> #     model="gpt-4",
                >>> #     timeout=30,
                >>> #     max_retries=5
                >>> # )
        
        Side Effects:
            - Calls _validate_config() (may raise ValueError)
            - Logs initialization message (info level)
        
        Note:
            Base class doesn't validate specific parameters—_validate_config()
            handles provider-specific validation. Subclasses should call
            super().__init__(...) first, then add custom initialization.
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
        """Return the LLM provider type identifier.
        
        Abstract property that must return provider enum value. Used for logging,
        response metadata, and adapter identification.
        
        Returns:
            LLMProvider: Provider enum value (OPENAI, ANTHROPIC, GOOGLE, etc.)
        
        Example:
            Implementation in subclass:
                >>> # class OpenAIAdapter(BaseLLMAdapter):  # doctest: +SKIP
                >>> #     @property
                >>> #     def provider(self) -> LLMProvider:
                >>> #         return LLMProvider.OPENAI
        
        Note:
            Must be implemented by all subclasses. Accessed via self.provider.value
            for string representation.
        """
        pass
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider-specific adapter configuration.
        
        Called during __init__ to verify required configuration (API key, model,
        base_url, etc.). Must raise ValueError for invalid configuration.
        
        Raises:
            ValueError: If configuration invalid (missing API key, invalid model,
                malformed base_url, etc.). Error message should be descriptive.
        
        Example:
            Implementation in subclass:
                >>> # class OpenAIAdapter(BaseLLMAdapter):  # doctest: +SKIP
                >>> #     def _validate_config(self) -> None:
                >>> #         if not self.api_key:
                >>> #             raise ValueError("OpenAI API key required")
                >>> #         if not self.model:
                >>> #             raise ValueError("Model name required")
        
        Note:
            Private method (leading underscore). Called automatically during
            __init__—don't call manually. Should validate all required config.
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
        """Generate response from single prompt (async).
        
        Core generation method for single-turn prompts. Sends prompt to LLM API
        and returns standardized LLMResponse. Supports system prompt, token limit,
        temperature, and stop sequences.
        
        Args:
            prompt (str): User prompt text to generate response for.
            max_tokens (int, optional): Maximum tokens to generate. Provider may
                return fewer. Default: 1024.
            temperature (float, optional): Sampling temperature (0.0-1.0).
                Lower = more deterministic, higher = more creative. Default: 0.7.
            system_prompt (Optional[str], optional): System message to prepend.
                Sets assistant behavior/context. Default: None.
            stop_sequences (Optional[List[str]], optional): List of strings that
                stop generation when encountered. Default: None.
        
        Returns:
            LLMResponse: Standardized response with content, model, provider,
                usage, finish_reason, metadata.
        
        Raises:
            Provider-specific exceptions: API errors, rate limits, auth failures,
                timeout errors, etc. Implementation-dependent.
        
        Example:
            Implementation in subclass:
                >>> # class OpenAIAdapter(BaseLLMAdapter):  # doctest: +SKIP
                >>> #     async def generate(self, prompt, **kwargs) -> LLMResponse:
                >>> #         response = await openai.ChatCompletion.acreate(
                >>> #             model=self.model,
                >>> #             messages=[
                >>> #                 {"role": "system", "content": kwargs.get("system_prompt", "")},
                >>> #                 {"role": "user", "content": prompt}
                >>> #             ],
                >>> #             max_tokens=kwargs.get("max_tokens", 1024),
                >>> #             temperature=kwargs.get("temperature", 0.7)
                >>> #         )
                >>> #         return LLMResponse(
                >>> #             content=response.choices[0].message.content,
                >>> #             model=response.model,
                >>> #             provider=self.provider.value,
                >>> #             usage=dict(response.usage),
                >>> #             finish_reason=response.choices[0].finish_reason
                >>> #         )
            
            Usage:
                >>> # adapter = OpenAIAdapter(api_key="sk-...", model="gpt-4")  # doctest: +SKIP
                >>> # response = await adapter.generate(
                >>> #     prompt="Explain TB",
                >>> #     max_tokens=500,
                >>> #     temperature=0.5,
                >>> #     system_prompt="You are a medical expert"
                >>> # )  # doctest: +SKIP
        
        Note:
            Async method—must be awaited. Implementations should handle retries
            (via self.max_retries), timeouts (via self.timeout), and error logging.
            system_prompt handling varies by provider (some use chat format).
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
        """Generate response from conversation history (async).
        
        Multi-turn conversation generation. Sends list of LLMMessage objects
        (system, user, assistant roles) to LLM API and returns response.
        Maintains conversation context.
        
        Args:
            messages (List[LLMMessage]): Conversation history. Order matters.
                Each message has role ('system', 'user', 'assistant') and content.
            max_tokens (int, optional): Maximum tokens to generate. Default: 1024.
            temperature (float, optional): Sampling temperature (0.0-1.0).
                Default: 0.7.
            stop_sequences (Optional[List[str]], optional): Generation stop
                strings. Default: None.
        
        Returns:
            LLMResponse: Standardized response with content, model, provider,
                usage, finish_reason, metadata.
        
        Raises:
            ValueError: If messages empty or roles invalid (caught by LLMMessage).
            Provider-specific exceptions: API errors, rate limits, auth failures,
                timeout errors, etc.
        
        Example:
            Implementation in subclass:
                >>> # class OpenAIAdapter(BaseLLMAdapter):  # doctest: +SKIP
                >>> #     async def generate_chat(self, messages, **kwargs) -> LLMResponse:
                >>> #         api_messages = [
                >>> #             {"role": msg.role, "content": msg.content}
                >>> #             for msg in messages
                >>> #         ]
                >>> #         response = await openai.ChatCompletion.acreate(
                >>> #             model=self.model,
                >>> #             messages=api_messages,
                >>> #             max_tokens=kwargs.get("max_tokens", 1024),
                >>> #             temperature=kwargs.get("temperature", 0.7)
                >>> #         )
                >>> #         return LLMResponse(...)
            
            Usage:
                >>> # from scripts.llm.base_adapter import LLMMessage
                >>> # messages = [
                >>> #     LLMMessage(role="system", content="You are helpful"),
                >>> #     LLMMessage(role="user", content="What is TB?"),
                >>> #     LLMMessage(role="assistant", content="TB is tuberculosis"),
                >>> #     LLMMessage(role="user", content="How is it transmitted?")
                >>> # ]  # doctest: +SKIP
                >>> # response = await adapter.generate_chat(messages)  # doctest: +SKIP
        
        Note:
            Async method—must be awaited. messages list should start with system
            message (optional), then alternate user/assistant. Implementations
            should validate message sequence and handle provider-specific formats.
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
        """Stream response chunks from LLM in real-time (async iterator).
        
        Streaming generation for real-time output. Yields response text chunks
        as they're generated by LLM. Useful for long responses and user feedback.
        Returns AsyncIterator that must be iterated with 'async for'.
        
        Args:
            prompt (str): User prompt text.
            max_tokens (int, optional): Maximum tokens to generate. Default: 1024.
            temperature (float, optional): Sampling temperature (0.0-1.0).
                Default: 0.7.
            system_prompt (Optional[str], optional): System message. Default: None.
            stop_sequences (Optional[List[str]], optional): Stop strings.
                Default: None.
        
        Yields:
            str: Response text chunks as generated. May be words, sentences, or
                tokens depending on provider.
        
        Raises:
            Provider-specific exceptions: API errors, rate limits, auth failures,
                timeout errors, stream interruption, etc.
        
        Example:
            Implementation in subclass:
                >>> # class OpenAIAdapter(BaseLLMAdapter):  # doctest: +SKIP
                >>> #     async def stream_generate(self, prompt, **kwargs) -> AsyncIterator[str]:
                >>> #         stream = await openai.ChatCompletion.acreate(
                >>> #             model=self.model,
                >>> #             messages=[{"role": "user", "content": prompt}],
                >>> #             max_tokens=kwargs.get("max_tokens", 1024),
                >>> #             temperature=kwargs.get("temperature", 0.7),
                >>> #             stream=True
                >>> #         )
                >>> #         async for chunk in stream:
                >>> #             if chunk.choices[0].delta.content:
                >>> #                 yield chunk.choices[0].delta.content
            
            Usage:
                >>> # adapter = OpenAIAdapter(api_key="sk-...", model="gpt-4")  # doctest: +SKIP
                >>> # async for chunk in adapter.stream_generate(
                >>> #     prompt="Explain data privacy",
                >>> #     max_tokens=1000
                >>> # ):
                >>> #     print(chunk, end='', flush=True)  # doctest: +SKIP
        
        Note:
            Async generator—use 'async for' to iterate. Chunk size/granularity
            varies by provider. Implementations should handle stream interruption
            and cleanup. No LLMResponse returned—only text chunks.
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text using provider's tokenizer (async).
        
        Provider-specific token counting for cost estimation and prompt length
        validation. Uses same tokenizer as LLM model.
        
        Args:
            text (str): Text to count tokens in. Can be empty.
        
        Returns:
            int: Number of tokens. Returns 0 for empty text.
        
        Example:
            Implementation in subclass:
                >>> # import tiktoken
                >>> # class OpenAIAdapter(BaseLLMAdapter):  # doctest: +SKIP
                >>> #     async def count_tokens(self, text: str) -> int:
                >>> #         encoding = tiktoken.encoding_for_model(self.model)
                >>> #         return len(encoding.encode(text))
            
            Usage:
                >>> # adapter = OpenAIAdapter(api_key="sk-...", model="gpt-4")  # doctest: +SKIP
                >>> # count = await adapter.count_tokens("Hello world")  # doctest: +SKIP
                >>> # print(f"Tokens: {count}")  # doctest: +SKIP
        
        Note:
            Async method—must be awaited. Token count may differ from other
            tokenizers (e.g., BERT vs GPT). Used for max_tokens validation and
            cost estimation.
        """
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate adapter can connect to LLM service (async health check).
        
        Tests API connection, authentication, and basic functionality. Used for
        startup validation and health monitoring. Should be fast (timeout quickly).
        
        Returns:
            bool: True if connection valid and API accessible, False otherwise.
        
        Example:
            Implementation in subclass:
                >>> # class OpenAIAdapter(BaseLLMAdapter):  # doctest: +SKIP
                >>> #     async def validate_connection(self) -> bool:
                >>> #         try:
                >>> #             # Simple API call to test connection
                >>> #             await openai.Model.aretrieve(self.model)
                >>> #             return True
                >>> #         except Exception as e:
                >>> #             log.error(f"Connection validation failed: {e}")
                >>> #             return False
            
            Usage:
                >>> # adapter = OpenAIAdapter(api_key="sk-...", model="gpt-4")  # doctest: +SKIP
                >>> # if await adapter.validate_connection():
                >>> #     print("API ready")
                >>> # else:
                >>> #     print("API unavailable")  # doctest: +SKIP
        
        Note:
            Async method—must be awaited. Should NOT raise exceptions—return
            False instead. Log errors via logging_system. Useful for pre-flight
            checks before batch processing.
        """
        pass
    
    def __repr__(self) -> str:
        """Return string representation of adapter for debugging and logging.
        
        Shows adapter class name, provider, model, and base_url in readable format.
        Used in log messages and REPL output.
        
        Returns:
            str: Formatted string "ClassName(provider=X, model=Y, base_url=Z)"
        
        Example:
            Display adapter info:
                >>> # adapter = OpenAIAdapter(  # doctest: +SKIP
                >>> #     api_key="sk-...",
                >>> #     model="gpt-4",
                >>> #     base_url="https://api.openai.com"
                >>> # )
                >>> # repr(adapter)  # doctest: +SKIP
                >>> # "OpenAIAdapter(provider=openai, model=gpt-4, base_url=https://api.openai.com)"
                >>> # print(adapter)  # doctest: +SKIP
                >>> # OpenAIAdapter(provider=openai, model=gpt-4, base_url=https://api.openai.com)
        
        Note:
            Doesn't include api_key (security). Shows None for base_url if not set.
            Inherited by all subclasses (no override needed).
        """
        return (
            f"{self.__class__.__name__}("
            f"provider={self.provider.value}, "
            f"model={self.model}, "
            f"base_url={self.base_url})"
        )
