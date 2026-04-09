"""Semantic search using sentence-transformers embeddings with cosine similarity."""

from __future__ import annotations

from typing import Optional

import numpy as np

from .database import Database
from .models import Conversation

# Lazy-loaded model
_model = None
_model_name = "all-MiniLM-L6-v2"


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_model_name)
    return _model


def embed_text(text: str) -> np.ndarray:
    model = _get_model()
    return model.encode(text, normalize_embeddings=True).astype(np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def search(db: Database, query: str, top_k: int = 10) -> list[tuple[Conversation, float]]:
    """Search conversations by semantic similarity to query."""
    query_emb = embed_text(query)
    all_embs = db.get_all_embeddings()
    if not all_embs:
        return []

    scored: list[tuple[str, float]] = []
    for conv_id, emb in all_embs:
        score = cosine_similarity(query_emb, emb)
        scored.append((conv_id, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    results = []
    for conv_id, score in scored[:top_k]:
        conv = db.get_conversation(conv_id)
        if conv:
            results.append((conv, score))
    return results


def embed_conversation(conv: Conversation) -> np.ndarray:
    """Generate embedding for a conversation's full text."""
    text = conv.title + "\n" + conv.full_text
    # Truncate to ~512 tokens worth of text (~2000 chars)
    if len(text) > 2000:
        text = text[:2000]
    return embed_text(text)
