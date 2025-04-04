"""Base classes and interfaces for MCP servers."""

import logging
import os
import subprocess
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar

import aiohttp

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MCPServerInterface(Protocol):
    """Base interface for MCP server interactions."""

    endpoint: str

    async def start(self) -> None:
        """Start the MCP server."""
        ...

    async def stop(self) -> None:
        """Stop the MCP server."""
        ...

    async def health_check(self) -> bool:
        """Check if the server is healthy and ready to accept requests."""
        ...


class BaseMCPServer:
    """Base class for all MCP servers."""

    def __init__(
        self,
        name: str,
        endpoint: str,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ):
        """Initialize a base MCP server.

        Args:
            name: Name of the MCP server
            endpoint: Server endpoint URL
            command: Command to start the server
            args: Command arguments
            env_vars: Environment variables for the server process
        """
        self.name = name
        self.endpoint = endpoint
        self.command = command
        self.args = args or []
        self.env_vars = env_vars or {}
        self.process: Optional[subprocess.Popen] = None

    async def start(self) -> None:
        """Start the MCP server process."""
        if self.command:
            try:
                # Prepare environment
                env = os.environ.copy()
                env.update(self.env_vars)

                # Build command
                cmd = [self.command] + self.args

                logger.info(f"Starting MCP server: {self.name}")

                self.process = subprocess.Popen(
                    cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )

                logger.info(f"Started {self.name} (PID: {self.process.pid})")
            except Exception as e:
                logger.error(f"Error starting {self.name}: {e}")
                raise

    async def stop(self) -> None:
        """Stop the MCP server process."""
        if self.process:
            try:
                logger.info(f"Stopping {self.name}")
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                logger.error(f"Error stopping {self.name}: {e}")
            finally:
                self.process = None

    async def health_check(self) -> bool:
        """Check if the server is healthy."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.endpoint}/health") as response:
                    return response.status == 200
        except Exception:
            return False
