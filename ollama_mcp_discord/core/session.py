"""Session management for user conversations."""

import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from ollama_mcp_discord.mcp.client import MCPClient
from ollama_mcp_discord.ollama.client import OllamaClient
from ollama_mcp_discord.system_message import get_system_message

logger = logging.getLogger(__name__)


class Session:
    """User session for managing conversations and MCP integrations."""

    def __init__(
        self,
        user_id: int,
        model_name: str,
        ollama_client: Optional[OllamaClient] = None,
        mcp_client: Optional[MCPClient] = None,
    ):
        """Initialize a new session for a user.

        Args:
            user_id: The Discord user ID
            model_name: The default Ollama model to use
            ollama_client: An initialized Ollama client (optional)
            mcp_client: An initialized MCP client (optional)
        """
        self.user_id = user_id
        self.model_name = model_name
        self.conversation_id = str(uuid.uuid4())

        # Initialize clients
        self.ollama_client = ollama_client or OllamaClient(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"), model=model_name
        )
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

        # Trim message history to keep only the most recent messages (max 10)
        max_capacity = 10
        if len(self.messages) > max_capacity:
            # Remove oldest messages to stay within capacity
            self.messages = self.messages[-max_capacity:]

        return response

    async def set_model(self, model_name: str) -> None:
        """Set the Ollama model to use.

        Args:
            model_name: The name of the model to use

        Raises:
            ValueError: If the model doesn't exist
        """
        try:
            # Validate that the model exists
            models = await self.ollama_client.list_models()
            valid_models = [model["name"] for model in models]

            if model_name not in valid_models:
                raise ValueError(f"Model '{model_name}' not found")

            # Set the model
            self.model_name = model_name
            self.ollama_client.model = model_name
            logger.info(f"Changed model to {model_name} for user {self.user_id}")

        except Exception as e:
            logger.error(f"Error setting model: {e}")
            raise

    async def create_memory(self, content: str) -> str:
        """Create a memory item.

        Args:
            content: The content to store in memory

        Returns:
            The memory ID

        Raises:
            ValueError: If content is empty
        """
        if not content or content.strip() == "":
            raise ValueError("Memory content cannot be empty")

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
        try:
            # Get system message from file or use default
            custom_system_message = get_system_message()
            system_prompt = custom_system_message or "You are a helpful assistant."

            # Get conversation history formatted for Ollama
            history = self._format_conversation_history()

            # Log for debugging
            logger.debug(f"Generating response with model: {self.model_name}")
            logger.debug(f"System prompt: {system_prompt}")
            logger.debug(f"User message: {user_message}")
            logger.debug(f"History length: {len(history)}")

            # Generate response with Ollama
            response = await self.ollama_client.generate(prompt=user_message, system=system_prompt, context=history)

            logger.debug(f"Generated response length: {len(response)}")
            return response

        except Exception as e:
            logger.error(f"Error in _generate_response: {e}", exc_info=True)
            raise

    def _format_conversation_history(self) -> List[Any]:
        """Format the conversation history for Ollama.

        Returns:
            The formatted history
        """
        # Only include the most recent messages to stay within context limits
        recent_messages = self.messages[-10:] if len(self.messages) > 10 else self.messages

        return recent_messages

    async def sequential_thinking(self, initial_thought: str) -> Dict[str, Any]:
        """Perform sequential thinking through the MCP client.

        Args:
            initial_thought: The initial thought to start the thinking process

        Returns:
            The final thinking result
        """
        if not initial_thought or initial_thought.strip() == "":
            raise ValueError("Initial thought cannot be empty")

        # Use the MCP client to perform sequential thinking
        current_thought_dict = {
            "thought": initial_thought,
            "thoughtNumber": 1,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
        }
        current_result = None

        # Continue thinking until no more thoughts are needed
        while True:
            # Process the current thought
            current_result = await self.mcp_client.sequential_thinking(current_thought_dict)

            # Check if thinking is complete
            if not current_result.get("nextThoughtNeeded", False):
                break

            # Update the current thought for the next iteration
            current_thought_dict = current_result

        return current_result
