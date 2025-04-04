"""MCP client implementation for Ollama-MCP Discord bot."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from ollama_mcp_discord.core.config import config
from ollama_mcp_discord.mcp.servers import (
    BaseMCPServer,
    FetchMCPServer,
    MemoryMCPServer,
    PuppeteerMCPServer,
    SequentialThinkingMCPServer,
)

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with MCP servers."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the MCP client.

        Args:
            config_path: Path to MCP server configuration JSON file
        """
        # Default server endpoints from configuration
        self.memory_endpoint = config.memory_server_endpoint
        self.fetch_endpoint = config.fetch_server_endpoint
        self.puppeteer_endpoint = config.puppeteer_server_endpoint
        self.sequential_thinking_endpoint = config.sequential_thinking_server_endpoint

        # Initialize MCP servers
        self.memory_server = MemoryMCPServer("memory", self.memory_endpoint)
        self.fetch_server = FetchMCPServer("fetch", self.fetch_endpoint)
        self.puppeteer_server = PuppeteerMCPServer("puppeteer", self.puppeteer_endpoint)
        self.sequential_thinking_server = SequentialThinkingMCPServer(
            "sequential-thinking", self.sequential_thinking_endpoint
        )

        # Dictionary of all servers
        self.servers: Dict[str, BaseMCPServer] = {
            "memory": self.memory_server,
            "fetch": self.fetch_server,
            "puppeteer": self.puppeteer_server,
            "sequential-thinking": self.sequential_thinking_server,
        }

        # Load server configuration
        self.mcp_servers = {}
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config_data = json.load(f)
                    self.mcp_servers = config_data.get("mcpServers", {})

                    # Update server configurations from config file
                    for server_name, server_config in self.mcp_servers.items():
                        if server_name in self.servers:
                            self.servers[server_name].command = server_config.get("command")
                            self.servers[server_name].args = server_config.get("args", [])
                            self.servers[server_name].env_vars = server_config.get("env", {})
            except Exception as e:
                logger.error(f"Error loading MCP configuration: {e}")

    async def start_servers(self):
        """Start all configured MCP servers."""
        for server in self.servers.values():
            if server.command:  # Only start servers with commands
                await server.start()

    async def stop_servers(self):
        """Stop all running MCP servers."""
        for server in self.servers.values():
            await server.stop()

    # Convenience methods that delegate to the appropriate server
    async def create_memory_entity(self, name: str, entity_type: str, observations: List[str]) -> Dict[str, Any]:
        """Create an entity in the memory server."""
        return await self.memory_server.create_memory_entity(name, entity_type, observations)

    async def retrieve_entity(self, name: str) -> Dict[str, Any]:
        """Retrieve an entity from the memory server."""
        return await self.memory_server.retrieve_entity(name)

    async def add_observation(self, name: str, observation: str) -> Dict[str, Any]:
        """Add an observation to an entity in the memory server."""
        return await self.memory_server.add_observation(name, observation)

    async def fetch_url(self, url: str, max_length: int = 5000) -> str:
        """Fetch content from a URL."""
        return await self.fetch_server.fetch_url(url, max_length)

    async def fetch_and_extract(self, url: str, query: str, max_length: int = 5000) -> str:
        """Fetch and extract information from a URL."""
        return await self.fetch_server.fetch_and_extract(url, query, max_length)

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL using Puppeteer."""
        return await self.puppeteer_server.navigate(url)

    async def click(self, selector: str) -> Dict[str, Any]:
        """Click on an element using Puppeteer."""
        return await self.puppeteer_server.click(selector)

    async def type(self, selector: str, text: str) -> Dict[str, Any]:
        """Type text into an element using Puppeteer."""
        return await self.puppeteer_server.type(selector, text)

    async def screenshot(self, selector: Optional[str] = None, full_page: bool = False) -> str:
        """Take a screenshot using Puppeteer."""
        return await self.puppeteer_server.screenshot(selector, full_page)

    async def think(
        self,
        thought: str,
        thought_number: int,
        total_thoughts: int,
        next_thought_needed: bool = True,
    ) -> Dict[str, Any]:
        """Execute a sequential thinking step."""
        return await self.sequential_thinking_server.think(thought, thought_number, total_thoughts, next_thought_needed)

    async def start_thinking(self, initial_thought: str, estimated_steps: int) -> Dict[str, Any]:
        """Start a sequential thinking process."""
        return await self.sequential_thinking_server.start_thinking(initial_thought, estimated_steps)

    async def conclude_thinking(self, final_thought: str, thought_number: int, total_thoughts: int) -> Dict[str, Any]:
        """Conclude a sequential thinking process."""
        return await self.sequential_thinking_server.conclude_thinking(final_thought, thought_number, total_thoughts)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_servers()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_servers()
