"""Discord bot implementation using nextcord."""

import logging
from typing import Dict, Optional

import aiohttp
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from ollama_mcp_discord.core.session import Session
from ollama_mcp_discord.core.settings import settings
from ollama_mcp_discord.mcp.client import MCPClient
from ollama_mcp_discord.system_message import set_system_message

logger = logging.getLogger(__name__)

# User sessions storage
user_sessions: Dict[int, Session] = {}

# Shared MCP client
mcp_client: Optional[MCPClient] = None


def create_bot(shared_mcp_client: Optional[MCPClient] = None) -> commands.Bot:
    """Create and configure the Discord bot.

    Args:
        shared_mcp_client: An initialized MCP client to share across sessions
    """
    global mcp_client
    mcp_client = shared_mcp_client

    intents = nextcord.Intents.default()
    intents.message_content = True

    # Create bot with command prefix
    bot = commands.Bot(command_prefix=settings.command_prefix, intents=intents, help_command=None)

    @bot.event
    async def on_ready():
        """Handle bot ready event."""
        if bot.user is None:
            logger.error("Bot user is None")
            return

        logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
        logger.info(f"Connected to {len(bot.guilds)} guilds")
        if mcp_client:
            logger.info("Using shared MCP client")
        else:
            logger.info("No shared MCP client provided, sessions will create their own")

    # Message event listener for triggering on specific words
    @bot.event
    async def on_message(message):
        """Process messages."""
        # Ignore messages from bots (including self) to prevent loops
        if message.author.bot:
            return

        # Don't trigger on command messages
        if message.content.startswith(bot.command_prefix):
            # Process commands as normal
            await bot.process_commands(message)
            return

        # Make sure other commands still work
        await bot.process_commands(message)

    # Register commands
    register_commands(bot)

    return bot


def register_commands(bot: commands.Bot):
    """Register all text commands."""

    # System message slash command
    @bot.slash_command(name="set_system_message", description="Set the system message for the AI model")
    async def set_system_message_command(
        interaction: Interaction,
        message: str = SlashOption(name="message", description="The system message to set", required=True),
    ):
        """Set the system message for the AI model.

        Args:
            interaction: The interaction object
            message: The system message to set
        """
        # Defer the response to give us time to process
        await interaction.response.defer(ephemeral=True)

        try:
            # Set the system message
            set_system_message(message)

            # Respond to the user
            await interaction.followup.send("System message updated successfully!", ephemeral=True)
        except Exception as e:
            logger.exception(f"Error setting system message: {e}")
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)

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

                # Handle Discord's 2000 character limit
                if len(response) <= 2000:
                    # Send the response as is if it's within the limit
                    await ctx.reply(response)
                else:
                    # Split the response into chunks of 2000 characters or less
                    chunks = [response[i : i + 1900] for i in range(0, len(response), 1900)]
                    # Send the first chunk as a reply to maintain thread
                    await ctx.reply(f"{chunks[0]}... (continued)")
                    # Send remaining chunks as follow-up messages
                    for i, chunk in enumerate(chunks[1:], 1):
                        if i == len(chunks) - 1:  # Last chunk
                            await ctx.send(chunk)
                        else:
                            await ctx.send(f"{chunk}... (continued)")
            except aiohttp.ClientResponseError as e:
                error_msg = f"API Error: {e.status} {e.message}"
                if e.status == 400:
                    error_msg += (
                        "\nThis could be due to an invalid model name or a model compatibility issue."  # noqa: E501
                    )
                    # Try using a different model
                    error_msg += "\nTry using a different model with: !model llama3.2:latest"
                logger.error(error_msg)
                await ctx.reply(error_msg)
            except Exception as e:
                logger.exception(f"Error processing chat message: {e}")
                await ctx.reply(f"An error occurred while processing your message: {str(e)}")

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
                await ctx.reply(f"I'll remember that! Memory created with ID: {memory_id}")
            except Exception as e:
                logger.exception(f"Error creating memory: {e}")
                await ctx.reply(f"An error occurred while creating memory: {str(e)}")

    # System message command
    @bot.command(name="system_message")
    async def system_message_command(ctx: commands.Context, *, message: str):
        """Set the system message for the AI model.

        Usage: !system_message <message>
        """
        # Show typing indicator
        async with ctx.typing():
            try:
                # Set the system message
                set_system_message(message)

                # Confirm to the user
                await ctx.reply("System message updated successfully!")
            except Exception as e:
                logger.exception(f"Error setting system message: {e}")
                await ctx.reply(f"An error occurred: {str(e)}")

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
        embed.add_field(name="!chat <message>", value="Chat with the AI model", inline=False)

        embed.add_field(name="!model <n>", value="Change which Ollama model to use", inline=False)

        embed.add_field(
            name="!remember <content>",
            value="Store information in the AI's memory",
            inline=False,
        )

        embed.add_field(
            name="/set_system_message <message>",
            value="Set the system message for the AI model (slash command)",
            inline=False,
        )

        embed.add_field(
            name="!system_message <message>",
            value="Set the system message for the AI model",
            inline=False,
        )

        await ctx.reply(embed=embed)

    logger.info("Text commands registered")


def get_user_session(user_id: int) -> Session:
    """Get or create a session for a user.

    Args:
        user_id: The Discord user ID

    Returns:
        The user's session
    """
    if user_id not in user_sessions:
        # Create a new session for this user
        user_sessions[user_id] = Session(
            user_id=user_id,
            model_name=settings.ollama_model,
            mcp_client=mcp_client,
        )
    return user_sessions[user_id]
