"""Configuration module for Ollama-MCP Discord bot using Pydantic."""

import pathlib
from typing import Dict, List, Optional

from pydantic import AnyHttpUrl, BaseModel, BaseSettings, Field, root_validator


class MCPServerSettings(BaseModel):
    """Configuration for an MCP server."""

    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)


class Settings(BaseSettings):
    """Main configuration settings for the Ollama-MCP Discord bot."""

    # Discord settings
    discord_token: str = Field(..., description="Discord bot token")
    command_prefix: str = Field("!", description="Command prefix for Discord commands")
    trigger_words: List[str] = Field(default_factory=lambda: ["@bot"], description="Words that trigger the bot")

    # MCP config
    mcp_config_path: str = Field("mcp.json", description="Path to MCP server configuration file")
    memory_server_endpoint: AnyHttpUrl = Field("http://localhost:3100", description="Endpoint for memory MCP server")
    fetch_server_endpoint: AnyHttpUrl = Field("http://localhost:3101", description="Endpoint for fetch MCP server")
    puppeteer_server_endpoint: AnyHttpUrl = Field(
        "http://localhost:3102", description="Endpoint for puppeteer MCP server"
    )
    sequential_thinking_server_endpoint: AnyHttpUrl = Field(
        "http://localhost:3103", description="Endpoint for sequential thinking MCP server"
    )

    # Ollama settings
    ollama_host: AnyHttpUrl = Field("http://localhost:11434", description="Ollama server host")
    ollama_model: str = Field("llama3", description="Default Ollama model to use")

    # MCP servers config
    mcp_servers: Dict[str, MCPServerSettings] = Field(default_factory=dict)

    @root_validator(pre=True)
    def load_mcp_config(cls, values: Dict) -> Dict:
        """Load MCP server configuration from the config file.

        Args:
            values: The values dictionary from pydantic

        Returns:
            Updated values dictionary with mcp_servers loaded
        """
        import json
        import os

        config_path = values.get("mcp_config_path", "mcp.json")

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

        # Load configuration if the file exists
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    # Convert the raw dict to MCPServerSettings objects
                    mcp_servers = {}
                    for server_name, server_config in config.get("mcpServers", {}).items():
                        mcp_servers[server_name] = MCPServerSettings(**server_config)
                    values["mcp_servers"] = mcp_servers
            except Exception as e:
                import logging

                logging.getLogger(__name__).error(f"Error loading MCP configuration: {e}")

        return values

    class Config:
        """Pydantic config settings."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_mcp_server_config(server_name: str) -> MCPServerSettings:
    """Get configuration for a specific MCP server.

    Args:
        server_name: Name of the MCP server

    Returns:
        Server configuration
    """
    return settings.mcp_servers.get(server_name, MCPServerSettings())
