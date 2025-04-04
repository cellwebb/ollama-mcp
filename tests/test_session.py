"""Tests for the Session class."""

from unittest import mock

import pytest
from pytest_mock import MockerFixture

from ollama_mcp_discord.core.session import Session


class TestSession:
    """Behavior tests for the Session class."""

    @pytest.fixture
    def mock_ollama_client(self, mocker: MockerFixture):
        """Create a mock OllamaClient."""
        client = mocker.patch(
            "ollama_mcp_discord.ollama.client.OllamaClient", autospec=True
        )
        client_instance = client.return_value
        client_instance.generate.return_value = "Mock response"
        client_instance.list_models.return_value = [
            {"name": "llama3"},
            {"name": "mistral"},
        ]
        return client_instance

    @pytest.fixture
    def mock_mcp_client(self, mocker: MockerFixture):
        """Create a mock MCPClient."""
        client = mocker.patch("ollama_mcp_discord.mcp.client.MCPClient", autospec=True)
        client_instance = client.return_value
        client_instance.create_memory_entity.return_value = "memory-id"
        return client_instance

    @pytest.fixture
    def session(self, mock_ollama_client, mock_mcp_client):
        """Create a test Session instance with mocked clients."""
        with mock.patch("uuid.uuid4", return_value="test-uuid"):
            return Session(user_id=123, model_name="llama3")

    @pytest.mark.asyncio
    async def test_process_message_returns_ai_response(
        self, session, mock_ollama_client
    ):
        """
        Given a user message
        When processing the message
        Then the AI's response should be returned and added to message history
        """
        # Given
        user_message = "Hello, AI!"
        mock_ollama_client.generate.return_value = "Hello, human!"

        # When
        response = await session.process_message(user_message)

        # Then
        assert response == "Hello, human!"
        assert len(session.messages) == 2
        assert session.messages[0] == {"role": "user", "content": user_message}
        assert session.messages[1] == {"role": "assistant", "content": "Hello, human!"}

    @pytest.mark.asyncio
    async def test_set_model_changes_ollama_model(self, session, mock_ollama_client):
        """
        Given a valid model name
        When setting the model
        Then the model should be updated in the session and client
        """
        # Given
        new_model = "mistral"

        # When
        await session.set_model(new_model)

        # Then
        assert session.model_name == "mistral"
        assert session.ollama_client.model == "mistral"

    @pytest.mark.asyncio
    async def test_set_model_raises_error_for_invalid_model(
        self, session, mock_ollama_client
    ):
        """
        Given an invalid model name
        When setting the model
        Then a ValueError should be raised
        """
        # Given
        invalid_model = "nonexistent-model"

        # When/Then
        with pytest.raises(ValueError, match=f"Model '{invalid_model}' not found"):
            await session.set_model(invalid_model)

    @pytest.mark.asyncio
    async def test_create_memory_stores_content(self, session, mock_mcp_client):
        """
        Given content to remember
        When creating a memory
        Then the content should be stored using the MCP client
        """
        # Given
        memory_content = "Remember this important information"

        # When
        with mock.patch("uuid.uuid4", return_value="memory-uuid"):
            memory_id = await session.create_memory(memory_content)

        # Then
        assert memory_id == "memory-uuid"
        mock_mcp_client.create_memory_entity.assert_called_once_with(
            name="memory-uuid", entity_type="UserMemory", observations=[memory_content]
        )

    @pytest.mark.asyncio
    async def test_generate_response_uses_conversation_history(
        self, session, mock_ollama_client
    ):
        """
        Given previous conversation history
        When generating a response
        Then the history should be included in the context
        """
        # Given
        # Add some history
        session.messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"},
        ]

        # When
        await session._generate_response("Second message")

        # Then
        # Check that generate was called with the correct context
        mock_ollama_client.generate.assert_called_once()
        _, kwargs = mock_ollama_client.generate.call_args
        assert "context" in kwargs
        assert kwargs["context"] == session.messages
