"""Client for interacting with Ollama API."""

import logging
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, host: str, model: str):
        """Initialize the Ollama client.

        Args:
            host: Base URL for the Ollama server
            model: Name of the model to use
        """
        self.host = host.rstrip("/")
        self.model = model
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """Ensure a client session is created."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

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

        await self._ensure_session()

        # Ensure session is not None (mypy can't infer this from _ensure_session)
        assert self.session is not None, "Client session must be initialized"

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
            url = f"{self.host}/api/generate"
            logger.debug(f"Sending request to {url} with model {self.model}")
            async with self.session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                logger.debug(f"Response status: {response.status}")
                return result.get("response", "")
        except aiohttp.ClientError as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models.

        Returns:
            List of available models
        """
        await self._ensure_session()

        # Ensure session is not None (mypy can't infer this from _ensure_session)
        assert self.session is not None, "Client session must be initialized"

        try:
            url = f"{self.host}/api/tags"
            logger.debug(f"Requesting models from {url}")
            async with self.session.get(url) as response:
                response.raise_for_status()
                result = await response.json()
                models = result.get("models", [])
                logger.debug(f"Retrieved {len(models)} models")
                return models
        except aiohttp.ClientError as e:
            logger.error(f"Error listing models: {e}")
            raise
