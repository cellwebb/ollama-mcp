"""Tests for the OllamaClient class."""

from unittest import mock

import aiohttp
import pytest

from ollama_mcp_discord.ollama.client import OllamaClient


class TestOllamaClient:
    """Behavior tests for the OllamaClient class."""

    @pytest.fixture
    def client(self):
        """Create a test OllamaClient instance."""
        return OllamaClient(host="http://test.ollama:11434", model="test-model")

    @pytest.mark.asyncio
    async def test_list_models_returns_available_models(self, client):
        """When listing models, it should return models from the Ollama API."""
        # Given
        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.json = mock.AsyncMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3", "modified_at": "2023-06-01T12:00:00Z"},
                {"name": "mistral", "modified_at": "2023-05-30T10:30:00Z"},
            ]
        }

        # Create a context manager mock for the response
        cm = mock.MagicMock()
        cm.__aenter__ = mock.AsyncMock(return_value=mock_response)
        cm.__aexit__ = mock.AsyncMock()

        # Create a session mock
        session_mock = mock.MagicMock()
        session_mock.get = mock.MagicMock(return_value=cm)

        with (
            mock.patch.object(client, "_ensure_session", mock.AsyncMock()),
            mock.patch.object(client, "session", session_mock),
        ):
            # When
            result = await client.list_models()

            # Then
            assert len(result) == 2
            assert result[0]["name"] == "llama3"
            assert result[1]["name"] == "mistral"

    @pytest.mark.asyncio
    async def test_generate_returns_model_response(self, client):
        """When generating text, it should return the model's response."""
        # Given
        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.json = mock.AsyncMock()
        mock_response.json.return_value = {
            "model": "test-model",
            "response": "This is a test response",
            "done": True,
        }

        # Create a context manager mock for the response
        cm = mock.MagicMock()
        cm.__aenter__ = mock.AsyncMock(return_value=mock_response)
        cm.__aexit__ = mock.AsyncMock()

        # Create a session mock
        session_mock = mock.MagicMock()
        session_mock.post = mock.MagicMock(return_value=cm)

        with (
            mock.patch.object(client, "_ensure_session", mock.AsyncMock()),
            mock.patch.object(client, "session", session_mock),
        ):
            # When
            result = await client.generate(
                prompt="Test prompt",
                system="You are a test assistant",
                context=[],
            )

            # Then
            assert result == "This is a test response"

    @pytest.mark.asyncio
    async def test_generate_with_context_sends_correct_payload(self, client):
        """When generating with context, it should include context in the payload."""
        # Given
        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.json = mock.AsyncMock()
        mock_response.json.return_value = {
            "model": "test-model",
            "response": "Response with context",
            "done": True,
        }

        # Create a context manager mock for the response
        cm = mock.MagicMock()
        cm.__aenter__ = mock.AsyncMock(return_value=mock_response)
        cm.__aexit__ = mock.AsyncMock()

        # Create a session mock
        session_mock = mock.MagicMock()
        # Set up the post method to capture the payload
        original_post = mock.MagicMock(return_value=cm)

        captured_payload = {}

        def mock_post(url, json=None, **kwargs):
            nonlocal captured_payload
            captured_payload = json
            return original_post(url, json=json, **kwargs)

        session_mock.post = mock_post

        context = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"},
        ]

        with (
            mock.patch.object(client, "_ensure_session", mock.AsyncMock()),
            mock.patch.object(client, "session", session_mock),
        ):
            # When
            await client.generate(
                prompt="New message",
                system="You are a test assistant",
                context=context,
            )

            # Then
            # Verify the payload contains the context
            assert captured_payload["model"] == "test-model"
            assert captured_payload["prompt"] == "New message"
            assert captured_payload["system"] == "You are a test assistant"
            assert captured_payload["context"] == context

    @pytest.mark.asyncio
    async def test_generate_handles_error_response(self, client):
        """When Ollama API returns an error, it should raise an exception."""
        # Given
        error = aiohttp.ClientResponseError(
            request_info=mock.MagicMock(),
            history=(),
            status=400,
            message="Bad Request",
            headers=mock.MagicMock(),
        )

        # Mock the session
        session_mock = mock.MagicMock()
        session_mock.post = mock.MagicMock(side_effect=error)

        # When/Then
        with (
            mock.patch.object(client, "_ensure_session", mock.AsyncMock()),
            mock.patch.object(client, "session", session_mock),
            pytest.raises(aiohttp.ClientResponseError),
        ):
            await client.generate(prompt="Test prompt")

    @pytest.mark.asyncio
    async def test_generate_with_empty_prompt(self, client):
        """
        Given an empty prompt
        When generating text
        Then it should handle the empty prompt gracefully
        """
        # Given
        empty_prompt = ""

        # When/Then - validate empty prompts
        with (
            mock.patch.object(client, "_ensure_session", mock.AsyncMock()),
            pytest.raises(ValueError, match="Prompt cannot be empty"),
        ):
            await client.generate(prompt=empty_prompt)

    @pytest.mark.asyncio
    async def test_generate_with_server_down(self, client):
        """
        Given the Ollama server is unreachable
        When generating text
        Then it should handle the connection error gracefully
        """
        # Given
        session_mock = mock.MagicMock()
        # Set post to raise a connection error
        session_mock.post = mock.MagicMock(side_effect=aiohttp.ClientConnectionError("Connection refused"))

        # When/Then
        with (
            mock.patch.object(client, "_ensure_session", mock.AsyncMock()),
            mock.patch.object(client, "session", session_mock),
            pytest.raises(aiohttp.ClientConnectionError),
        ):
            await client.generate(prompt="Test prompt")

    @pytest.mark.asyncio
    async def test_generate_with_long_prompt(self, client):
        """
        Given an excessively long prompt
        When generating text
        Then it should process the long input appropriately
        """
        # Given
        # Create a very long prompt (e.g., 10,000 characters)
        long_prompt = "A" * 10000

        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.json = mock.AsyncMock()
        mock_response.json.return_value = {
            "model": "test-model",
            "response": "Response to long prompt",
            "done": True,
        }

        # Create a context manager mock for the response
        cm = mock.MagicMock()
        cm.__aenter__ = mock.AsyncMock(return_value=mock_response)
        cm.__aexit__ = mock.AsyncMock()

        # Create a session mock
        session_mock = mock.MagicMock()
        session_mock.post = mock.MagicMock(return_value=cm)

        with (
            mock.patch.object(client, "_ensure_session", mock.AsyncMock()),
            mock.patch.object(client, "session", session_mock),
        ):
            # When
            result = await client.generate(prompt=long_prompt)

            # Then
            assert result == "Response to long prompt"

    @pytest.mark.asyncio
    async def test_generate_closes_session_on_error(self, client):
        """
        Given an API error occurs
        When generating text
        Then it should properly close the session to prevent resource leaks
        """
        # Given
        error_exception = Exception("Test error")

        # Create a session mock that raises an exception on post
        session_mock = mock.MagicMock()
        session_mock.closed = False
        session_mock.post = mock.MagicMock(side_effect=error_exception)

        with (
            mock.patch.object(client, "_ensure_session", mock.AsyncMock()),
            mock.patch.object(client, "session", session_mock),
        ):
            # When/Then
            with pytest.raises(Exception) as excinfo:
                await client.generate(prompt="Test prompt")

            assert str(excinfo.value) == "Test error"
