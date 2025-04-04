"""Main entry point for the Ollama-MCP Discord Bot."""

import asyncio
import logging
import os

import dotenv

from ollama_mcp_discord.discord.bot import create_bot

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

    # Create and start the Discord bot
    bot = create_bot()

    try:
        logger.info("Starting Discord bot")
        await bot.start(os.getenv("DISCORD_TOKEN"))
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await bot.close()
    except Exception as e:
        logger.exception(f"Error running bot: {e}")
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
