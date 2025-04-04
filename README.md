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

## MCP Server Configuration

The Ollama-MCP Discord bot can interact with various MCP servers. To configure these servers, create a `mcp.json` file in the project root with the following structure:

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": "/Users/cell/.windsurf-memory.json"
      }
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    },
    "mcp-puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "env": {
        "PUPPETEER_LAUNCH_OPTIONS": "{ \"headless\": false}",
        "ALLOW_DANGEROUS": "true"
      }
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

### Starting the Bot

To start the bot, run the following command:

```bash
python -m ollama_mcp_discord
```

The bot will automatically start the configured MCP servers.

### Environment Variables

- `DISCORD_TOKEN`: Required for the Discord bot to authenticate.
- `MCP_CONFIG_PATH`: Optional path to the MCP configuration file (default: `mcp.json`).

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
