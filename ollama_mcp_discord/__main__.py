"""Main entry point for the Ollama-MCP Discord Bot."""

import asyncio
import logging
import os
import pathlib

import dotenv

from ollama_mcp_discord.discord.bot import create_bot
from ollama_mcp_discord.mcp.client import MCPClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Run the main application."""
    # Load environment variables
    dotenv.load_dotenv()

    # Validate required environment variables
    if not os.getenv("DISCORD_TOKEN"):
        logger.error("DISCORD_TOKEN environment variable is required")
        return

    # Determine configuration path
    config_path = os.getenv("MCP_CONFIG_PATH", "mcp.json")
    if not os.path.isabs(config_path):
        # If relative path, look in the current directory and home directory
        if os.path.exists(config_path):
            config_path = os.path.abspath(config_path)
        else:
            home_config = os.path.join(pathlib.Path.home(), config_path)
            if os.path.exists(home_config):
                config_path = home_config
            else:
                logger.warning(
                    f"MCP configuration file not found at {config_path} or {home_config}"
                )
                config_path = None

    # Start MCP servers if configuration exists
    mcp_client = None
    if config_path:
        logger.info(f"Using MCP configuration from {config_path}")
        mcp_client = MCPClient(config_path=config_path)
        await mcp_client.start_servers()

    # Create and start the Discord bot
    bot = create_bot(shared_mcp_client=mcp_client)

    try:
        logger.info("Starting Discord bot")
        await bot.start(os.getenv("DISCORD_TOKEN"))
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        if mcp_client:
            await mcp_client.stop_servers()
        await bot.close()
    except Exception as e:
        logger.exception(f"Error running bot: {e}")
        if mcp_client:
            await mcp_client.stop_servers()
        await bot.close()
    finally:
        # Ensure MCP servers are stopped
        if mcp_client:
            await mcp_client.stop_servers()


if __name__ == "__main__":
    asyncio.run(main())
