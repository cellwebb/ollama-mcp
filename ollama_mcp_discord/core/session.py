"""Session management for user conversations."""

import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from ollama_mcp_discord.mcp.client import MCPClient
from ollama_mcp_discord.ollama.client import OllamaClient

logger = logging.getLogger(__name__)


class Session:
    """User session for managing conversations and MCP integrations."""

    def __init__(self, user_id: int, model_name: str, mcp_client: Optional[MCPClient] = None):
        """Initialize a new session for a user.

        Args:
            user_id: The Discord user ID
            model_name: The default Ollama model to use
            mcp_client: An initialized MCP client (optional)
        """
        self.user_id = user_id
        self.model_name = model_name
        self.conversation_id = str(uuid.uuid4())

        # Initialize clients
        self.ollama_client = OllamaClient(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"), model=model_name)
        # Use provided MCP client or create a new one
        self.mcp_client = mcp_client or MCPClient()

        # Conversation history
        self.messages: List[Dict[str, Any]] = []

    async def process_message(self, content: str) -> str:
        """Process a user message and return the AI response.

        Args:
            content: The user message

        Returns:
            The AI's response
        """
        # Add user message to history
        self.messages.append({"role": "user", "content": content})

        # Generate response with MCP capabilities
        response = await self._generate_response(content)

        # Add AI response to history
        self.messages.append({"role": "assistant", "content": response})

        return response

    async def set_model(self, model_name: str) -> None:
        """Change the Ollama model being used.

        Args:
            model_name: The name of the model to use
        """
        # Check if model exists
        models = await self.ollama_client.list_models()
        if model_name not in [model["name"] for model in models]:
            raise ValueError(f"Model '{model_name}' not found")

        # Update model
        self.model_name = model_name
        self.ollama_client.model = model_name

        logger.info(f"Changed model to {model_name} for user {self.user_id}")

    async def create_memory(self, content: str) -> str:
        """Create a memory item.

        Args:
            content: The content to store in memory

        Returns:
            The memory ID
        """
        memory_id = str(uuid.uuid4())

        # Create memory entity
        await self.mcp_client.create_memory_entity(name=memory_id, entity_type="UserMemory", observations=[content])

        return memory_id

    async def _generate_response(self, user_message: str) -> str:
        """Generate a response using Ollama with MCP capabilities.

        Args:
            user_message: The user's message

        Returns:
            The generated response
        """
        # Build prompt with MCP tool context
        system_prompt = (
            "You are an AI assistant with access to the following tools:\n"
            "- Memory: Store and retrieve information\n"
            "- Fetch: Get information from the web\n"
            "- Puppeteer: Control a browser\n"
            "- Sequential Thinking: Break down complex problems\n\n"
            "The user can interact with you using these commands:\n"
            "!chat - Chat with you directly\n"
            "!model <name> - Change the AI model\n"
            "!remember <content> - Store something in memory\n"
            "!help - Show all available commands"
        )

        # Get conversation history formatted for Ollama
        history = self._format_conversation_history()

        # Generate response with Ollama
        response = await self.ollama_client.generate(prompt=user_message, system=system_prompt, context=history)

        return response

    def _format_conversation_history(self) -> List[Any]:
        """Format the conversation history for Ollama.

        Returns:
            The formatted history
        """
        # Only include the most recent messages to stay within context limits
        recent_messages = self.messages[-10:] if len(self.messages) > 10 else self.messages

        return recent_messages
