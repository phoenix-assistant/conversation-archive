"""FastAPI web API for conversation-archive."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .database import Database
from .models import Conversation, Message

app = FastAPI(title="Conversation Archive", version="0.1.0")

_db: Optional[Database] = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10


class SearchResult(BaseModel):
    id: str
    title: str
    platform: str
    score: float
    message_count: int
    created_at: Optional[str] = None


@app.get("/")
def root():
    return HTMLResponse("""
    <html><head><title>Conversation Archive</title>
    <style>
        body { font-family: system-ui; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        input { width: 100%; padding: 0.5rem; font-size: 1.1rem; margin: 1rem 0; }
        .result { border: 1px solid #ddd; padding: 1rem; margin: 0.5rem 0; border-radius: 4px; }
        .score { color: #666; font-size: 0.9rem; }
    </style></head>
    <body>
        <h1>🗂️ Conversation Archive</h1>
        <input type="text" id="q" placeholder="Search your conversations..." onkeyup="if(event.key==='Enter')search()">
        <div id="results"></div>
        <script>
        async function search() {
            const q = document.getElementById('q').value;
            const r = await fetch('/api/search?query=' + encodeURIComponent(q));
            const data = await r.json();
            document.getElementById('results').innerHTML = data.map(d =>
                `<div class="result"><strong>${d.title}</strong> <span class="score">(${d.score.toFixed(3)})</span><br>
                 <small>${d.platform} · ${d.message_count} messages · ${d.created_at || '—'}</small></div>`
            ).join('');
        }
        </script>
    </body></html>
    """)


@app.get("/api/conversations")
def list_conversations(
    platform: Optional[str] = None,
    after: Optional[str] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
):
    db = get_db()
    convs = db.list_conversations(platform=platform, after=after, limit=limit, offset=offset)
    return [c.to_dict() for c in convs]


@app.get("/api/conversations/{conv_id}")
def get_conversation(conv_id: str):
    db = get_db()
    conv = db.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv.to_dict()


@app.get("/api/search")
def search_conversations(query: str, top_k: int = Query(default=10, le=100)):
    from .search import search

    db = get_db()
    results = search(db, query, top_k=top_k)
    return [
        SearchResult(
            id=conv.id, title=conv.title, platform=conv.platform,
            score=score, message_count=len(conv.messages),
            created_at=conv.created_at.isoformat() if conv.created_at else None,
        ).model_dump()
        for conv, score in results
    ]


@app.get("/api/stats")
def stats():
    db = get_db()
    return {"total_conversations": db.count()}
