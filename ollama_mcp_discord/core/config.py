"""Configuration module for Ollama-MCP Discord bot."""

import json
import logging
import os
import pathlib
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""

    pass


class Configuration:
    """Configuration handler for Ollama-MCP Discord bot."""

    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration from environment variables.

        Args:
            env_file: Optional path to .env file
        """
        # Load environment variables from file if provided
        if env_file and os.path.exists(env_file):
            self._load_env_file(env_file)

        # Required environment variables
        self.discord_token = self._get_required_env("DISCORD_TOKEN")

        # MCP server configuration
        self.mcp_config_path = os.getenv("MCP_CONFIG_PATH", "mcp.json")

        # MCP server endpoints
        self.memory_server_endpoint = os.getenv("MEMORY_SERVER_ENDPOINT", "http://localhost:3100")
        self.fetch_server_endpoint = os.getenv("FETCH_SERVER_ENDPOINT", "http://localhost:3101")
        self.puppeteer_server_endpoint = os.getenv(
            "PUPPETEER_SERVER_ENDPOINT", "http://localhost:3102"
        )
        self.sequential_thinking_server_endpoint = os.getenv(
            "SEQUENTIAL_THINKING_SERVER_ENDPOINT", "http://localhost:3103"
        )

        # Ollama configuration
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")

        # Discord configuration
        self.command_prefix = os.getenv("COMMAND_PREFIX", "!")
        self.trigger_words = self._parse_list_env("TRIGGER_WORDS", ["@bot"])

        # MCP servers configuration from config file
        self.mcp_servers = self._load_mcp_config()

    def _get_required_env(self, name: str) -> str:
        """Get a required environment variable.

        Args:
            name: Environment variable name

        Returns:
            The environment variable value

        Raises:
            ConfigurationError: If the environment variable is not set
        """
        value = os.getenv(name)
        if not value:
            raise ConfigurationError(f"Required environment variable {name} not set")
        return value

    def _parse_list_env(self, name: str, default: List[str] = None) -> List[str]:
        """Parse a comma-separated list from an environment variable.

        Args:
            name: Environment variable name
            default: Default value if not set

        Returns:
            List of values
        """
        value = os.getenv(name)
        if not value:
            return default or []
        return [item.strip() for item in value.split(",")]

    def _load_env_file(self, env_file: str) -> None:
        """Load environment variables from a file.

        Args:
            env_file: Path to .env file
        """
        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip("'\"")
        except Exception as e:
            logger.warning(f"Error loading environment file {env_file}: {e}")

    def _load_mcp_config(self) -> Dict[str, Any]:
        """Load MCP server configuration from the config file.

        Returns:
            MCP server configuration dictionary
        """
        config_path = self.mcp_config_path

        # Resolve relative path
        if not os.path.isabs(config_path):
            # Check current directory
            if os.path.exists(config_path):
                config_path = os.path.abspath(config_path)
            else:
                # Check home directory
                home_config = os.path.join(pathlib.Path.home(), config_path)
                if os.path.exists(home_config):
                    config_path = home_config
                else:
                    logger.warning(
                        f"MCP configuration file not found at {config_path} " f"or {home_config}"
                    )
                    return {}

        # Load configuration
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                logger.info(f"Loaded MCP configuration from {config_path}")
                return config.get("mcpServers", {})
        except Exception as e:
            logger.error(f"Error loading MCP configuration: {e}")
            return {}

    def get_mcp_server_config(self, server_name: str) -> Dict[str, Any]:
        """Get configuration for a specific MCP server.

        Args:
            server_name: Name of the MCP server

        Returns:
            Server configuration dictionary
        """
        return self.mcp_servers.get(server_name, {})


# Global configuration instance
config = Configuration()
