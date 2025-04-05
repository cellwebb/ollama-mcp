"""Discord bot implementation using nextcord."""

import logging
import os
from typing import Dict, Optional, Set

import aiohttp
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from ollama_mcp_discord.core.session import Session
from ollama_mcp_discord.mcp.client import MCPClient
from ollama_mcp_discord.system_message import set_system_message

logger = logging.getLogger(__name__)

# User sessions storage
user_sessions: Dict[int, Session] = {}

# Shared MCP client
mcp_client: Optional[MCPClient] = None

# Trigger words that the bot will respond to
TRIGGER_WORDS: Set[str] = {"hello", "hey", "ollama", "ai", "bot"}
TRIGGER_RESPONSES: Dict[str, str] = {
    "hello": "Hello there! How can I help you today?",
    "hey": "Hey! Need something from me?",
    "ollama": "You mentioned Ollama! I'm powered by Ollama models.",
    "ai": "AI is my specialty! What would you like to know?",
    "bot": "I'm your friendly neighborhood bot! Type !help to see what I can do.",
}


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
    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

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
        """Process messages and respond to trigger words."""
        # Ignore messages from bots (including self) to prevent loops
        if message.author.bot:
            return

        # Don't trigger on command messages
        if message.content.startswith(bot.command_prefix):
            # Process commands as normal
            await bot.process_commands(message)
            return

        # Check if message contains any trigger words
        message_lower = message.content.lower()
        for word in TRIGGER_WORDS:
            if word in message_lower.split():
                response = TRIGGER_RESPONSES.get(word, f"I noticed you said '{word}'!")
                await message.reply(response)
                # Only respond to the first trigger word found
                break

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

                # Send the response
                await ctx.reply(response)
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

    # Add or remove trigger words command
    @bot.command(name="trigger")
    async def trigger(ctx: commands.Context, action: str, word: str, *, response: str = "") -> None:
        """Add or remove trigger words.

        Usage:
        !trigger add <word> <response>
        !trigger remove <word>
        """
        global TRIGGER_WORDS, TRIGGER_RESPONSES

        action = action.lower()
        word = word.lower()

        if action == "add":
            if not response:
                await ctx.reply("Please provide a response for this trigger word.")
                return

            TRIGGER_WORDS.add(word)
            TRIGGER_RESPONSES[word] = response
            await ctx.reply(f"Added trigger word: '{word}' with response: '{response}'")

        elif action == "remove":
            if word in TRIGGER_WORDS:
                TRIGGER_WORDS.remove(word)
                if word in TRIGGER_RESPONSES:
                    del TRIGGER_RESPONSES[word]
                await ctx.reply(f"Removed trigger word: '{word}'")
            else:
                await ctx.reply(f"Trigger word '{word}' not found.")

        else:
            await ctx.reply("Invalid action. Use 'add' or 'remove'.")

    # List trigger words command
    @bot.command(name="triggers")
    async def triggers(ctx: commands.Context):
        """List all trigger words and their responses.

        Usage: !triggers
        """
        if not TRIGGER_WORDS:
            await ctx.reply("No trigger words are set.")
            return

        embed = nextcord.Embed(
            title="Trigger Words",
            description="Words that will trigger a response:",
            color=nextcord.Color.green(),
        )

        for word in TRIGGER_WORDS:
            response = TRIGGER_RESPONSES.get(word, "No response set")
            embed.add_field(name=word, value=response, inline=False)

        await ctx.reply(embed=embed)

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
            name="!trigger add <word> <response>",
            value="Add a trigger word that the bot will respond to",
            inline=False,
        )

        embed.add_field(
            name="!trigger remove <word>",
            value="Remove a trigger word",
            inline=False,
        )

        embed.add_field(
            name="!triggers",
            value="List all trigger words and their responses",
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
    """Get or create user session.

    Args:
        user_id: Discord user ID

    Returns:
        A session for the user
    """
    # Check if we already have a session for this user
    if user_id in user_sessions:
        return user_sessions[user_id]

    # Default model - could be configured differently
    default_model = os.getenv("DEFAULT_MODEL", "llama3")

    # Create new session with shared MCP client if available
    session = Session(user_id, default_model, mcp_client=mcp_client)
    user_sessions[user_id] = session

    logger.info(f"Created new session for user {user_id} with model {default_model}")
    return session
