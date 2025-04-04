"""Client for interacting with MCP servers."""

import asyncio
import json
import logging
import os
import signal
import subprocess
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with MCP servers."""

    def __init__(self):
        """Initialize the MCP client."""
        # MCP server endpoints defined in mcp.json
        self.memory_endpoint = "http://localhost:3100"
        self.fetch_endpoint = "http://localhost:3101"
        self.puppeteer_endpoint = "http://localhost:3102"
        self.sequential_thinking_endpoint = "http://localhost:3103"

        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def create_memory_entity(
        self, name: str, entity_type: str, observations: List[str]
    ) -> Dict[str, Any]:
        """Create an entity in the memory server.

        Args:
            name: Entity name
            entity_type: Type of entity
            observations: List of observations

        Returns:
            The created entity
        """
        await self._ensure_session()

        payload = {
            "entities": [
                {"name": name, "entityType": entity_type, "observations": observations}
            ]
        }

        try:
            url = f"{self.memory_endpoint}/mcp_memory_create_entities"
            async with self.session.post(url, json=payload) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Error creating memory entity: {e}")
            raise

    async def create_memory_relation(
        self, from_entity: str, to_entity: str, relation_type: str
    ) -> Dict[str, Any]:
        """Create a relation between entities in memory.

        Args:
            from_entity: Source entity name
            to_entity: Target entity name
            relation_type: Type of relation

        Returns:
            The created relation
        """
        await self._ensure_session()

        payload = {
            "relations": [
                {"from": from_entity, "to": to_entity, "relationType": relation_type}
            ]
        }

        try:
            url = f"{self.memory_endpoint}/mcp_memory_create_relations"
            async with self.session.post(url, json=payload) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Error creating memory relation: {e}")
            raise

    async def fetch_url(self, url: str, max_length: int = 5000) -> str:
        """Fetch content from a URL.

        Args:
            url: The URL to fetch
            max_length: Maximum length of content to return

        Returns:
            The fetched content
        """
        await self._ensure_session()

        payload = {"url": url, "max_length": max_length}

        try:
            endpoint = f"{self.fetch_endpoint}/mcp_fetch_fetch"
            async with self.session.post(endpoint, json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                return result.get("content", "")
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching URL: {e}")
            raise

    async def sequential_thinking(
        self, thought: str, thought_number: int = 1, total_thoughts: int = 5
    ) -> Dict[str, Any]:
        """Use sequential thinking to break down complex problems.

        Args:
            thought: The current thought
            thought_number: Current thought number
            total_thoughts: Estimated total thoughts

        Returns:
            Result of the sequential thinking process
        """
        await self._ensure_session()

        payload = {
            "thought": thought,
            "thoughtNumber": thought_number,
            "totalThoughts": total_thoughts,
            "nextThoughtNeeded": True,
        }

        try:
            endpoint = f"{self.sequential_thinking_endpoint}/mcp_sequential_thinking_sequentialthinking"
            async with self.session.post(endpoint, json=payload) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Error using sequential thinking: {e}")
            raise
