"""
System message management for the Ollama-MCP Discord bot.

This module provides functions to set, get, and clear a persistent system message
that can be used to guide the behavior of the AI model across different conversations.
"""

import json
import os
from typing import Optional

SYSTEM_MESSAGE_FILE = os.path.expanduser("~/.mcp_system_message.json")


def get_system_message() -> Optional[str]:
    """
    Retrieve the current system message.

    Returns:
        Optional[str]: The current system message, or None if not set.
    """
    try:
        with open(SYSTEM_MESSAGE_FILE, "r") as f:
            data = json.load(f)
            return data.get("system_message")
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def set_system_message(message: str) -> None:
    """
    Set the system message and save it to a file.

    Args:
        message (str): The system message to set.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(SYSTEM_MESSAGE_FILE), exist_ok=True)

    # Save the system message
    with open(SYSTEM_MESSAGE_FILE, "w") as f:
        json.dump({"system_message": message}, f, indent=2)


def clear_system_message() -> None:
    """
    Clear the current system message.
    """
    try:
        os.remove(SYSTEM_MESSAGE_FILE)
    except FileNotFoundError:
        pass  # Already cleared
