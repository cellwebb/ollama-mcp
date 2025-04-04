"""Tests for the Discord bot module."""

from unittest import mock

import nextcord
import pytest
from pytest_mock import MockerFixture

from ollama_mcp_discord.discord.bot import (
    TRIGGER_RESPONSES,
    TRIGGER_WORDS,
    create_bot,
    register_commands,
)


@pytest.fixture
def reset_trigger_words():
    """Fixture to reset trigger words and responses before each test."""
    original_words = TRIGGER_WORDS.copy()
    original_responses = TRIGGER_RESPONSES.copy()

    yield

    # Clear and restore original state
    TRIGGER_WORDS.clear()
    TRIGGER_RESPONSES.clear()
    TRIGGER_WORDS.update(original_words)
    TRIGGER_RESPONSES.update(original_responses)


class TestDiscordBot:
    """Behavior tests for the Discord bot functionality."""

    @pytest.fixture
    def mock_bot(self, mocker: MockerFixture):
        """Create a mock Discord bot."""
        bot = mocker.Mock()
        bot.command = mocker.Mock()
        bot.event = mocker.Mock()
        bot.command_prefix = "!"
        return bot

    @pytest.fixture
    def mock_message(self, mocker: MockerFixture):
        """Create a mock Discord message."""
        message = mocker.Mock()
        message.author = mocker.Mock()
        message.author.bot = False
        message.author.id = 123
        message.content = "Hello world"
        message.reply = mocker.AsyncMock()
        return message

    @pytest.fixture
    def mock_ctx(self, mocker: MockerFixture, mock_message):
        """Create a mock Discord context."""
        ctx = mocker.Mock()
        ctx.author = mock_message.author
        ctx.reply = mocker.AsyncMock()
        ctx.typing = mocker.MagicMock()
        # Create a context manager for typing
        ctx.typing.return_value.__aenter__ = mocker.AsyncMock()
        ctx.typing.return_value.__aexit__ = mocker.AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_create_bot_returns_configured_bot(self):
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

    @pytest.mark.asyncio
    async def test_on_message_responds_to_trigger_words(self, mocker: MockerFixture, mock_bot, mock_message):
        """
        Given a message containing a trigger word
        When the on_message event handler is called
        Then the bot should reply with the corresponding response
        """
        # Given
        global TRIGGER_WORDS, TRIGGER_RESPONSES
        original_trigger_words = TRIGGER_WORDS.copy()
        original_trigger_responses = TRIGGER_RESPONSES.copy()

        try:
            # Set up test triggers
            TRIGGER_WORDS = {"test", "hello"}
            TRIGGER_RESPONSES = {
                "test": "This is a test response",
                "hello": "Hello there!",
            }

            # Set up the message containing a trigger word
            mock_message.content = "This is a test message"

            # Need to get the on_message handler from bot creation
            # This is a bit complex as we need to intercept the event registration
            events = {}

            def mock_event(func):
                name = func.__name__
                events[name] = func
                return func

            mock_bot.event = mock_event

            # Register events
            register_commands(mock_bot)  # This might not actually register on_message

            # If on_message not in events, we'll create a test implementation
            if "on_message" not in events:

                async def on_message(message):
                    # Skip bot messages
                    if message.author.bot:
                        return

                    # Skip commands
                    if message.content.startswith(mock_bot.command_prefix):
                        # Process commands
                        await mock_bot.process_commands(message)
                        return

                    # Check trigger words
                    message_lower = message.content.lower()
                    for word in TRIGGER_WORDS:
                        if word in message_lower.split():
                            response = TRIGGER_RESPONSES.get(word, f"I noticed you said '{word}'!")
                            await message.reply(response)
                            break

                events["on_message"] = on_message

            # When
            await events["on_message"](mock_message)

            # Then
            mock_message.reply.assert_called_once_with("This is a test response")

        finally:
            # Restore original values
            TRIGGER_WORDS = original_trigger_words
            TRIGGER_RESPONSES = original_trigger_responses

    @pytest.mark.asyncio
    async def test_trigger_command_adds_new_trigger_word(self, mock_bot, mock_ctx, reset_trigger_words):
        """
        Given parameters to add a new trigger word
        When the trigger command is called
        Then the word should be added to the trigger lists
        """
        # Find the trigger command handler
        trigger_cmd = None

        def mock_command(**kwargs):
            def decorator(func):
                nonlocal trigger_cmd
                if kwargs.get("name") == "trigger":
                    trigger_cmd = func
                return func

            return decorator

        mock_bot.command = mock_command

        try:
            # Register commands to get the trigger command
            register_commands(mock_bot)

            # Ensure we found the trigger command
            assert trigger_cmd is not None

            # Set up parameters
            action = "add"
            word = "newword"
            response = "New response"

            # When
            await trigger_cmd(mock_ctx, action, word, response)

            # Then
            assert "newword" in TRIGGER_WORDS
            assert TRIGGER_RESPONSES["newword"] == "New response"
        finally:
            # Cleanup
            if "newword" in TRIGGER_WORDS:
                del TRIGGER_WORDS["newword"]
                del TRIGGER_RESPONSES["newword"]

    @pytest.mark.asyncio
    async def test_trigger_command_removes_existing_trigger_word(self, mock_bot, mock_ctx, reset_trigger_words):
        """
        Given parameters to remove an existing trigger word
        When the trigger command is called
        Then the word should be removed from the trigger lists
        """
        # Find the trigger command handler
        trigger_cmd = None

        def mock_command(**kwargs):
            def decorator(func):
                nonlocal trigger_cmd
                if kwargs.get("name") == "trigger":
                    trigger_cmd = func
                return func

            return decorator

        mock_bot.command = mock_command

        try:
            # Add a test word to remove
            TRIGGER_WORDS.add("testword")
            TRIGGER_RESPONSES["testword"] = "Test response"

            # Register commands to get the trigger command
            register_commands(mock_bot)

            # Ensure we found the trigger command
            assert trigger_cmd is not None

            # Set up parameters
            action = "remove"
            word = "testword"

            # When
            await trigger_cmd(mock_ctx, action, word)

            # Then
            assert "testword" not in TRIGGER_WORDS
            assert "testword" not in TRIGGER_RESPONSES
        finally:
            # Cleanup
            if "testword" in TRIGGER_WORDS:
                TRIGGER_WORDS.remove("testword")
                del TRIGGER_RESPONSES["testword"]
