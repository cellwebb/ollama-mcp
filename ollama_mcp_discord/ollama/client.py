"""Client for interacting with Ollama API."""

import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with the Ollama API."""

    def __init__(self, host: str, model: str):
        """Initialize the Ollama client.

        Args:
            host: The Ollama API host URL
            model: The default model to use
        """
        self.host = host.rstrip("/")
        self.model = model
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        context: Optional[List[Any]] = None,
    ) -> str:
        """Generate a response from the model.

        Args:
            prompt: The prompt text
            system: Optional system prompt
            context: Optional conversation context

        Returns:
            The generated text
        """
        await self._ensure_session()

        payload = {"model": self.model, "prompt": prompt, "stream": False}

        if system:
            payload["system"] = system

        if context:
            payload["context"] = context

        try:
            url = f"{self.host}/api/generate"
            async with self.session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()
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

        try:
            url = f"{self.host}/api/tags"
            async with self.session.get(url) as response:
                response.raise_for_status()
                result = await response.json()
                return result.get("models", [])
        except aiohttp.ClientError as e:
            logger.error(f"Error listing models: {e}")
            raise
