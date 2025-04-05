"""MCP SDK client integration.

This module provides a wrapper around the official MCP SDK,
creating a standardized interface for the Ollama-MCP Discord bot.
"""

import logging
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

from ollama_mcp_discord.core.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ServerInfo:
    """Information about an MCP server."""

    name: str
    command: str
    args: List[str]
    env: Dict[str, str]


class MCPSDKClient:
    """Client for interacting with MCP servers using the official MCP SDK."""

    def __init__(self):
        """Initialize the MCP SDK client."""
        self.servers: Dict[str, ServerInfo] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stacks: Dict[str, AsyncExitStack] = {}
        self.stdio_clients: Dict[str, Tuple[Any, Any]] = {}  # (read, write)

        # Initialize server configurations
        self._initialize_servers()

    def _initialize_servers(self):
        """Initialize server configurations from settings."""
        # Memory server
        if settings.memory_server_command:
            self.servers["memory"] = ServerInfo(
                name="memory",
                command=settings.memory_server_command,
                args=settings.memory_server_args,
                env=settings.memory_server_env or {},
            )

        # Fetch server
        if settings.fetch_server_command:
            self.servers["fetch"] = ServerInfo(
                name="fetch",
                command=settings.fetch_server_command,
                args=settings.fetch_server_args,
                env=settings.fetch_server_env or {},
            )

        # Puppeteer server
        if settings.puppeteer_server_command:
            self.servers["puppeteer"] = ServerInfo(
                name="puppeteer",
                command=settings.puppeteer_server_command,
                args=settings.puppeteer_server_args,
                env=settings.puppeteer_server_env or {},
            )

        # Sequential thinking server
        if settings.sequential_thinking_server_command:
            self.servers["sequential_thinking"] = ServerInfo(
                name="sequential_thinking",
                command=settings.sequential_thinking_server_command,
                args=settings.sequential_thinking_server_args,
                env=settings.sequential_thinking_server_env or {},
            )

    async def start_server(self, server_name: str) -> Optional[ClientSession]:
        """Start an MCP server and create a session.

        Args:
            server_name: The name of the server to start

        Returns:
            The client session for the server, or None if the server couldn't be started
        """
        if server_name not in self.servers:
            logger.error(f"Server {server_name} not found in configuration")
            return None

        try:
            server_info = self.servers[server_name]

            # Create server parameters
            server_params = StdioServerParameters(
                command=server_info.command,
                args=server_info.args,
                env=server_info.env,
            )

            # Set up exit stack for resource management
            exit_stack = AsyncExitStack()
            self.exit_stacks[server_name] = exit_stack

            # Create stdio client
            read, write = await exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio_clients[server_name] = (read, write)

            # Create client session
            session = await exit_stack.enter_async_context(ClientSession(read, write))

            # Initialize the session
            await session.initialize()

            # Store the session
            self.sessions[server_name] = session

            logger.info(f"Started MCP server: {server_name}")
            return session

        except Exception as e:
            logger.error(f"Error starting server {server_name}: {e}")
            # Clean up resources in case of error
            if server_name in self.exit_stacks:
                await self.exit_stacks[server_name].aclose()
                del self.exit_stacks[server_name]
            return None

    async def stop_server(self, server_name: str) -> None:
        """Stop an MCP server.

        Args:
            server_name: The name of the server to stop
        """
        if server_name in self.exit_stacks:
            try:
                await self.exit_stacks[server_name].aclose()
                logger.info(f"Stopped MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Error stopping server {server_name}: {e}")
            finally:
                # Clean up resources
                if server_name in self.sessions:
                    del self.sessions[server_name]
                if server_name in self.stdio_clients:
                    del self.stdio_clients[server_name]
                del self.exit_stacks[server_name]

    async def start_all_servers(self) -> None:
        """Start all configured MCP servers."""
        for server_name in self.servers:
            await self.start_server(server_name)

    async def stop_all_servers(self) -> None:
        """Stop all running MCP servers."""
        for server_name in list(self.exit_stacks.keys()):
            await self.stop_server(server_name)

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on an MCP server.

        Args:
            server_name: The name of the server
            tool_name: The name of the tool to call
            arguments: The arguments to pass to the tool

        Returns:
            The result of the tool call

        Raises:
            ValueError: If the server is not running or the tool is not found
        """
        if server_name not in self.sessions:
            # Try to start the server
            session = await self.start_server(server_name)
            if not session:
                raise ValueError(f"Server {server_name} is not running")
        else:
            session = self.sessions[server_name]

        try:
            # Call the tool
            result = await session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on server {server_name}: {e}")
            raise

    async def read_resource(self, server_name: str, resource_path: str) -> Tuple[str, str]:
        """Read a resource from an MCP server.

        Args:
            server_name: The name of the server
            resource_path: The path of the resource to read

        Returns:
            A tuple of (content, mime_type)

        Raises:
            ValueError: If the server is not running or the resource is not found
        """
        if server_name not in self.sessions:
            # Try to start the server
            session = await self.start_server(server_name)
            if not session:
                raise ValueError(f"Server {server_name} is not running")
        else:
            session = self.sessions[server_name]

        try:
            # Read the resource
            content, mime_type = await session.read_resource(resource_path)
            return content, mime_type
        except Exception as e:
            logger.error(f"Error reading resource {resource_path} from server {server_name}: {e}")
            raise

    async def list_tools(self, server_name: str) -> List[types.Tool]:
        """List tools available on an MCP server.

        Args:
            server_name: The name of the server

        Returns:
            A list of available tools

        Raises:
            ValueError: If the server is not running
        """
        if server_name not in self.sessions:
            # Try to start the server
            session = await self.start_server(server_name)
            if not session:
                raise ValueError(f"Server {server_name} is not running")
        else:
            session = self.sessions[server_name]

        try:
            # List tools
            tools = await session.list_tools()
            return tools
        except Exception as e:
            logger.error(f"Error listing tools on server {server_name}: {e}")
            raise

    async def list_resources(self, server_name: str) -> List[types.Resource]:
        """List resources available on an MCP server.

        Args:
            server_name: The name of the server

        Returns:
            A list of available resources

        Raises:
            ValueError: If the server is not running
        """
        if server_name not in self.sessions:
            # Try to start the server
            session = await self.start_server(server_name)
            if not session:
                raise ValueError(f"Server {server_name} is not running")
        else:
            session = self.sessions[server_name]

        try:
            # List resources
            resources = await session.list_resources()
            return resources
        except Exception as e:
            logger.error(f"Error listing resources on server {server_name}: {e}")
            raise

    # Convenience methods for specific MCP servers

    async def fetch_url(self, url: str, max_length: int = 5000) -> str:
        """Fetch content from a URL using the fetch server.

        Args:
            url: The URL to fetch
            max_length: Maximum content length to return

        Returns:
            The fetched content
        """
        try:
            result = await self.call_tool("fetch", "fetch", {"url": url, "max_length": max_length})
            return result
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            raise

    async def sequential_thinking(self, thought_params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform sequential thinking using the sequential thinking server.

        Args:
            thought_params: Parameters for the thinking process
                - thought: Current thinking step
                - thoughtNumber: Current thought number
                - totalThoughts: Estimated total thoughts
                - nextThoughtNeeded: Whether another thought is needed

        Returns:
            The result of the thinking process
        """
        try:
            result = await self.call_tool("sequential_thinking", "sequentialthinking", thought_params)
            return result
        except Exception as e:
            logger.error(f"Error in sequential thinking: {e}")
            raise

    async def create_memory_entity(self, name: str, entity_type: str, observations: List[str]) -> Dict[str, Any]:
        """Create a memory entity using the memory server.

        Args:
            name: The name of the entity
            entity_type: The type of the entity
            observations: Initial observations about the entity

        Returns:
            The created entity
        """
        try:
            result = await self.call_tool(
                "memory",
                "create_memory_entity",
                {"name": name, "entity_type": entity_type, "observations": observations},
            )
            return result
        except Exception as e:
            logger.error(f"Error creating memory entity {name}: {e}")
            raise

    async def retrieve_entity(self, name: str) -> Dict[str, Any]:
        """Retrieve a memory entity using the memory server.

        Args:
            name: The name of the entity to retrieve

        Returns:
            The retrieved entity
        """
        try:
            result = await self.call_tool("memory", "retrieve_entity", {"name": name})
            return result
        except Exception as e:
            logger.error(f"Error retrieving entity {name}: {e}")
            raise

    async def add_observation(self, name: str, observation: str) -> Dict[str, Any]:
        """Add an observation to a memory entity.

        Args:
            name: The name of the entity
            observation: The observation to add

        Returns:
            The updated entity
        """
        try:
            result = await self.call_tool("memory", "add_observation", {"name": name, "observation": observation})
            return result
        except Exception as e:
            logger.error(f"Error adding observation to entity {name}: {e}")
            raise

    # Context manager methods

    async def __aenter__(self):
        """Start all servers when entering context."""
        await self.start_all_servers()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stop all servers when exiting context."""
        await self.stop_all_servers()
