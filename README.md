# Conversation Archive

Privacy-first personal knowledge base that aggregates AI conversations (ChatGPT, Claude, Gemini) with semantic search.

## Features

- **Import** conversations from ChatGPT and Claude exports
- **Semantic search** using local embeddings (sentence-transformers)
- **Browse** by platform, date, topic
- **Extract** code blocks, key decisions, action items
- **Export** to Markdown or JSON
- **Web UI** with instant search
- **100% local** — no cloud required

## Quick Start

```bash
pip install .

# Import ChatGPT conversations
convarch import --source chatgpt --file conversations.json

# Search
convarch search "python csv parsing"

# Browse
convarch browse --platform claude --after 2026-01-01

# Export
convarch export --format markdown --output my-insights/

# Stats
convarch stats
```

## Web UI

```bash
uvicorn convarch.api:app --reload
# Open http://localhost:8000
```

```
┌──────────────────────────────────────────────────┐
│  🗂️ Conversation Archive                         │
│                                                  │
│  [Search your conversations...              ]    │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │ Python CSV Help           (0.923)        │    │
│  │ chatgpt · 5 messages · 2026-01-15       │    │
│  └──────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────┐    │
│  │ Data Processing Pipeline   (0.871)       │    │
│  │ claude · 12 messages · 2026-01-10       │    │
│  └──────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

## CLI Reference

```
┌─────────────────────────────────────────────────────────────┐
│ $ convarch search "deploy fastapi to docker"                │
│                                                             │
│  Score  │ Platform │ Title                     │ Date       │
│ ───────┼──────────┼───────────────────────────┼────────── │
│  0.941 │ chatgpt  │ Docker FastAPI Deploy      │ 2026-01-20│
│  0.887 │ claude   │ Container Best Practices   │ 2026-01-18│
│  0.823 │ chatgpt  │ Python Web Frameworks      │ 2026-01-12│
└─────────────────────────────────────────────────────────────┘
```

## Architecture

```
convarch/
├── cli.py          # Click CLI
├── api.py          # FastAPI web server
├── database.py     # SQLite storage
├── search.py       # Semantic search (sentence-transformers)
├── models.py       # Data models
├── export.py       # Markdown/JSON export
├── parsers/
│   ├── chatgpt.py  # ChatGPT JSON parser
│   └── claude.py   # Claude JSON parser
└── extractors/
    └── content.py  # Code blocks, action items, decisions
```

## Docker

```bash
docker build -t convarch .
docker run -p 8000:8000 -v ~/.convarch:/root/.convarch convarch
```

## Browser Extension

A stub Chrome extension is included in `extension/`. It provides the manifest and background worker for future integration with ChatGPT, Claude, and Gemini web interfaces.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
