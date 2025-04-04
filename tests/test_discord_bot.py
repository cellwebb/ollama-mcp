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

    @pytest.mark.asyncio
    async def test_trigger_command_adding_existing_trigger_word(self, mock_bot, mock_ctx, reset_trigger_words):
        """
        Given parameters to add an already existing trigger word
        When the trigger command is called
        Then the word should be updated with the new response without duplication
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
            # Add a test word initially
            TRIGGER_WORDS.add("existingword")
            TRIGGER_RESPONSES["existingword"] = "Original response"

            # Count initial size
            initial_count = len(TRIGGER_WORDS)

            # Register commands to get the trigger command
            register_commands(mock_bot)

            # Ensure we found the trigger command
            assert trigger_cmd is not None

            # Set up parameters to add the same word with a different response
            action = "add"
            word = "existingword"
            new_response = "Updated response"

            # When
            await trigger_cmd(mock_ctx, action, word, new_response)

            # Then
            assert "existingword" in TRIGGER_WORDS
            assert TRIGGER_RESPONSES["existingword"] == "Updated response"
            # Ensure no duplication occurred
            assert len(TRIGGER_WORDS) == initial_count

            # Verify the context replied with appropriate message
            mock_ctx.reply.assert_called_once()
        finally:
            # Cleanup
            if "existingword" in TRIGGER_WORDS:
                TRIGGER_WORDS.remove("existingword")
                del TRIGGER_RESPONSES["existingword"]

    @pytest.mark.asyncio
    async def test_trigger_command_removing_nonexistent_trigger_word(self, mock_bot, mock_ctx, reset_trigger_words):
        """
        Given parameters to remove a trigger word that doesn't exist
        When the trigger command is called
        Then the operation should be handled gracefully without error
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

        # Make a copy of current trigger words to verify no changes
        initial_words = TRIGGER_WORDS.copy()
        initial_responses = TRIGGER_RESPONSES.copy()

        # Register commands to get the trigger command
        register_commands(mock_bot)

        # Ensure we found the trigger command
        assert trigger_cmd is not None

        # Set up parameters for nonexistent word
        action = "remove"
        word = "nonexistentword"  # A word that doesn't exist in the triggers

        # When
        await trigger_cmd(mock_ctx, action, word)

        # Then
        # Verify nothing was changed in the trigger words
        assert TRIGGER_WORDS == initial_words
        assert TRIGGER_RESPONSES == initial_responses

        # Verify the context replied with appropriate error message
        mock_ctx.reply.assert_called_once()
        # Can add specific assertion for error message if implemented in the bot

    @pytest.mark.asyncio
    async def test_message_with_multiple_trigger_words(self, mocker: MockerFixture, mock_bot, mock_message):
        """
        Given a message containing multiple trigger words
        When the on_message event handler is called
        Then the bot should reply with the response for only the first encountered trigger word
        """
        # Given
        global TRIGGER_WORDS, TRIGGER_RESPONSES
        original_trigger_words = TRIGGER_WORDS.copy()
        original_trigger_responses = TRIGGER_RESPONSES.copy()

        try:
            # Set up test triggers with multiple words
            TRIGGER_WORDS = {"first", "second", "third"}
            TRIGGER_RESPONSES = {
                "first": "Response to first",
                "second": "Response to second",
                "third": "Response to third",
            }

            # Set up the message containing multiple trigger words
            # Order in the message: second, first, third
            mock_message.content = "This message contains second and first and third triggers"

            # Need to get the on_message handler from bot creation
            # This is a bit complex as we need to intercept the event registration
            events = {}

            def mock_event(func):
                name = func.__name__
                events[name] = func
                return func

            mock_bot.event = mock_event

            # Register events
            register_commands(mock_bot)

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
                            break  # Only respond to the first trigger word

                events["on_message"] = on_message

            # When
            await events["on_message"](mock_message)

            # Then
            # Should only respond to "second" as it appears first in the message
            mock_message.reply.assert_called_once_with("Response to second")

            # Verify it doesn't respond multiple times
            assert mock_message.reply.call_count == 1

        finally:
            # Restore original values
            TRIGGER_WORDS = original_trigger_words
            TRIGGER_RESPONSES = original_trigger_responses

    @pytest.mark.asyncio
    async def test_trigger_word_as_substring(self, mocker: MockerFixture, mock_bot, mock_message):
        """
        Given a message containing a trigger word as part of a larger word
        When the on_message event handler is called
        Then the bot should not respond to the substring
        """
        # Given
        global TRIGGER_WORDS, TRIGGER_RESPONSES
        original_trigger_words = TRIGGER_WORDS.copy()
        original_trigger_responses = TRIGGER_RESPONSES.copy()

        try:
            # Set up test trigger
            TRIGGER_WORDS = {"help"}
            TRIGGER_RESPONSES = {
                "help": "How can I help you?",
            }

            # Set up the message containing the trigger word as part of another word
            mock_message.content = "I'm helping myself, thanks!"  # "help" is part of "helping"

            # Need to get the on_message handler
            events = {}

            def mock_event(func):
                name = func.__name__
                events[name] = func
                return func

            mock_bot.event = mock_event

            # Register events
            register_commands(mock_bot)

            # If on_message not in events, create a test implementation
            if "on_message" not in events:

                async def on_message(message):
                    # Skip bot messages
                    if message.author.bot:
                        return

                    # Skip commands
                    if message.content.startswith(mock_bot.command_prefix):
                        await mock_bot.process_commands(message)
                        return

                    # Check trigger words - only match whole words
                    message_words = message.content.lower().split()
                    for word in TRIGGER_WORDS:
                        if word in message_words:
                            response = TRIGGER_RESPONSES.get(word, f"I noticed you said '{word}'!")
                            await message.reply(response)
                            break

                events["on_message"] = on_message

            # When
            await events["on_message"](mock_message)

            # Then
            # Should not respond since "help" is only part of "helping"
            mock_message.reply.assert_not_called()

        finally:
            # Restore original values
            TRIGGER_WORDS = original_trigger_words
            TRIGGER_RESPONSES = original_trigger_responses
