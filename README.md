# Conversation Archive

> **One-line pitch:** A personal knowledge base that aggregates, indexes, and makes searchable all your AI conversations across ChatGPT, Claude, Gemini, and others—with privacy-first design and semantic search.

---

## Problem

### Who Feels the Pain
- **Power users of AI tools** (10+ conversations/week) who've lost valuable insights in chat history
- **Researchers and analysts** who use AI for ideation/analysis but can't retrieve past explorations
- **Professionals** who've solved problems with AI but can't find the solution months later
- **Teams** sharing AI workflows who need knowledge capture without manual documentation
- **Privacy-conscious users** who want to own their AI conversation data

### How Bad Is It
- **Average ChatGPT user** has 50-200 conversations; finding specific content takes 5-15 minutes of scrolling
- **No cross-platform search:** If you used Claude for one thing and ChatGPT for another, no unified view
- **Export friction:** ChatGPT export is JSON blob requiring technical skill to parse
- **Knowledge loss:** Estimated 80% of valuable AI-assisted insights are never retrievable
- **Enterprise concern:** Companies lack visibility into AI usage patterns and knowledge created

### Pain Intensity: 6/10
Moderate frustration—users feel it when they need something, but don't think about it daily. Latent demand, needs trigger event.

---

## Solution

### What We Build
A cross-platform AI conversation aggregator with:
1. **Automatic sync** from major AI platforms (API + browser extension)
2. **Semantic search** across all conversations
3. **Knowledge extraction** (key insights, decisions, code snippets auto-tagged)
4. **Privacy-first architecture** (local-first option, encryption, data ownership)

### How It Works

**Data Collection:**
- Browser extension monitors AI chat interfaces, captures conversations
- API connections where available (OpenAI API logs, Anthropic Console)
- Manual import of exports (ChatGPT JSON, Claude exports)
- Optional: email forwarding for AI-via-email services

**Processing Pipeline:**
1. **Ingest** - Normalize conversation format across platforms
2. **Enrich** - Extract entities, topics, code blocks, decisions, action items
3. **Embed** - Generate vector embeddings for semantic search
4. **Index** - Full-text search + vector index
5. **Classify** - Auto-tag by domain (code, writing, research, brainstorm, etc.)

**User Interface:**
- **Search bar** with natural language queries ("that Python script for parsing CSVs")
- **Browse by** time, platform, topic, project
- **Highlights** - AI-extracted key insights and decisions
- **Collections** - User-curated groupings
- **Export** - Markdown, JSON, PDF for any subset

**Privacy Controls:**
- Local-only mode (no cloud, runs on device)
- End-to-end encryption for cloud sync
- Granular deletion (conversation, platform, time range)
- Data export (full ownership)
- No training on user data (explicit policy)

---

## Why Now

1. **Fragmentation is peaking** - ChatGPT, Claude, Gemini, Perplexity, Poe, Copilot—users spread across 3-5 tools
2. **Conversation volume exploding** - Power users hitting 100+ conversations/month
3. **Vector search commoditized** - Pinecone, Weaviate, pgvector make semantic search cheap
4. **Privacy backlash** - Users increasingly want data ownership, local-first gaining traction
5. **Enterprise AI governance** - Companies need to know what employees are putting into AI
6. **Second-brain movement** - Obsidian, Notion, Roam users want AI conversations in their PKM

---

## Market Landscape

### TAM (Total Addressable Market)
- **Global AI chat users:** 500M (monthly active)
- **Power users (10+ convos/week):** 50M
- **Average spend on productivity tools:** $100/year
- **TAM:** $5B

### SAM (Serviceable Addressable Market)
- **English-speaking power users with retrieval pain:** 15M
- **Willingness to pay for knowledge tools:** 20%
- **Average price point:** $100/year
- **SAM:** $300M

### SOM (Serviceable Obtainable Market - 3 year)
- **Realistic capture:** 1% of SAM = 30,000 users
- **SOM:** $3M ARR

### Competitors

| Competitor | What They Do | Gap |
|------------|--------------|-----|
| **ChatGPT native search** | Basic search within ChatGPT | Single platform, keyword only, no enrichment |
| **Claude Projects** | Conversation organization | Single platform, limited search |
| **Notion AI** | AI + knowledge base | Doesn't aggregate external AI chats |
| **Mem.ai** | AI-powered notes | Manual capture, not automatic sync |
| **Rewind.ai** | Screen recording + search | Heavy (records everything), privacy concerns |
| **Obsidian + plugins** | PKM with AI | DIY, requires technical setup, no auto-sync |
| **Dust.tt** | Enterprise AI orchestration | Enterprise focus, not personal knowledge |
| **TypingMind** | ChatGPT interface | Single API, not aggregation |

### Gap Analysis
**No dedicated cross-platform AI conversation aggregator exists.** Rewind is closest but too broad (all screen activity). Market wants focused, privacy-respecting AI chat knowledge base.

---

## Competitive Advantages

### Moats

1. **Aggregation complexity** - Each platform requires different capture method; early mover builds integrations
2. **Knowledge graph** - Entity extraction and linking across conversations creates unique dataset
3. **Privacy positioning** - Local-first architecture differentiates from cloud-only competitors
4. **Format expertise** - Deep understanding of each AI platform's quirks and export formats
5. **Community plugins** - Open plugin architecture for new platforms, custom enrichment

### Differentiation
- **Cross-platform by design** - Not an add-on to one AI, built for the multi-AI reality
- **Privacy-first** - Local option, encryption, no data selling—trust moat
- **Semantic search** - "Find that thing about..." not just keywords
- **Auto-enrichment** - Extracts value without user effort
- **PKM integration** - Works with Obsidian, Notion, Roam (where knowledge workers live)

---

## Technical Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Collection Layer                     │
├─────────────────────────────────────────────────────────────┤
│  Browser Extension     │  API Connectors    │  Import Tools │
│  - ChatGPT DOM scrape  │  - OpenAI API logs │  - JSON parse │
│  - Claude intercept    │  - Anthropic API   │  - CSV/MD     │
│  - Gemini capture      │  - (future APIs)   │  - Email fwd  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Processing Pipeline                        │
├─────────────────────────────────────────────────────────────┤
│  Normalizer        │  Enrichment          │  Embeddings     │
│  - Format unify    │  - Entity extraction │  - OpenAI/local │
│  - Dedup           │  - Topic modeling    │  - Chunking     │
│  - Clean           │  - Code detection    │  - Vectorize    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Storage Layer                            │
├───────────────────────────┬─────────────────────────────────┤
│      Local Mode           │         Cloud Mode               │
│  - SQLite (metadata)      │  - PostgreSQL (metadata)         │
│  - LanceDB (vectors)      │  - Pinecone/pgvector (vectors)   │
│  - Local files (raw)      │  - S3 encrypted (raw)            │
└───────────────────────────┴─────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
├─────────────────────────────────────────────────────────────┤
│  Desktop App (Electron/Tauri)  │  Web App        │  CLI     │
│  - Search UI                    │  - Cloud users  │  - Power │
│  - Browse/organize              │  - Team collab  │  - users │
│  - Settings                     │  - Share        │          │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

**Local-First Stack:**
- **Desktop App:** Tauri (Rust + web frontend) - small binary, native performance
- **Local DB:** SQLite + LanceDB (vector search)
- **Embeddings:** Local model (all-MiniLM-L6-v2) or OpenAI API
- **Extension:** TypeScript, Chrome Manifest V3

**Cloud Stack:**
- **Backend:** Node.js/Fastify or Go
- **Database:** PostgreSQL + pgvector
- **Storage:** S3 with client-side encryption
- **Search:** Elasticsearch (full-text) + pgvector (semantic)
- **Infrastructure:** Railway/Fly.io

### Key Technical Challenges
1. **Platform capture reliability** - AI sites change frequently, scraping breaks
2. **Sync conflicts** - Local + cloud requires CRDT or careful conflict resolution
3. **Embedding costs** - Large conversation volumes = significant API costs (local model mitigates)
4. **Privacy in cloud mode** - True E2E encryption while enabling search is hard
5. **Cross-browser extension** - Safari especially difficult

---

## Build Plan

### Phase 1: MVP (Months 1-3)
**Goal:** Validate core value prop with local-only product

- Desktop app (Mac) with local-only storage
- ChatGPT import (JSON export parsing)
- Claude import (manual export)
- Basic semantic search (local embeddings)
- Simple browse UI (by date, platform)
- Free, open-source core

**Success Metrics:**
- 500 downloads
- 100 weekly active users
- Qualitative feedback on search utility

### Phase 2: Live Sync + Enrichment (Months 4-8)
**Goal:** Reduce friction, add value, initial revenue

- Browser extension for live capture (ChatGPT, Claude)
- Auto-enrichment (topic tags, code extraction, key insights)
- Collections and organization features
- Windows + Linux support
- Pro tier ($8/month): cloud sync, larger storage, priority processing
- Obsidian plugin for PKM integration

**Success Metrics:**
- 5,000 downloads
- 1,000 weekly active users
- 300 paid users ($2.4K MRR)
- Positive retention (30-day > 40%)

### Phase 3: Platform & Teams (Months 9-18)
**Goal:** Expand platforms, team features, $1M ARR path

- Gemini, Perplexity, Copilot capture
- Team workspaces (shared knowledge base)
- API for developers
- Enterprise features (SSO, audit logs, admin controls)
- Mobile companion app (search on the go)
- Community plugin marketplace

**Success Metrics:**
- 25,000 downloads
- 8,000 paid users + 15 enterprise contracts
- $1M ARR

---

## Risks & Challenges

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Platforms block scraping** | High | High | Multiple capture methods, API where available, user owns their data argument |
| **Native search improves** | High | Medium | Cross-platform value remains; deeper enrichment as moat |
| **Privacy breach** | Low | Fatal | Local-first default, security audits, minimal cloud data |
| **Embedding costs** | Medium | Medium | Local models default, efficient chunking, user pays for cloud embeddings |
| **Low willingness to pay** | Medium | High | Freemium with generous free tier, enterprise focus for revenue |
| **Big player enters** | Medium | High | Speed to market, community, privacy positioning |

### Biggest Challenge
**Platform capture fragility.** AI companies don't want third parties accessing conversation data. Will require constant maintenance as UIs change, and potential legal gray areas around ToS.

---

## Monetization

### Pricing Tiers

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | Local-only, 1,000 conversations, basic search, import only |
| **Pro** | $8/month ($80/year) | Unlimited, cloud sync, live capture, enrichment, priority support |
| **Team** | $15/user/month | Pro + shared workspace, team search, admin controls |
| **Enterprise** | Custom ($300-2K/month) | Team + SSO, compliance, dedicated support, on-prem option |

### Path to $1M ARR

| Segment | Users | Price | ARR |
|---------|-------|-------|-----|
| Pro (individual) | 6,000 | $80/year | $480K |
| Team (small) | 2,000 | $150/year | $300K |
| Enterprise | 10 contracts | $25K avg | $250K |
| **Total** | | | **$1.03M** |

### Timeline to $1M ARR: 18-24 months
- Requires strong word-of-mouth in AI power user community
- Open-source strategy for distribution
- Enterprise sales starting month 9

---

## Verdict: 🟢 BUILD

### Reasoning

**For:**
- **Clear, felt pain** - Anyone with 50+ AI conversations has searched in vain
- **Growing market** - AI conversation volume only increasing; fragmentation getting worse
- **Technical feasibility** - Standard stack, no breakthrough required
- **Privacy differentiation** - Local-first is genuine moat against big tech incumbents
- **Multiple revenue paths** - Consumer, prosumer, enterprise all viable
- **Community potential** - Open-source core can drive distribution and trust

**Against:**
- **Platform capture risk** - Reliant on scraping that could break or be blocked
- **Native search improving** - ChatGPT search getting better (but still single-platform)
- **Requires behavior change** - Users must remember to use it

**Why BUILD:**
The cross-platform aggregation angle is **genuinely unserved**. Even if ChatGPT search improves, users with Claude + ChatGPT + Gemini + Perplexity still have no unified view. Privacy-first positioning creates trust moat that big tech can't easily copy.

**Best entry:** Open-source local-only MVP, build community of AI power users (HN, Reddit r/ChatGPT, Twitter AI community). Convert to paid with cloud sync and live capture. Enterprise comes naturally once product is proven.

**Comparable exits:**
- Notion: $10B (knowledge management)
- Obsidian: $50M+ ARR (local-first PKM)
- Rewind: $350M valuation (personal search)

This sits at intersection of all three trends. Ceiling is high if execution is strong.
