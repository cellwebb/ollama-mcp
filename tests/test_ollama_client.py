"""Tests for the OllamaClient class."""

import json
from unittest import mock

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
        mock_response = mock.AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3", "modified_at": "2023-06-01T12:00:00Z"},
                {"name": "mistral", "modified_at": "2023-05-30T10:30:00Z"},
            ]
        }

        with mock.patch("aiohttp.ClientSession.get", return_value=mock_response):
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
        mock_response = mock.AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "model": "test-model",
            "response": "This is a test response",
            "done": True,
        }

        with mock.patch("aiohttp.ClientSession.post", return_value=mock_response):
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
        mock_post = mock.AsyncMock()
        mock_post.return_value.__aenter__.return_value.status = 200
        mock_post.return_value.__aenter__.return_value.json.return_value = {
            "model": "test-model",
            "response": "Response with context",
            "done": True,
        }

        context = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"},
        ]

        with mock.patch("aiohttp.ClientSession.post", mock_post):
            # When
            await client.generate(
                prompt="New message",
                system="You are a test assistant",
                context=context,
            )

            # Then
            # Extract the payload from the call
            call_args = mock_post.call_args
            assert call_args is not None

            # Verify the payload contains the context
            payload = json.loads(call_args[1]["json"])
            assert payload["model"] == "test-model"
            assert payload["prompt"] == "New message"
            assert payload["system"] == "You are a test assistant"
            assert payload["context"] == context

    @pytest.mark.asyncio
    async def test_generate_handles_error_response(self, client):
        """When Ollama API returns an error, it should raise an exception."""
        # Given
        mock_response = mock.AsyncMock()
        mock_response.status = 400
        mock_response.json.return_value = {"error": "Invalid model"}
        mock_response.text.return_value = "Invalid model"

        with (
            mock.patch("aiohttp.ClientSession.post", return_value=mock_response),
            pytest.raises(ValueError, match="Error from Ollama API: Invalid model"),
        ):
            # When/Then
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

        # When/Then
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            await client.generate(prompt=empty_prompt)

    @pytest.mark.asyncio
    async def test_generate_with_server_down(self, client):
        """
        Given the Ollama server is unreachable
        When generating text
        Then it should handle the connection error gracefully
        """
        # Given
        import aiohttp

        # Mock a connection error
        with mock.patch(
            "aiohttp.ClientSession.post",
            side_effect=aiohttp.ClientConnectionError("Connection refused"),
        ):
            # When/Then
            with pytest.raises(ConnectionError, match="Failed to connect to Ollama API"):
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

        mock_response = mock.AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "model": "test-model",
            "response": "Response to long prompt",
            "done": True,
        }

        with mock.patch("aiohttp.ClientSession.post", return_value=mock_response):
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
        mock_session = mock.MagicMock()
        mock_session.__aenter__ = mock.AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = mock.AsyncMock()
        mock_session.post = mock.AsyncMock()

        # Set up post to raise an exception
        mock_post_cm = mock.MagicMock()
        mock_post_cm.__aenter__ = mock.AsyncMock(side_effect=Exception("Test error"))
        mock_post_cm.__aexit__ = mock.AsyncMock()
        mock_session.post.return_value = mock_post_cm

        # Replace client session creation
        with mock.patch("aiohttp.ClientSession", return_value=mock_session):
            # When/Then
            with pytest.raises(Exception):
                await client.generate(prompt="Test prompt")

            # Verify session was closed properly
            mock_session.__aexit__.assert_called_once()
