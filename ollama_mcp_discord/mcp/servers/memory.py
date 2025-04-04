"""Memory MCP server implementation."""

import logging
from typing import Any, Dict, List

import aiohttp

from ollama_mcp_discord.mcp.servers.base import BaseMCPServer

logger = logging.getLogger(__name__)


class MemoryMCPServer(BaseMCPServer):
    """Memory MCP server for managing entity memories."""

    async def create_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create entities in the memory server.

        Args:
            entities: List of entity objects to create

        Returns:
            Response from the memory server
        """
        payload = {"entities": entities}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.endpoint}/mcp_memory_create_entities", json=payload) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Error creating memory entities: {e}")
            raise

    async def create_memory_entity(self, name: str, entity_type: str, observations: List[str]) -> Dict[str, Any]:
        """Create a single entity in the memory server.

        Args:
            name: Entity name
            entity_type: Type of entity
            observations: List of observations about the entity

        Returns:
            Response from the memory server
        """
        return await self.create_entities([{"name": name, "entityType": entity_type, "observations": observations}])

    async def retrieve_entity(self, name: str) -> Dict[str, Any]:
        """Retrieve an entity from the memory server.

        Args:
            name: Name of the entity to retrieve

        Returns:
            Entity data
        """
        payload = {"name": name}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.endpoint}/mcp_memory_retrieve_entity", json=payload) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Error retrieving entity: {e}")
            raise

    async def add_observation(self, name: str, observation: str) -> Dict[str, Any]:
        """Add an observation to an existing entity.

        Args:
            name: Name of the entity
            observation: Observation to add

        Returns:
            Updated entity data
        """
        payload = {"name": name, "observation": observation}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.endpoint}/mcp_memory_add_observation", json=payload) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Error adding observation: {e}")
            raise
