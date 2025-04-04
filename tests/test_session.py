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
        client = mocker.patch("ollama_mcp_discord.ollama.client.OllamaClient", autospec=True)
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
    async def test_process_message_returns_ai_response(self, session, mock_ollama_client):
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
    async def test_set_model_raises_error_for_invalid_model(self, session, mock_ollama_client):
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
    async def test_generate_response_uses_conversation_history(self, session, mock_ollama_client):
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

    @pytest.mark.asyncio
    async def test_conversation_history_capacity(self, session, mock_ollama_client):
        """
        Given more messages than the maximum history capacity
        When processing a new message
        Then only the most recent messages should be retained up to the capacity limit
        """
        # Given
        # Add more messages than the typical capacity (assuming a limit exists in the Session class)
        # We'll assume the limit is 10 messages (5 exchanges) for this test
        max_capacity = 10

        # Generate message history that exceeds capacity
        for i in range(max_capacity + 2):  # Add 2 extra to exceed capacity
            if i % 2 == 0:
                session.messages.append({"role": "user", "content": f"User message {i // 2}"})
            else:
                session.messages.append({"role": "assistant", "content": f"Assistant response {i // 2}"})

        original_messages = session.messages.copy()
        assert len(original_messages) > max_capacity

        # Save a new message that would make us exceed capacity
        new_message = "This should cause oldest messages to be removed"
        mock_ollama_client.generate.return_value = "Response to new message"

        # When
        await session.process_message(new_message)

        # Then
        # Verify we don't exceed the expected capacity
        assert len(session.messages) <= max_capacity

        # Verify the oldest messages were dropped
        # The newest messages should match the end of the original list plus our new exchange
        # We'll compare specific messages instead of storing the expected list

        # Check that newest messages are preserved (allowing for capacity limit implementation details)
        # The newest user message and response should always be present
        assert session.messages[-2] == {"role": "user", "content": new_message}
        expected_response = {"role": "assistant", "content": "Response to new message"}
        assert session.messages[-1] == expected_response

    @pytest.mark.asyncio
    async def test_create_memory_with_invalid_content(self, session, mock_mcp_client):
        """
        Given invalid or empty content
        When creating a memory
        Then it should raise a validation error
        """
        # Given
        empty_content = ""

        # When/Then
        with pytest.raises(ValueError, match="Memory content cannot be empty"):
            await session.create_memory(empty_content)

        # MCP client should not be called with invalid content
        mock_mcp_client.create_memory_entity.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_model_multiple_times(self, session, mock_ollama_client):
        """
        Given multiple model changes in succession
        When setting the model repeatedly
        Then each change should be applied correctly
        """
        # Given
        initial_model = session.model_name
        assert initial_model == "llama3"  # From the fixture

        # When changing model multiple times
        # First change
        await session.set_model("mistral")
        assert session.model_name == "mistral"

        # Second change back to original
        await session.set_model("llama3")
        assert session.model_name == "llama3"

        # Third change to mistral again
        await session.set_model("mistral")
        assert session.model_name == "mistral"

        # Then
        # Verify the model is set correctly after multiple changes
        assert session.model_name == "mistral"
        assert session.ollama_client.model == "mistral"

    @pytest.mark.asyncio
    async def test_sequential_thinking_with_branching(self, session, mock_mcp_client):
        """
        Given sequential thinking with branching
        When processing branching thoughts
        Then the session should handle it correctly
        """
        # Given
        initial_thought = "Initial thought about the problem"

        # Mock the MCP client sequential thinking method
        mock_mcp_client.sequential_thinking = mock.AsyncMock()

        # Configure responses for different thinking scenarios
        # First call - regular thought
        mock_mcp_client.sequential_thinking.side_effect = [
            {
                "thought": "First step in analysis",
                "thoughtNumber": 1,
                "totalThoughts": 3,
                "nextThoughtNeeded": True,
                "branchId": None,
                "branchFromThought": None,
                "isRevision": False,
            },
            # Second call - create a branch
            {
                "thought": "Actually, let me try a different approach",
                "thoughtNumber": 2,
                "totalThoughts": 4,  # Increased due to new branching path
                "nextThoughtNeeded": True,
                "branchId": "alternative-path",
                "branchFromThought": 1,
                "isRevision": False,
            },
            # Third call - continue in the branch
            {
                "thought": "Following the alternative approach",
                "thoughtNumber": 3,
                "totalThoughts": 4,
                "nextThoughtNeeded": True,
                "branchId": "alternative-path",
                "branchFromThought": None,
                "isRevision": False,
            },
            # Fourth call - final conclusion
            {
                "thought": "Final conclusion from alternative approach",
                "thoughtNumber": 4,
                "totalThoughts": 4,
                "nextThoughtNeeded": False,
                "branchId": "alternative-path",
                "branchFromThought": None,
                "isRevision": False,
            },
        ]

        # When
        # Start the sequential thinking process
        result = await session.sequential_thinking(initial_thought)

        # Then
        # Verify the MCP client was called correctly
        assert mock_mcp_client.sequential_thinking.call_count == 4

        # First call should have the initial thought
        first_call_args = mock_mcp_client.sequential_thinking.call_args_list[0][0][0]
        assert first_call_args["thought"] == initial_thought

        # Last call should return the final result (with nextThoughtNeeded = False)
        assert result["thought"] == "Final conclusion from alternative approach"
        assert result["nextThoughtNeeded"] is False
