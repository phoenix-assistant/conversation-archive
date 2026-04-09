"""Tests for conversation-archive."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

from convarch.database import Database
from convarch.export import export_json, export_markdown
from convarch.extractors.content import (
    extract_action_items,
    extract_code_blocks,
    extract_key_decisions,
)
from convarch.models import Conversation, Message
from convarch.parsers.chatgpt import parse_chatgpt_export
from convarch.parsers.claude import parse_claude_export


# --- Fixtures ---

@pytest.fixture
def tmp_db(tmp_path):
    db = Database(tmp_path / "test.db")
    yield db
    db.close()


@pytest.fixture
def sample_conv():
    return Conversation(
        id="test-123",
        title="Python CSV Help",
        platform="chatgpt",
        messages=[
            Message(role="user", content="How do I parse CSV in Python?"),
            Message(role="assistant", content="Use the `csv` module:\n```python\nimport csv\nwith open('file.csv') as f:\n    reader = csv.reader(f)\n    for row in reader:\n        print(row)\n```\nYou should also consider pandas for larger files."),
        ],
        created_at=datetime(2026, 1, 15, 10, 30),
        updated_at=datetime(2026, 1, 15, 10, 35),
        tags=["python", "csv"],
    )


# --- Model tests ---

def test_message_to_dict():
    msg = Message(role="user", content="hello", timestamp=datetime(2026, 1, 1))
    d = msg.to_dict()
    assert d["role"] == "user"
    assert d["content"] == "hello"
    assert "2026" in d["timestamp"]


def test_conversation_full_text(sample_conv):
    text = sample_conv.full_text
    assert "[user]:" in text
    assert "CSV" in text


def test_conversation_to_dict(sample_conv):
    d = sample_conv.to_dict()
    assert d["id"] == "test-123"
    assert len(d["messages"]) == 2
    assert d["platform"] == "chatgpt"


# --- Database tests ---

def test_db_save_and_get(tmp_db, sample_conv):
    emb = np.random.randn(384).astype(np.float32)
    tmp_db.save_conversation(sample_conv, emb)
    retrieved = tmp_db.get_conversation("test-123")
    assert retrieved is not None
    assert retrieved.title == "Python CSV Help"
    assert len(retrieved.messages) == 2


def test_db_list_conversations(tmp_db, sample_conv):
    tmp_db.save_conversation(sample_conv)
    convs = tmp_db.list_conversations()
    assert len(convs) == 1
    assert convs[0].platform == "chatgpt"


def test_db_list_by_platform(tmp_db, sample_conv):
    tmp_db.save_conversation(sample_conv)
    assert len(tmp_db.list_conversations(platform="chatgpt")) == 1
    assert len(tmp_db.list_conversations(platform="claude")) == 0


def test_db_count(tmp_db, sample_conv):
    assert tmp_db.count() == 0
    tmp_db.save_conversation(sample_conv)
    assert tmp_db.count() == 1


def test_db_delete(tmp_db, sample_conv):
    tmp_db.save_conversation(sample_conv)
    tmp_db.delete_conversation("test-123")
    assert tmp_db.count() == 0


def test_db_embeddings(tmp_db, sample_conv):
    emb = np.ones(384, dtype=np.float32)
    tmp_db.save_conversation(sample_conv, emb)
    results = tmp_db.get_all_embeddings()
    assert len(results) == 1
    assert results[0][0] == "test-123"
    np.testing.assert_array_almost_equal(results[0][1], emb)


# --- Parser tests ---

def test_chatgpt_parser(tmp_path):
    data = [{
        "id": "conv-1",
        "title": "Test Chat",
        "create_time": 1700000000,
        "update_time": 1700000100,
        "default_model_slug": "gpt-4",
        "mapping": {
            "node-1": {
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["Hello"]},
                    "create_time": 1700000000,
                }
            },
            "node-2": {
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["Hi there!"]},
                    "create_time": 1700000050,
                }
            },
        },
    }]
    f = tmp_path / "chatgpt.json"
    f.write_text(json.dumps(data))
    convs = parse_chatgpt_export(f)
    assert len(convs) == 1
    assert convs[0].platform == "chatgpt"
    assert len(convs[0].messages) == 2


def test_claude_parser(tmp_path):
    data = [{
        "uuid": "conv-c1",
        "name": "Claude Test",
        "created_at": "2026-01-15T10:00:00Z",
        "updated_at": "2026-01-15T10:05:00Z",
        "chat_messages": [
            {"sender": "human", "text": "Hello Claude", "created_at": "2026-01-15T10:00:00Z"},
            {"sender": "assistant", "text": "Hello!", "created_at": "2026-01-15T10:00:05Z"},
        ],
    }]
    f = tmp_path / "claude.json"
    f.write_text(json.dumps(data))
    convs = parse_claude_export(f)
    assert len(convs) == 1
    assert convs[0].platform == "claude"
    assert convs[0].messages[0].role == "user"


# --- Extractor tests ---

def test_extract_code_blocks(sample_conv):
    blocks = extract_code_blocks(sample_conv)
    assert len(blocks) == 1
    assert blocks[0].language == "python"
    assert "csv" in blocks[0].code


def test_extract_action_items(sample_conv):
    items = extract_action_items(sample_conv)
    assert len(items) >= 1
    assert any("pandas" in item.text.lower() for item in items)


# --- Export tests ---

def test_export_markdown(tmp_path, sample_conv):
    export_markdown([sample_conv], tmp_path / "export")
    files = list((tmp_path / "export").glob("*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "Python CSV Help" in content


def test_export_json(tmp_path, sample_conv):
    out = tmp_path / "export.json"
    export_json([sample_conv], out)
    data = json.loads(out.read_text())
    assert len(data) == 1
    assert data[0]["title"] == "Python CSV Help"
