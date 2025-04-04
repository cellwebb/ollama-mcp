"""Client for interacting with MCP servers."""

import asyncio
import json
import logging
import os
import signal
import subprocess
from typing import Any, Dict, List, Optional, Union

import aiohttp

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with MCP servers."""

    def __init__(self, config_path: str = None):
        """Initialize the MCP client.

        Args:
            config_path: Path to MCP server configuration JSON file
        """
        # Default MCP server endpoints
        self.memory_endpoint = "http://localhost:3100"
        self.fetch_endpoint = "http://localhost:3101"
        self.puppeteer_endpoint = "http://localhost:3102"
        self.sequential_thinking_endpoint = "http://localhost:3103"

        # Load server configuration if provided
        self.mcp_servers = {}
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    self.mcp_servers = config.get("mcpServers", {})
                    logger.info(f"Loaded MCP server configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading MCP configuration: {e}")

        # Server processes
        self.server_processes: Dict[str, subprocess.Popen] = {}

        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def start_servers(self):
        """Start MCP servers based on configuration."""
        for server_name, server_config in self.mcp_servers.items():
            try:
                command = server_config.get("command")
                args = server_config.get("args", [])
                env_vars = server_config.get("env", {})

                # Prepare environment
                env = os.environ.copy()
                env.update(env_vars)

                # Build command
                cmd = [command] + args

                logger.info(
                    f"Starting MCP server: {server_name} with command: {' '.join(cmd)}"
                )

                # Start the process
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                self.server_processes[server_name] = process
                logger.info(f"Started MCP server: {server_name} (PID: {process.pid})")

            except Exception as e:
                logger.error(f"Error starting MCP server {server_name}: {e}")

    async def stop_servers(self):
        """Stop all running MCP servers."""
        for server_name, process in self.server_processes.items():
            try:
                logger.info(f"Stopping MCP server: {server_name} (PID: {process.pid})")

                # Try to terminate gracefully first
                process.terminate()

                # Wait for a short timeout
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(
                        f"Server {server_name} did not terminate gracefully, forcing kill"
                    )
                    process.kill()

                logger.info(f"Stopped MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Error stopping MCP server {server_name}: {e}")

        # Clear process dictionary
        self.server_processes.clear()

        # Close HTTP session if open
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        """Start servers and session when used as async context manager."""
        await self.start_servers()
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stop servers and session when exiting async context manager."""
        await self.stop_servers()

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
