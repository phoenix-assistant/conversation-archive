"""Parser for ChatGPT JSON export format."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..models import Conversation, Message


def parse_chatgpt_export(file_path: Path) -> list[Conversation]:
    """Parse ChatGPT's conversations.json export file."""
    with open(file_path) as f:
        data = json.load(f)

    conversations = []
    for item in data:
        messages = _extract_messages(item)
        if not messages:
            continue

        created = datetime.fromtimestamp(item["create_time"]) if item.get("create_time") else None
        updated = datetime.fromtimestamp(item["update_time"]) if item.get("update_time") else None

        conv = Conversation(
            id=item.get("id", ""),
            title=item.get("title", "Untitled"),
            platform="chatgpt",
            messages=messages,
            created_at=created,
            updated_at=updated,
            metadata={"model": item.get("default_model_slug", "")},
        )
        conversations.append(conv)

    return conversations


def _extract_messages(item: dict) -> list[Message]:
    """Extract messages from ChatGPT's nested mapping structure."""
    messages = []
    mapping = item.get("mapping", {})

    # Build ordered list from the tree
    nodes = []
    for node_id, node in mapping.items():
        msg = node.get("message")
        if not msg:
            continue
        author = msg.get("author", {}).get("role", "unknown")
        if author not in ("user", "assistant", "system"):
            continue
        content_parts = msg.get("content", {}).get("parts", [])
        text = "\n".join(str(p) for p in content_parts if isinstance(p, str))
        if not text.strip():
            continue
        ts = msg.get("create_time")
        timestamp = datetime.fromtimestamp(ts) if ts else None
        nodes.append((ts or 0, Message(role=author, content=text, timestamp=timestamp)))

    nodes.sort(key=lambda x: x[0])
    return [n[1] for n in nodes]
