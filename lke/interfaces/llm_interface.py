"""
Abstract interface for Large Language Model interactions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import os
import json
import subprocess
import time
from dataclasses import dataclass
import hashlib


@dataclass
class LLMResponse:
    """Standard response from LLM."""
    text: str
    metadata: Dict[str, Any] = None
    cached: bool = False

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LLMInterface(ABC):
    """
    Abstract interface to a language model.

    Implementations may call:
    - a local CLI binary (e.g. via subprocess),
    - a remote HTTP API,
    - a local Python model in process.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize LLM interface with optional caching."""
        self.cache_dir = cache_dir
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate that the LLM is accessible."""
        pass

    def _get_cache_key(self, prompt: str, **kwargs) -> str:
        """Generate cache key for a prompt."""
        cache_data = f"{prompt}{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.sha256(cache_data.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[LLMResponse]:
        """Retrieve cached response if available."""
        if not self.cache_dir:
            return None

        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                data = json.load(f)
                return LLMResponse(
                    text=data['text'],
                    metadata=data.get('metadata', {}),
                    cached=True
                )
        return None

    def _cache_response(self, cache_key: str, response: LLMResponse):
        """Cache a response."""
        if not self.cache_dir:
            return

        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        with open(cache_file, 'w') as f:
            json.dump({
                'text': response.text,
                'metadata': response.metadata
            }, f)


class ClaudeCLIInterface(LLMInterface):
    """Interface to Claude via command-line tool."""

    def __init__(self, cache_dir: Optional[str] = None,
                 model: str = "claude-3-opus-20240229",
                 max_tokens: int = 4000):
        """
        Initialize Claude CLI interface.

        Args:
            cache_dir: Directory for caching responses
            model: Model identifier
            max_tokens: Maximum tokens in response
        """
        super().__init__(cache_dir)
        self.model = model
        self.max_tokens = max_tokens

    def validate_connection(self) -> bool:
        """Check if Claude CLI is available."""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Claude CLI."""
        # Check cache first
        cache_key = self._get_cache_key(prompt, **kwargs)
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return cached_response

        # Prepare command
        cmd = ["claude"]

        # Add optional parameters
        if kwargs.get("temperature"):
            cmd.extend(["--temperature", str(kwargs["temperature"])])
        if kwargs.get("max_tokens", self.max_tokens):
            cmd.extend(["--max-tokens", str(kwargs.get("max_tokens", self.max_tokens))])

        # Add the prompt
        cmd.append(prompt)

        try:
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=kwargs.get("timeout", 60)
            )

            if result.returncode != 0:
                raise RuntimeError(f"Claude CLI error: {result.stderr}")

            response = LLMResponse(
                text=result.stdout.strip(),
                metadata={
                    "model": self.model,
                    "timestamp": time.time()
                }
            )

            # Cache the response
            self._cache_response(cache_key, response)

            return response

        except subprocess.TimeoutExpired:
            raise TimeoutError("Claude CLI request timed out")
        except Exception as e:
            raise RuntimeError(f"Failed to execute Claude CLI: {e}")


class ClaudeAPIInterface(LLMInterface):
    """Interface to Claude via Anthropic API."""

    def __init__(self, api_key: str, cache_dir: Optional[str] = None,
                 model: str = "claude-3-opus-20240229",
                 max_tokens: int = 4000):
        """
        Initialize Claude API interface.

        Args:
            api_key: Anthropic API key
            cache_dir: Directory for caching responses
            model: Model identifier
            max_tokens: Maximum tokens in response
        """
        super().__init__(cache_dir)
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens

        # Import anthropic library if available
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic library not installed. Run: pip install anthropic")

    def validate_connection(self) -> bool:
        """Validate API key and connection."""
        try:
            # Try a minimal API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception:
            return False

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Claude API."""
        # Check cache first
        cache_key = self._get_cache_key(prompt, **kwargs)
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return cached_response

        try:
            # Create message
            response = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", 0.7),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract text from response
            text = response.content[0].text if response.content else ""

            llm_response = LLMResponse(
                text=text,
                metadata={
                    "model": self.model,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens
                    } if hasattr(response, 'usage') else {},
                    "timestamp": time.time()
                }
            )

            # Cache the response
            self._cache_response(cache_key, llm_response)

            return llm_response

        except Exception as e:
            raise RuntimeError(f"Claude API error: {e}")


class OpenAIInterface(LLMInterface):
    """Interface to OpenAI GPT models."""

    def __init__(self, api_key: str, cache_dir: Optional[str] = None,
                 model: str = "gpt-4",
                 max_tokens: int = 4000):
        """
        Initialize OpenAI interface.

        Args:
            api_key: OpenAI API key
            cache_dir: Directory for caching responses
            model: Model identifier
            max_tokens: Maximum tokens in response
        """
        super().__init__(cache_dir)
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens

        # Import openai library if available
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai library not installed. Run: pip install openai")

    def validate_connection(self) -> bool:
        """Validate API key and connection."""
        try:
            # Try to list models
            self.client.models.list()
            return True
        except Exception:
            return False

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using OpenAI API."""
        # Check cache first
        cache_key = self._get_cache_key(prompt, **kwargs)
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return cached_response

        try:
            # Create chat completion
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", 0.7)
            )

            # Extract text
            text = response.choices[0].message.content

            llm_response = LLMResponse(
                text=text,
                metadata={
                    "model": self.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    } if response.usage else {},
                    "timestamp": time.time()
                }
            )

            # Cache the response
            self._cache_response(cache_key, llm_response)

            return llm_response

        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")


class OllamaInterface(LLMInterface):
    """Interface to Ollama for local model execution."""

    def __init__(self, cache_dir: Optional[str] = None,
                 model: str = "llama2",
                 host: str = "http://localhost:11434",
                 timeout: int = 120):
        """
        Initialize Ollama interface.

        Args:
            cache_dir: Directory for caching responses
            model: Model name (e.g., 'llama2', 'mistral', 'codellama')
            host: Ollama API host URL
            timeout: Request timeout in seconds
        """
        super().__init__(cache_dir)
        self.model = model
        self.host = host.rstrip('/')
        self.timeout = timeout

        # Import requests library if available
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("requests library not installed. Run: pip install requests")

    def validate_connection(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            # Check if Ollama is running
            response = self.requests.get(
                f"{self.host}/api/tags",
                timeout=5
            )
            if response.status_code != 200:
                return False

            # Check if the specified model is available
            models = response.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]
            return self.model in model_names

        except Exception:
            return False

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Ollama."""
        # Check cache first
        cache_key = self._get_cache_key(prompt, **kwargs)
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return cached_response

        try:
            # Prepare request
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 4000),
                    "top_p": kwargs.get("top_p", 0.9),
                    "seed": kwargs.get("seed")
                }
            }

            # Make API call
            response = self.requests.post(
                f"{self.host}/api/generate",
                json=data,
                timeout=kwargs.get("timeout", self.timeout)
            )

            if response.status_code != 200:
                raise RuntimeError(f"Ollama API error: {response.text}")

            result = response.json()

            llm_response = LLMResponse(
                text=result.get("response", ""),
                metadata={
                    "model": self.model,
                    "total_duration": result.get("total_duration"),
                    "load_duration": result.get("load_duration"),
                    "eval_count": result.get("eval_count"),
                    "eval_duration": result.get("eval_duration"),
                    "timestamp": time.time()
                }
            )

            # Cache the response
            self._cache_response(cache_key, llm_response)

            return llm_response

        except self.requests.exceptions.Timeout:
            raise TimeoutError(f"Ollama request timed out after {self.timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}")

    def list_models(self) -> List[str]:
        """List available models in Ollama."""
        try:
            response = self.requests.get(
                f"{self.host}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m.get("name", "") for m in models]
        except Exception:
            pass
        return []

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            response = self.requests.post(
                f"{self.host}/api/pull",
                json={"name": model_name},
                timeout=600  # Model downloads can take time
            )
            return response.status_code == 200
        except Exception:
            return False


class MockLLMInterface(LLMInterface):
    """Mock LLM interface for testing."""

    def __init__(self, responses: Optional[Dict[str, str]] = None,
                 cache_dir: Optional[str] = None):
        """
        Initialize mock interface.

        Args:
            responses: Dictionary mapping prompts to responses
            cache_dir: Directory for caching responses
        """
        super().__init__(cache_dir)
        self.responses = responses or {}
        self.default_response = "This is a mock response."

    def validate_connection(self) -> bool:
        """Always valid for mock interface."""
        return True

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate mock response."""
        # Check for predefined response
        for key, response in self.responses.items():
            if key in prompt:
                return LLMResponse(
                    text=response,
                    metadata={"mock": True, "timestamp": time.time()}
                )

        # Return default response
        return LLMResponse(
            text=self.default_response,
            metadata={"mock": True, "timestamp": time.time()}
        )


def create_llm_interface(provider: str, **kwargs) -> LLMInterface:
    """
    Factory function to create appropriate LLM interface.

    Args:
        provider: One of 'claude-cli', 'claude-api', 'openai', 'ollama', 'mock'
        **kwargs: Provider-specific arguments

    Returns:
        LLMInterface instance
    """
    if provider == "claude-cli":
        return ClaudeCLIInterface(**kwargs)
    elif provider == "claude-api":
        if "api_key" not in kwargs:
            raise ValueError("API key required for Claude API")
        return ClaudeAPIInterface(**kwargs)
    elif provider == "openai":
        if "api_key" not in kwargs:
            raise ValueError("API key required for OpenAI")
        return OpenAIInterface(**kwargs)
    elif provider == "ollama":
        return OllamaInterface(**kwargs)
    elif provider == "mock":
        return MockLLMInterface(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")