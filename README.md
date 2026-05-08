<div align="center">

# Notification Ai MCP

**MCP server for notification ai mcp operations**

[![PyPI](https://img.shields.io/pypi/v/meok-notification-ai-mcp)](https://pypi.org/project/meok-notification-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Notification Ai MCP provides AI-powered tools via the Model Context Protocol (MCP).

## Tools

| Tool | Description |
|------|-------------|
| `send_notification` | Send a notification with title, message, channel (info/warning/error/success/sys |
| `list_notifications` | List notifications for a recipient, optionally filtered by channel and read stat |
| `mark_read` | Mark notifications as read. Provide comma-separated IDs or set mark_all=true. |
| `get_preferences` | Get or update notification preferences. Update with JSON: {\"channels\": {\"info |

## Installation

```bash
pip install meok-notification-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "notification-ai": {
      "command": "python",
      "args": ["-m", "meok_notification_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 4 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
