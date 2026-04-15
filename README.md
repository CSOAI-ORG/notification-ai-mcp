# Notification AI

> By [MEOK AI Labs](https://meok.ai) — Send notifications via webhooks

## Installation

```bash
pip install notification-ai-mcp
```

## Usage

```bash
python server.py
```

## Tools

### `send_webhook`
Send a webhook notification to a specified URL.

**Parameters:**
- `url` (str): Webhook URL
- `payload` (str): JSON payload to send

### `send_desktop_notification`
Send a desktop notification.

**Parameters:**
- `title` (str): Notification title
- `message` (str): Notification message

### `schedule_notification`
Schedule a notification to be sent after a delay.

**Parameters:**
- `message` (str): Notification message
- `delay_seconds` (int): Delay in seconds (default: 60)

### `list_notification_history`
List recent notification history.

**Parameters:**
- `limit` (int): Maximum entries to return (default: 10)

## Authentication

Free tier: 30 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## License

MIT — MEOK AI Labs
