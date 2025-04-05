"""Main entry point for the Ollama-MCP Discord Bot."""

import asyncio
import logging

import dotenv

from ollama_mcp_discord.core.config import ConfigurationError, config
from ollama_mcp_discord.discord.bot import create_bot
from ollama_mcp_discord.mcp.client import MCPClient

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
        logger.info("Creating MCP client")
        mcp_client = MCPClient(config_path=config.mcp_config_path)

        logger.info("Starting MCP servers")
        await mcp_client.start_servers()

        logger.info("Creating Discord bot")
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
        logger.info("Stopping MCP servers")
        if "mcp_client" in locals():
            await mcp_client.stop_servers()
        logger.info("Closing Discord bot")
        if "bot" in locals():
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
