"""Parser for Claude conversation export format."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..models import Conversation, Message


def parse_claude_export(file_path: Path) -> list[Conversation]:
    """Parse Claude's JSON export file.

    Claude exports as a JSON array of conversations, each with:
    - uuid: conversation id
    - name: conversation title
    - created_at / updated_at: ISO timestamps
    - chat_messages: list of {sender, text, created_at}
    """
    with open(file_path) as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]

    conversations = []
    for item in data:
        messages = []
        for msg in item.get("chat_messages", []):
            role = msg.get("sender", "unknown")
            if role == "human":
                role = "user"
            elif role == "assistant":
                role = "assistant"
            else:
                continue

            text = msg.get("text", "")
            if not text.strip():
                continue

            ts = None
            if msg.get("created_at"):
                try:
                    ts = datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            messages.append(Message(role=role, content=text, timestamp=ts))

        if not messages:
            continue

        created = None
        if item.get("created_at"):
            try:
                created = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        updated = None
        if item.get("updated_at"):
            try:
                updated = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        conv = Conversation(
            id=item.get("uuid", ""),
            title=item.get("name", "Untitled"),
            platform="claude",
            messages=messages,
            created_at=created,
            updated_at=updated,
        )
        conversations.append(conv)

    return conversations
