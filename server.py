#!/usr/bin/env python3
"""In-memory notification system with channels, priorities, and history. — MEOK AI Labs."""

import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import json, hashlib
from datetime import datetime, timezone
from collections import defaultdict, deque
from mcp.server.fastmcp import FastMCP

FREE_DAILY_LIMIT = 30
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now - t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT:
        return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day. Upgrade: meok.ai"})
    _usage[c].append(now)
    return None

mcp = FastMCP("notification-ai", instructions="In-memory notification system with channels, priorities, and history. By MEOK AI Labs.")

MAX_NOTIFICATIONS = 500
_notifications = deque(maxlen=MAX_NOTIFICATIONS)
_preferences = defaultdict(lambda: {
    "channels": {"info": True, "warning": True, "error": True, "success": True},
    "quiet_hours": None,
    "max_per_hour": 60,
})

VALID_PRIORITIES = ["low", "normal", "high", "urgent"]
VALID_CHANNELS = ["info", "warning", "error", "success", "system"]


def _notif_id() -> str:
    return hashlib.md5(f"{datetime.now(timezone.utc).isoformat()}{len(_notifications)}".encode()).hexdigest()[:12]


@mcp.tool()
def send_notification(title: str, message: str, channel: str = "info", priority: str = "normal", tags: str = "", recipient: str = "default", api_key: str = "") -> str:
    """Send a notification with title, message, channel (info/warning/error/success/system), and priority (low/normal/high/urgent)."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl():
        return err

    channel = channel.lower().strip()
    priority = priority.lower().strip()

    if channel not in VALID_CHANNELS:
        return json.dumps({"error": f"Invalid channel '{channel}'. Use: {', '.join(VALID_CHANNELS)}"})
    if priority not in VALID_PRIORITIES:
        return json.dumps({"error": f"Invalid priority '{priority}'. Use: {', '.join(VALID_PRIORITIES)}"})

    prefs = _preferences[recipient]
    if not prefs["channels"].get(channel, True):
        return json.dumps({"status": "suppressed", "reason": f"Channel '{channel}' is muted for recipient '{recipient}'"})

    now = datetime.now(timezone.utc)
    recent_count = sum(1 for n in _notifications if n["recipient"] == recipient and (now - datetime.fromisoformat(n["created_at"])).total_seconds() < 3600)
    if recent_count >= prefs["max_per_hour"]:
        return json.dumps({"status": "rate_limited", "reason": f"Exceeded {prefs['max_per_hour']}/hour limit"})

    tag_list = [t.strip() for t in tags.split(',') if t.strip()] if tags else []
    nid = _notif_id()

    notification = {
        "id": nid,
        "title": title,
        "message": message,
        "channel": channel,
        "priority": priority,
        "tags": tag_list,
        "recipient": recipient,
        "read": False,
        "created_at": now.isoformat(),
    }
    _notifications.appendleft(notification)

    return json.dumps({
        "status": "sent",
        "notification_id": nid,
        "channel": channel,
        "priority": priority,
        "recipient": recipient,
        "title": title[:60],
        "total_pending": sum(1 for n in _notifications if n["recipient"] == recipient and not n["read"]),
        "timestamp": now.isoformat(),
    })


@mcp.tool()
def list_notifications(recipient: str = "default", channel: str = "", unread_only: bool = False, limit: int = 20, api_key: str = "") -> str:
    """List notifications for a recipient, optionally filtered by channel and read status."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl():
        return err

    limit = max(1, min(limit, 100))
    items = [n for n in _notifications if n["recipient"] == recipient]

    if channel:
        channel = channel.lower().strip()
        items = [n for n in items if n["channel"] == channel]
    if unread_only:
        items = [n for n in items if not n["read"]]

    items = items[:limit]

    summary = defaultdict(int)
    unread_count = 0
    for n in _notifications:
        if n["recipient"] == recipient:
            summary[n["channel"]] += 1
            if not n["read"]:
                unread_count += 1

    return json.dumps({
        "recipient": recipient,
        "total": len(items),
        "unread_total": unread_count,
        "channel_filter": channel or None,
        "unread_only": unread_only,
        "notifications": [{
            "id": n["id"],
            "title": n["title"],
            "message": n["message"][:120] + ("..." if len(n["message"]) > 120 else ""),
            "channel": n["channel"],
            "priority": n["priority"],
            "tags": n["tags"],
            "read": n["read"],
            "created_at": n["created_at"],
        } for n in items],
        "summary_by_channel": dict(summary),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@mcp.tool()
def mark_read(notification_ids: str = "", mark_all: bool = False, recipient: str = "default", api_key: str = "") -> str:
    """Mark notifications as read. Provide comma-separated IDs or set mark_all=true."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl():
        return err

    marked = 0
    not_found = []

    if mark_all:
        for n in _notifications:
            if n["recipient"] == recipient and not n["read"]:
                n["read"] = True
                marked += 1
    elif notification_ids:
        ids = [nid.strip() for nid in notification_ids.split(',') if nid.strip()]
        id_set = set(ids)
        for n in _notifications:
            if n["id"] in id_set and not n["read"]:
                n["read"] = True
                marked += 1
                id_set.discard(n["id"])
        not_found = list(id_set)

    unread_remaining = sum(1 for n in _notifications if n["recipient"] == recipient and not n["read"])

    return json.dumps({
        "status": "ok",
        "marked_read": marked,
        "not_found": not_found if not_found else None,
        "unread_remaining": unread_remaining,
        "recipient": recipient,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@mcp.tool()
def get_preferences(recipient: str = "default", update_json: str = "", api_key: str = "") -> str:
    """Get or update notification preferences. Update with JSON: {\"channels\": {\"info\": true, \"warning\": false}, \"max_per_hour\": 30}."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl():
        return err

    prefs = _preferences[recipient]

    if update_json:
        try:
            updates = json.loads(update_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON for preferences update"})

        if "channels" in updates and isinstance(updates["channels"], dict):
            for ch, enabled in updates["channels"].items():
                if ch in VALID_CHANNELS:
                    prefs["channels"][ch] = bool(enabled)

        if "max_per_hour" in updates:
            prefs["max_per_hour"] = max(1, min(int(updates["max_per_hour"]), 1000))

        if "quiet_hours" in updates:
            prefs["quiet_hours"] = updates["quiet_hours"]

    total_for_recipient = sum(1 for n in _notifications if n["recipient"] == recipient)
    unread = sum(1 for n in _notifications if n["recipient"] == recipient and not n["read"])

    channel_counts = defaultdict(int)
    for n in _notifications:
        if n["recipient"] == recipient:
            channel_counts[n["channel"]] += 1

    return json.dumps({
        "recipient": recipient,
        "preferences": {
            "channels": prefs["channels"],
            "max_per_hour": prefs["max_per_hour"],
            "quiet_hours": prefs["quiet_hours"],
        },
        "stats": {
            "total_notifications": total_for_recipient,
            "unread": unread,
            "by_channel": dict(channel_counts),
        },
        "available_channels": VALID_CHANNELS,
        "available_priorities": VALID_PRIORITIES,
        "updated": bool(update_json),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


if __name__ == "__main__":
    mcp.run()
