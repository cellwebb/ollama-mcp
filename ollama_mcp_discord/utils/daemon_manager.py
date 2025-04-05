"""Daemon process management for MCP servers.

This module implements daemon process management for MCP servers,
allowing them to run in the background with proper lifecycle management.
"""

import json
import logging
import os
import signal
import sys
import time
from contextlib import contextmanager
from typing import Dict, List, Optional

import daemon
from daemon import pidfile

from ollama_mcp_discord.core.settings import settings

logger = logging.getLogger(__name__)


class MCPServerDaemon:
    """Daemon process manager for MCP servers."""

    def __init__(
        self,
        server_name: str,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        working_dir: Optional[str] = None,
        pid_file: Optional[str] = None,
        log_file: Optional[str] = None,
    ):
        """Initialize the MCP server daemon.

        Args:
            server_name: Name of the MCP server
            command: Command to run
            args: Command line arguments
            env: Environment variables
            working_dir: Working directory for the daemon
            pid_file: Path to PID file
            log_file: Path to log file
        """
        self.server_name = server_name
        self.command = command
        self.args = args or []
        self.env = env or {}

        # Set up paths
        self.working_dir = working_dir or os.getcwd()
        self.pid_file = pid_file or os.path.join(settings.daemon_pid_dir, f"{server_name}.pid")
        self.log_file = log_file or os.path.join(settings.daemon_log_dir, f"{server_name}.log")

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.pid_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def start(self) -> bool:
        """Start the MCP server as a daemon.

        Returns:
            True if the daemon was started, False otherwise
        """
        if self.is_running():
            logger.warning(f"Server {self.server_name} is already running")
            return False

        try:
            # Prepare daemon context
            context = daemon.DaemonContext(
                working_directory=self.working_dir,
                umask=0o022,
                pidfile=pidfile.PIDLockFile(self.pid_file),
                detach_process=True,
            )

            # Set up stdin, stdout, stderr
            context.stdin = open(os.devnull, "r")
            context.stdout = open(self.log_file, "a+")
            context.stderr = open(self.log_file, "a+")

            # Set up signal handlers
            context.signal_map = {
                signal.SIGTERM: self._handle_sigterm,
                signal.SIGINT: self._handle_sigint,
                signal.SIGHUP: self._handle_sighup,
            }

            # Start the daemon
            with context:
                # Set environment variables
                for key, value in self.env.items():
                    os.environ[key] = value

                # Execute the command
                os.execvp(self.command, [self.command] + self.args)

            return True
        except Exception as e:
            logger.error(f"Error starting server {self.server_name}: {e}")
            return False

    def stop(self) -> bool:
        """Stop the MCP server daemon.

        Returns:
            True if the daemon was stopped, False otherwise
        """
        if not self.is_running():
            logger.warning(f"Server {self.server_name} is not running")
            return False

        try:
            # Read PID from file
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())

            # Send SIGTERM
            os.kill(pid, signal.SIGTERM)

            # Wait for process to terminate
            for _ in range(10):  # Wait up to 5 seconds
                if not self.is_running():
                    return True
                time.sleep(0.5)

            # If still running, send SIGKILL
            if self.is_running():
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)

            # Check if process has terminated
            if not self.is_running():
                return True

            logger.error(f"Failed to stop server {self.server_name}")
            return False
        except Exception as e:
            logger.error(f"Error stopping server {self.server_name}: {e}")
            return False

    def restart(self) -> bool:
        """Restart the MCP server daemon.

        Returns:
            True if the daemon was restarted, False otherwise
        """
        self.stop()
        return self.start()

    def is_running(self) -> bool:
        """Check if the MCP server daemon is running.

        Returns:
            True if the daemon is running, False otherwise
        """
        if not os.path.exists(self.pid_file):
            return False

        try:
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())

            # Check if process exists
            os.kill(pid, 0)
            return True
        except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
            # Process does not exist
            return False

    def get_status(self) -> Dict[str, str]:
        """Get the status of the MCP server daemon.

        Returns:
            A dictionary with status information
        """
        status = {
            "server_name": self.server_name,
            "running": str(self.is_running()),
            "pid_file": self.pid_file,
            "log_file": self.log_file,
            "command": self.command,
            "args": " ".join(self.args),
        }

        # Add PID if running
        if self.is_running():
            try:
                with open(self.pid_file, "r") as f:
                    pid = int(f.read().strip())
                status["pid"] = str(pid)
            except (FileNotFoundError, ValueError):
                status["pid"] = "unknown"

        return status

    def _handle_sigterm(self, signum, frame):
        """Handle SIGTERM signal."""
        logger.info(f"Server {self.server_name} received SIGTERM")
        sys.exit(0)

    def _handle_sigint(self, signum, frame):
        """Handle SIGINT signal."""
        logger.info(f"Server {self.server_name} received SIGINT")
        sys.exit(0)

    def _handle_sighup(self, signum, frame):
        """Handle SIGHUP signal."""
        logger.info(f"Server {self.server_name} received SIGHUP, reloading configuration")
        # In a real implementation, reload configuration here


class DaemonManager:
    """Manager for multiple MCP server daemons."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the daemon manager.

        Args:
            config_path: Path to daemon configuration file (JSON)
        """
        self.daemons: Dict[str, MCPServerDaemon] = {}

        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
        else:
            self._initialize_default_daemons()

    def _load_config(self, config_path: str):
        """Load daemon configuration from a JSON file.

        Args:
            config_path: Path to daemon configuration file
        """
        try:
            with open(config_path, "r") as f:
                config = json.load(f)

            for server_name, server_config in config.get("servers", {}).items():
                daemon = MCPServerDaemon(
                    server_name=server_name,
                    command=server_config.get("command"),
                    args=server_config.get("args", []),
                    env=server_config.get("env", {}),
                    working_dir=server_config.get("working_dir"),
                    pid_file=server_config.get("pid_file"),
                    log_file=server_config.get("log_file"),
                )
                self.daemons[server_name] = daemon

            logger.info(f"Loaded {len(self.daemons)} daemon configurations from {config_path}")
        except Exception as e:
            logger.error(f"Error loading daemon configuration: {e}")
            self._initialize_default_daemons()

    def _initialize_default_daemons(self):
        """Initialize default daemons from settings."""
        # Memory server
        if settings.memory_server_command:
            self.daemons["memory"] = MCPServerDaemon(
                server_name="memory",
                command=settings.memory_server_command,
                args=settings.memory_server_args,
                env=settings.memory_server_env,
            )

        # Fetch server
        if settings.fetch_server_command:
            self.daemons["fetch"] = MCPServerDaemon(
                server_name="fetch",
                command=settings.fetch_server_command,
                args=settings.fetch_server_args,
                env=settings.fetch_server_env,
            )

        # Puppeteer server
        if settings.puppeteer_server_command:
            self.daemons["puppeteer"] = MCPServerDaemon(
                server_name="puppeteer",
                command=settings.puppeteer_server_command,
                args=settings.puppeteer_server_args,
                env=settings.puppeteer_server_env,
            )

        # Sequential thinking server
        if settings.sequential_thinking_server_command:
            self.daemons["sequential_thinking"] = MCPServerDaemon(
                server_name="sequential_thinking",
                command=settings.sequential_thinking_server_command,
                args=settings.sequential_thinking_server_args,
                env=settings.sequential_thinking_server_env,
            )

        logger.info(f"Initialized {len(self.daemons)} default daemons")

    def start_daemon(self, server_name: str) -> bool:
        """Start a daemon.

        Args:
            server_name: Name of the daemon to start

        Returns:
            True if the daemon was started, False otherwise
        """
        if server_name not in self.daemons:
            logger.error(f"Daemon {server_name} not found")
            return False

        return self.daemons[server_name].start()

    def stop_daemon(self, server_name: str) -> bool:
        """Stop a daemon.

        Args:
            server_name: Name of the daemon to stop

        Returns:
            True if the daemon was stopped, False otherwise
        """
        if server_name not in self.daemons:
            logger.error(f"Daemon {server_name} not found")
            return False

        return self.daemons[server_name].stop()

    def restart_daemon(self, server_name: str) -> bool:
        """Restart a daemon.

        Args:
            server_name: Name of the daemon to restart

        Returns:
            True if the daemon was restarted, False otherwise
        """
        if server_name not in self.daemons:
            logger.error(f"Daemon {server_name} not found")
            return False

        return self.daemons[server_name].restart()

    def start_all(self) -> Dict[str, bool]:
        """Start all daemons.

        Returns:
            A dictionary mapping daemon names to success status
        """
        results = {}
        for name in self.daemons:
            results[name] = self.start_daemon(name)
        return results

    def stop_all(self) -> Dict[str, bool]:
        """Stop all daemons.

        Returns:
            A dictionary mapping daemon names to success status
        """
        results = {}
        for name in self.daemons:
            results[name] = self.stop_daemon(name)
        return results

    def restart_all(self) -> Dict[str, bool]:
        """Restart all daemons.

        Returns:
            A dictionary mapping daemon names to success status
        """
        results = {}
        for name in self.daemons:
            results[name] = self.restart_daemon(name)
        return results

    def get_status_all(self) -> Dict[str, Dict[str, str]]:
        """Get status of all daemons.

        Returns:
            A dictionary mapping daemon names to status dictionaries
        """
        results = {}
        for name, daemon in self.daemons.items():
            results[name] = daemon.get_status()
        return results


@contextmanager
def supervised_daemon(daemon_manager: DaemonManager, server_name: str):
    """Context manager for supervised daemon execution.

    Args:
        daemon_manager: The daemon manager
        server_name: Name of the daemon to supervise

    Yields:
        None
    """
    try:
        # Start the daemon
        success = daemon_manager.start_daemon(server_name)
        if not success:
            logger.error(f"Failed to start daemon {server_name}")

        yield
    finally:
        # Stop the daemon
        daemon_manager.stop_daemon(server_name)
