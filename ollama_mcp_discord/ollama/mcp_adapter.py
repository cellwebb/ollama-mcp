"""MCP adapter for Ollama integration.

This module provides a FastMCP server that wraps the Ollama API,
exposing it as MCP resources and tools.
"""

import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from ollama_mcp_discord.core.settings import settings
from ollama_mcp_discord.ollama.client import OllamaClient

logger = logging.getLogger(__name__)


class OllamaMCPAdapter:
    """Adapter that exposes Ollama as an MCP server."""

    def __init__(self, host: Optional[str] = None):
        """Initialize the Ollama MCP adapter.

        Args:
            host: Base URL for the Ollama server (defaults to settings.ollama_host)
        """
        self.host = host or str(settings.ollama_host)
        self.ollama_client = OllamaClient(host=self.host)

        # Create FastMCP server
        self.mcp = FastMCP("Ollama")

        # Register resources and tools
        self._register_resources()
        self._register_tools()

    def _register_resources(self):
        """Register resources for the MCP server."""

        @self.mcp.resource("ollama://models")
        async def list_models_resource() -> str:
            """List available Ollama models."""
            try:
                models = await self.ollama_client.list_models()
                model_names = [model.get("name", "unknown") for model in models]
                return f"Available models: {', '.join(model_names)}"
            except Exception as e:
                logger.error(f"Error listing models: {e}")
                return f"Error listing models: {str(e)}"

        @self.mcp.resource("ollama://models/{model}")
        async def get_model_info(model: str) -> str:
            """Get information about a specific model."""
            try:
                models = await self.ollama_client.list_models()
                for m in models:
                    if m.get("name") == model:
                        return (
                            f"Model: {m.get('name')}\n"
                            f"Modified: {m.get('modified')}\n"
                            f"Size: {m.get('size')}\n"
                            f"Digest: {m.get('digest')}\n"
                            f"Details: {m.get('details', {})}"
                        )
                return f"Model '{model}' not found"
            except Exception as e:
                logger.error(f"Error getting model info: {e}")
                return f"Error getting model info: {str(e)}"

    def _register_tools(self):
        """Register tools for the MCP server."""

        @self.mcp.tool()
        async def generate(prompt: str, system: Optional[str] = None, model: Optional[str] = None) -> str:
            """Generate a response from an Ollama model.

            Args:
                prompt: Input prompt text
                system: Optional system message to guide the model
                model: Optional model name to use (defaults to server configuration)

            Returns:
                Generated text response
            """
            try:
                model_name = model or settings.ollama_model
                client = OllamaClient(model=model_name)

                response = await client.generate(prompt=prompt, system=system)
                return response
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                return f"Error generating response: {str(e)}"
            finally:
                await client.close()

        @self.mcp.tool()
        async def list_models() -> List[Dict[str, Any]]:
            """List all available Ollama models.

            Returns:
                List of model information dictionaries
            """
            try:
                models = await self.ollama_client.list_models()
                return models
            except Exception as e:
                logger.error(f"Error listing models: {e}")
                return []

    async def run(self):
        """Run the MCP server."""
        self.mcp.run()

    async def close(self):
        """Close the Ollama client."""
        await self.ollama_client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
