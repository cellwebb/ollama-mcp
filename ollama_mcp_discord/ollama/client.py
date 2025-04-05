"""Client for interacting with Ollama API."""

import logging
from typing import Any, Dict, List, Optional

from ollama_mcp_discord.core.settings import settings
from ollama_mcp_discord.utils.http import create_client

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        """Initialize the Ollama client.

        Args:
            host: Base URL for the Ollama server (defaults to settings.ollama_host)
            model: Name of the model to use (defaults to settings.ollama_model)
        """
        self.host = host or str(settings.ollama_host)
        self.model = model or settings.ollama_model
        self.http_client = create_client(base_url=self.host, timeout=120.0)

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        context: Optional[List[Any]] = None,
    ) -> str:
        """Generate a response from the Ollama model.

        Args:
            prompt: Input prompt
            system: Optional system message
            context: Optional context for conversation

        Returns:
            Generated response

        Raises:
            ValueError: If prompt is empty
        """
        if not prompt or prompt.strip() == "":
            raise ValueError("Prompt cannot be empty")

        # Super simplified payload - only the essentials
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        # Only add system if it's provided
        if system:
            payload["system"] = system

        # Only add context if it's provided
        if context:
            payload["context"] = context

        try:
            logger.debug(f"Sending request to Ollama with model {self.model}")
            result = await self.http_client.post("/api/generate", json=payload)
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models.

        Returns:
            List of available models
        """
        try:
            logger.debug("Requesting models from Ollama")
            result = await self.http_client.get("/api/tags")
            models = result.get("models", [])
            logger.debug(f"Retrieved {len(models)} models")
            return models
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            raise

    async def close(self):
        """Close the client session."""
        await self.http_client.close()

    async def __aenter__(self):
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.close()
