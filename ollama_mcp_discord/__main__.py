"""Main entry point for the Ollama-MCP Discord Bot."""

import asyncio
import logging
import os
import pathlib

import dotenv

from ollama_mcp_discord.core.config import ConfigurationError, config
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

    try:
        # Create MCP client using configuration
        mcp_client = MCPClient(config_path=config.mcp_config_path)
        await mcp_client.start_servers()

        # Create and start the Discord bot
        bot = create_bot(shared_mcp_client=mcp_client)

        logger.info("Starting Discord bot")
        await bot.start(config.discord_token)
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.exception(f"Error running bot: {e}")
    finally:
        # Ensure MCP servers are stopped and bot is closed
        if "mcp_client" in locals():
            await mcp_client.stop_servers()
        if "bot" in locals():
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
