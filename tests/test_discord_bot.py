"""Tests for the Discord bot module."""

import nextcord
import pytest

from ollama_mcp_discord.discord.bot import create_bot


@pytest.mark.asyncio
async def test_create_bot_returns_configured_bot():
    """
    When creating a bot
    Then it should return a configured nextcord.ext.commands.Bot
    """
    # When
    bot = create_bot()

    # Then
    assert isinstance(bot, nextcord.ext.commands.Bot)
    assert bot.command_prefix == "!"
    assert bot.intents.message_content is True
