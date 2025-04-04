"""Fetch MCP server implementation."""

import logging
from typing import Any, Dict, Optional

import aiohttp

from ollama_mcp_discord.mcp.servers.base import BaseMCPServer

logger = logging.getLogger(__name__)


class FetchMCPServer(BaseMCPServer):
    """Fetch MCP server for retrieving content from URLs."""

    async def fetch_url(
        self, url: str, max_length: int = 5000, raw: bool = False, start_index: int = 0
    ) -> str:
        """Fetch content from a URL.

        Args:
            url: URL to fetch
            max_length: Maximum content length to return
            raw: Whether to return raw HTML instead of simplified content
            start_index: Index to start returning content from

        Returns:
            Content from the URL
        """
        payload = {"url": url, "max_length": max_length, "raw": raw, "start_index": start_index}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/mcp_fetch_fetch", json=payload
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result.get("content", "")
        except Exception as e:
            logger.error(f"Error fetching URL: {e}")
            raise

    async def fetch_and_extract(self, url: str, query: str, max_length: int = 5000) -> str:
        """Fetch content from a URL and extract relevant information.

        Args:
            url: URL to fetch
            query: Query to extract information for
            max_length: Maximum content length to return

        Returns:
            Extracted content from the URL
        """
        payload = {"url": url, "query": query, "max_length": max_length}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/mcp_fetch_extract", json=payload
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result.get("content", "")
        except Exception as e:
            logger.error(f"Error extracting from URL: {e}")
            raise
