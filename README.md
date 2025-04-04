# Ollama-MCP Discord Bot

A Python project that connects Ollama to Model Context Protocol (MCP) servers and allows users to interact with AI models through Discord.

## Features

- Connect to local Ollama models
- Access MCP capabilities (memory, fetch, puppeteer, sequential thinking)
- User-friendly Discord bot interface with text commands
- Respond to specific trigger words in normal messages
- Multi-user conversation support
- Configurable model selection

## Quick Start

1. Clone this repository
2. Install dependencies: `uv pip install -r requirements.txt`
3. Configure environment variables in `.env`
4. Start the bot: `python -m ollama_mcp_discord`

## Configuration

Create a `.env` file with the following variables:

```bash
DISCORD_TOKEN=your_discord_bot_token
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=llama3
```

## Usage

Once the bot is running, you can interact with it in Discord using text commands:

```text
!chat What's the weather like today?
!model llama3
!remember Create a new memory item
!trigger add keyword Your custom response
!trigger remove keyword
!triggers
!help
```

The bot will also automatically respond to certain words in normal conversation:

- When someone says "hello" in chat, the bot will respond
- You can add or remove trigger words with the `!trigger` command

## Development

Check the ROADMAP.md file for implementation status and upcoming features.
