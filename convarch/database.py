"""SQLite database layer for conversation storage and search."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

from .models import Conversation, Message

DEFAULT_DB = Path.home() / ".convarch" / "convarch.db"


class Database:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                platform TEXT NOT NULL DEFAULT 'unknown',
                created_at TEXT,
                updated_at TEXT,
                tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                full_text TEXT DEFAULT '',
                embedding BLOB
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT,
                position INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
            CREATE INDEX IF NOT EXISTS idx_conv_platform ON conversations(platform);
            CREATE INDEX IF NOT EXISTS idx_conv_created ON conversations(created_at);
            CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id);
        """)
        self.conn.commit()

    def save_conversation(self, conv: Conversation, embedding: Optional[np.ndarray] = None):
        emb_blob = embedding.tobytes() if embedding is not None else None
        self.conn.execute(
            """INSERT OR REPLACE INTO conversations
               (id, title, platform, created_at, updated_at, tags, metadata, full_text, embedding)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                conv.id, conv.title, conv.platform,
                conv.created_at.isoformat() if conv.created_at else None,
                conv.updated_at.isoformat() if conv.updated_at else None,
                json.dumps(conv.tags), json.dumps(conv.metadata),
                conv.full_text, emb_blob,
            ),
        )
        self.conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv.id,))
        for i, msg in enumerate(conv.messages):
            self.conn.execute(
                "INSERT INTO messages (conversation_id, role, content, timestamp, position) VALUES (?, ?, ?, ?, ?)",
                (conv.id, msg.role, msg.content,
                 msg.timestamp.isoformat() if msg.timestamp else None, i),
            )
        self.conn.commit()

    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        row = self.conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
        if not row:
            return None
        return self._row_to_conversation(row)

    def list_conversations(
        self, platform: Optional[str] = None, after: Optional[str] = None,
        limit: int = 50, offset: int = 0,
    ) -> list[Conversation]:
        query = "SELECT * FROM conversations WHERE 1=1"
        params: list = []
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        if after:
            query += " AND created_at >= ?"
            params.append(after)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_conversation(r) for r in rows]

    def get_all_embeddings(self) -> list[tuple[str, np.ndarray]]:
        rows = self.conn.execute(
            "SELECT id, embedding FROM conversations WHERE embedding IS NOT NULL"
        ).fetchall()
        results = []
        for r in rows:
            emb = np.frombuffer(r["embedding"], dtype=np.float32)
            results.append((r["id"], emb))
        return results

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]

    def delete_conversation(self, conv_id: str):
        self.conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
        self.conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        self.conn.commit()

    def _row_to_conversation(self, row) -> Conversation:
        msgs = self.conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY position",
            (row["id"],),
        ).fetchall()
        return Conversation(
            id=row["id"],
            title=row["title"],
            platform=row["platform"],
            messages=[
                Message(
                    role=m["role"], content=m["content"],
                    timestamp=datetime.fromisoformat(m["timestamp"]) if m["timestamp"] else None,
                )
                for m in msgs
            ],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    def close(self):
        self.conn.close()
