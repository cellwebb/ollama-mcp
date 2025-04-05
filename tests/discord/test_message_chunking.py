"""Tests for message chunking functionality in the Discord bot."""

from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from nextcord.ext import commands

from ollama_mcp_discord.discord.bot import register_commands


class TestMessageChunking:
    """Tests for the message chunking functionality."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot for testing."""
        mock_bot = MagicMock(spec=commands.Bot)
        # Store the command function when the decorator is called
        mock_bot.command_functions = {}

        def command_decorator(*args, **kwargs):
            def decorator(func):
                name = kwargs.get("name", func.__name__)
                mock_bot.command_functions[name] = func
                return func

            return decorator

        mock_bot.command = MagicMock(side_effect=command_decorator)
        return mock_bot

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock context for testing."""
        mock_ctx = AsyncMock()
        mock_ctx.reply = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.typing = MagicMock(return_value=AsyncMock().__aenter__.return_value)
        mock_ctx.author = MagicMock()
        mock_ctx.author.id = 12345
        return mock_ctx

    @pytest.mark.asyncio
    @patch("ollama_mcp_discord.discord.bot.get_user_session")
    async def test_chat_command_with_short_response(self, mock_get_user_session, mock_bot, mock_ctx):
        """
        When the bot receives a chat command with a response under 2000 characters
        Then it should reply with a single message
        """
        # Setup
        mock_session = AsyncMock()
        mock_session.process_message.return_value = "This is a short response"
        mock_get_user_session.return_value = mock_session

        # Register commands to get the chat function
        register_commands(mock_bot)

        # Get the chat command function
        chat_command = mock_bot.command_functions.get("chat")
        assert chat_command is not None, "Chat command not registered"

        # Execute
        await chat_command(mock_ctx, message="Test message")

        # Assert
        mock_ctx.reply.assert_called_once_with("This is a short response")
        mock_ctx.send.assert_not_called()

    @pytest.mark.asyncio
    @patch("ollama_mcp_discord.discord.bot.get_user_session")
    async def test_chat_command_with_long_response(self, mock_get_user_session, mock_bot, mock_ctx):
        """
        When the bot receives a chat command with a response over 2000 characters
        Then it should split the response into multiple messages
        """
        # Setup
        long_response = "A" * 4000  # 4000 character response
        mock_session = AsyncMock()
        mock_session.process_message.return_value = long_response
        mock_get_user_session.return_value = mock_session

        # Register commands to get the chat function
        register_commands(mock_bot)

        # Get the chat command function
        chat_command = mock_bot.command_functions.get("chat")
        assert chat_command is not None, "Chat command not registered"

        # Execute
        await chat_command(mock_ctx, message="Test message")

        # Assert
        # Should have called reply with the first chunk
        first_chunk = "A" * 1900 + "... (continued)"
        mock_ctx.reply.assert_called_once_with(first_chunk)

        # Should have called send with the remaining chunks
        second_chunk = "A" * 1900 + "... (continued)"
        third_chunk = "A" * 200  # The remaining 200 characters

        # Check that the send method was called with the correct chunks
        expected_calls = [call(second_chunk), call(third_chunk)]
        mock_ctx.send.assert_has_calls(expected_calls)

        # Should have called send twice (for the second and third chunks)
        assert mock_ctx.send.call_count == 2, f"Expected 2 send calls, got {mock_ctx.send.call_count}"
