"""Discord bot implementation using nextcord."""

import logging
import os
from typing import Dict, Optional

import nextcord
from nextcord.ext import commands

from ollama_mcp_discord.core.session import Session

logger = logging.getLogger(__name__)

# User sessions storage
user_sessions: Dict[int, Session] = {}


def create_bot() -> commands.Bot:
    """Create and configure the Discord bot."""
    intents = nextcord.Intents.default()
    intents.message_content = True

    # Create bot with command prefix
    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

    @bot.event
    async def on_ready():
        """Handle bot ready event."""
        logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
        logger.info(f"Connected to {len(bot.guilds)} guilds")

    # Register commands
    register_commands(bot)

    return bot


def register_commands(bot: commands.Bot):
    """Register all text commands."""

    # Chat command
    @bot.command(name="chat")
    async def chat(ctx: commands.Context, *, message: str):
        """Chat with the AI model.

        Usage: !chat <your message>
        """
        # Show typing indicator
        async with ctx.typing():
            # Get or create user session
            session = get_user_session(ctx.author.id)

            try:
                # Process the message
                response = await session.process_message(message)

                # Send the response
                await ctx.reply(response)
            except Exception as e:
                logger.exception(f"Error processing chat message: {e}")
                await ctx.reply(
                    f"An error occurred while processing your message: {str(e)}"
                )

    # Model selection command
    @bot.command(name="model")
    async def model(ctx: commands.Context, name: str):
        """Select which model to use.

        Usage: !model <model_name>
        """
        # Show typing indicator
        async with ctx.typing():
            # Get or create user session
            session = get_user_session(ctx.author.id)

            try:
                # Set the model
                await session.set_model(name)

                # Confirm to the user
                await ctx.reply(f"Model set to {name}")
            except Exception as e:
                logger.exception(f"Error setting model: {e}")
                await ctx.reply(f"An error occurred while setting the model: {str(e)}")

    # Memory creation command
    @bot.command(name="remember")
    async def remember(ctx: commands.Context, *, content: str):
        """Create a new memory item.

        Usage: !remember <content>
        """
        # Show typing indicator
        async with ctx.typing():
            # Get or create user session
            session = get_user_session(ctx.author.id)

            try:
                # Create memory
                memory_id = await session.create_memory(content)

                # Confirm to the user
                await ctx.reply(
                    f"I'll remember that! Memory created with ID: {memory_id}"
                )
            except Exception as e:
                logger.exception(f"Error creating memory: {e}")
                await ctx.reply(f"An error occurred while creating memory: {str(e)}")

    # Custom help command
    @bot.command(name="help")
    async def help_command(ctx: commands.Context):
        """Show help for all commands.

        Usage: !help
        """
        embed = nextcord.Embed(
            title="Ollama-MCP Discord Bot Help",
            description="Here are the commands you can use:",
            color=nextcord.Color.blue(),
        )

        # Add command fields to the embed
        embed.add_field(
            name="!chat <message>", value="Chat with the AI model", inline=False
        )

        embed.add_field(
            name="!model <name>", value="Change which Ollama model to use", inline=False
        )

        embed.add_field(
            name="!remember <content>",
            value="Store information in the AI's memory",
            inline=False,
        )

        embed.add_field(name="!help", value="Show this help message", inline=False)

        # Add footer with additional info
        embed.set_footer(text="Powered by Ollama and MCP")

        await ctx.reply(embed=embed)

    logger.info("Text commands registered")


def get_user_session(user_id: int) -> Session:
    """Get or create a session for the user."""
    if user_id not in user_sessions:
        # Create a new session
        model_name = os.getenv("DEFAULT_MODEL", "llama3")
        user_sessions[user_id] = Session(user_id, model_name)

    return user_sessions[user_id]
