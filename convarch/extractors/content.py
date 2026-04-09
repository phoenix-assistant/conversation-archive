"""Extract structured content from conversation messages."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..models import Conversation


@dataclass
class CodeBlock:
    language: str
    code: str
    context: str  # surrounding text


@dataclass
class ActionItem:
    text: str
    source_role: str


def extract_code_blocks(conv: Conversation) -> list[CodeBlock]:
    """Extract fenced code blocks from conversation messages."""
    blocks = []
    pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
    for msg in conv.messages:
        for match in pattern.finditer(msg.content):
            lang = match.group(1) or "text"
            code = match.group(2).strip()
            # Get ~50 chars of context before the code block
            start = max(0, match.start() - 50)
            context = msg.content[start:match.start()].strip()
            blocks.append(CodeBlock(language=lang, code=code, context=context))
    return blocks


def extract_action_items(conv: Conversation) -> list[ActionItem]:
    """Extract action items / TODOs from conversation messages."""
    items = []
    patterns = [
        re.compile(r"(?:TODO|Action item|Next step|You should|I recommend)[:\s]+(.+?)(?:\n|$)", re.IGNORECASE),
        re.compile(r"^\s*[-*]\s+\[[ x]\]\s+(.+)$", re.MULTILINE),
        re.compile(r"^\d+\.\s+(.+?)(?:\n|$)", re.MULTILINE),
    ]
    for msg in conv.messages:
        if msg.role != "assistant":
            continue
        for pattern in patterns[:2]:  # Only TODO patterns and checkboxes
            for match in pattern.finditer(msg.content):
                text = match.group(1).strip()
                if len(text) > 10:  # Filter out noise
                    items.append(ActionItem(text=text, source_role=msg.role))
    return items


def extract_key_decisions(conv: Conversation) -> list[str]:
    """Extract key decisions or conclusions from conversation."""
    decisions = []
    decision_patterns = [
        re.compile(r"(?:decision|conclusion|summary|key takeaway|in summary)[:\s]+(.+?)(?:\n\n|$)", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:we decided|the answer is|the solution is|you should use)[:\s]+(.+?)(?:\n|$)", re.IGNORECASE),
    ]
    for msg in conv.messages:
        if msg.role != "assistant":
            continue
        for pattern in decision_patterns:
            for match in pattern.finditer(msg.content):
                text = match.group(1).strip()
                if len(text) > 15:
                    decisions.append(text[:200])
    return decisions
