"""Tests for the system message module."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from ollama_mcp_discord.system_message import (
    SYSTEM_MESSAGE_FILE,
    clear_system_message,
    get_system_message,
    set_system_message,
)


def test_system_message_lifecycle():
    # Backup the original system message file if it exists
    original_file = None
    if os.path.exists(SYSTEM_MESSAGE_FILE):
        original_file = SYSTEM_MESSAGE_FILE + ".bak"
        os.rename(SYSTEM_MESSAGE_FILE, original_file)

    try:
        # Test setting and getting a system message
        test_message = "This is a test system message"
        set_system_message(test_message)

        # Verify the message was set correctly
        retrieved_message = get_system_message()
        assert retrieved_message == test_message, "Retrieved system message does not match set message"

        # Test clearing the system message
        clear_system_message()

        # Verify the message was cleared
        assert get_system_message() is None, "System message was not cleared"

    finally:
        # Restore the original system message file
        if original_file:
            os.rename(original_file, SYSTEM_MESSAGE_FILE)
