"""Discord bot implementation using nextcord."""

import logging
import os
from typing import Dict, List, Optional, Set

import nextcord
from nextcord.ext import commands

from ollama_mcp_discord.core.session import Session

logger = logging.getLogger(__name__)

# User sessions storage
user_sessions: Dict[int, Session] = {}

# Trigger words that the bot will respond to
TRIGGER_WORDS: Set[str] = {"hello", "hey", "ollama", "ai", "bot"}
TRIGGER_RESPONSES: Dict[str, str] = {
    "hello": "Hello there! How can I help you today?",
    "hey": "Hey! Need something from me?",
    "ollama": "You mentioned Ollama! I'm powered by Ollama models.",
    "ai": "AI is my specialty! What would you like to know?",
    "bot": "I'm your friendly neighborhood bot! Type !help to see what I can do.",
}


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

    # Add or remove trigger words command
    @bot.command(name="trigger")
    async def trigger(
        ctx: commands.Context, action: str, word: str, *, response: str = None
    ):
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

        embed.add_field(
            name="!trigger add <word> <response>",
            value="Add a word that the bot will respond to",
            inline=False,
        )

        embed.add_field(
            name="!trigger remove <word>", value="Remove a trigger word", inline=False
        )

        embed.add_field(name="!triggers", value="List all trigger words", inline=False)

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
