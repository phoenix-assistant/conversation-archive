"""Export conversations to Markdown or JSON."""

from __future__ import annotations

import json
from pathlib import Path

from .models import Conversation


def export_markdown(conversations: list[Conversation], output_dir: Path):
    """Export conversations as individual Markdown files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for conv in conversations:
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in conv.title)[:80]
        filename = f"{conv.platform}_{safe_title}_{conv.id[:8]}.md"
        filepath = output_dir / filename

        lines = [f"# {conv.title}\n"]
        lines.append(f"**Platform:** {conv.platform}")
        if conv.created_at:
            lines.append(f"**Date:** {conv.created_at.strftime('%Y-%m-%d %H:%M')}")
        if conv.tags:
            lines.append(f"**Tags:** {', '.join(conv.tags)}")
        lines.append("\n---\n")

        for msg in conv.messages:
            role_label = "🧑 User" if msg.role == "user" else "🤖 Assistant"
            lines.append(f"### {role_label}\n")
            lines.append(msg.content)
            lines.append("")

        filepath.write_text("\n".join(lines))


def export_json(conversations: list[Conversation], output_path: Path):
    """Export conversations as a single JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = [conv.to_dict() for conv in conversations]
    output_path.write_text(json.dumps(data, indent=2, default=str))
