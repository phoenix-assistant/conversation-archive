import Database from 'better-sqlite3';
import path from 'path';

export interface Message {
  role: string;
  content: string;
  timestamp?: string;
}

export interface Conversation {
  id?: number;
  title: string;
  source: 'claude' | 'chatgpt' | 'markdown' | 'unknown';
  messages: Message[];
  tags: string[];
  created_at: string;
  imported_at?: string;
}

export class Storage {
  private db: Database.Database;

  constructor(dbPath: string = path.join(process.cwd(), 'conversations.db')) {
    this.db = new Database(dbPath);
    this.db.pragma('journal_mode = WAL');
    this.init();
  }

  private init() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        source TEXT NOT NULL,
        messages TEXT NOT NULL,
        tags TEXT DEFAULT '[]',
        created_at TEXT NOT NULL,
        imported_at TEXT DEFAULT (datetime('now'))
      );
      CREATE VIRTUAL TABLE IF NOT EXISTS conversations_fts USING fts5(
        title, content, tags, content_rowid='id'
      );
      CREATE TABLE IF NOT EXISTS code_snippets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER REFERENCES conversations(id),
        language TEXT,
        code TEXT NOT NULL,
        context TEXT
      );
      CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER REFERENCES conversations(id),
        summary TEXT NOT NULL,
        context TEXT
      );
    `);
  }

  insert(conv: Conversation): number {
    const stmt = this.db.prepare(`
      INSERT INTO conversations (title, source, messages, tags, created_at)
      VALUES (?, ?, ?, ?, ?)
    `);
    const result = stmt.run(
      conv.title,
      conv.source,
      JSON.stringify(conv.messages),
      JSON.stringify(conv.tags),
      conv.created_at
    );
    const id = result.lastInsertRowid as number;

    const allContent = conv.messages.map(m => m.content).join('\n');
    this.db.prepare(`INSERT INTO conversations_fts(rowid, title, content, tags) VALUES (?, ?, ?, ?)`)
      .run(id, conv.title, allContent, conv.tags.join(' '));

    return id;
  }

  search(query: string, limit = 20): (Conversation & { id: number; rank: number })[] {
    const rows = this.db.prepare(`
      SELECT c.*, fts.rank
      FROM conversations_fts fts
      JOIN conversations c ON c.id = fts.rowid
      WHERE conversations_fts MATCH ?
      ORDER BY fts.rank
      LIMIT ?
    `).all(query, limit) as any[];

    return rows.map(r => ({
      id: r.id,
      title: r.title,
      source: r.source,
      messages: JSON.parse(r.messages),
      tags: JSON.parse(r.tags),
      created_at: r.created_at,
      imported_at: r.imported_at,
      rank: r.rank,
    }));
  }

  getAll(limit = 100): (Conversation & { id: number })[] {
    const rows = this.db.prepare('SELECT * FROM conversations ORDER BY created_at DESC LIMIT ?').all(limit) as any[];
    return rows.map(r => ({
      id: r.id,
      title: r.title,
      source: r.source,
      messages: JSON.parse(r.messages),
      tags: JSON.parse(r.tags),
      created_at: r.created_at,
      imported_at: r.imported_at,
    }));
  }

  getById(id: number): (Conversation & { id: number }) | null {
    const r = this.db.prepare('SELECT * FROM conversations WHERE id = ?').get(id) as any;
    if (!r) return null;
    return { id: r.id, title: r.title, source: r.source, messages: JSON.parse(r.messages), tags: JSON.parse(r.tags), created_at: r.created_at, imported_at: r.imported_at };
  }

  addTags(id: number, tags: string[]) {
    const conv = this.getById(id);
    if (!conv) return;
    const merged = [...new Set([...conv.tags, ...tags])];
    this.db.prepare('UPDATE conversations SET tags = ? WHERE id = ?').run(JSON.stringify(merged), id);
    this.db.prepare('UPDATE conversations_fts SET tags = ? WHERE rowid = ?').run(merged.join(' '), id);
  }

  insertSnippet(conversationId: number, language: string, code: string, context: string) {
    this.db.prepare('INSERT INTO code_snippets (conversation_id, language, code, context) VALUES (?, ?, ?, ?)')
      .run(conversationId, language, code, context);
  }

  insertDecision(conversationId: number, summary: string, context: string) {
    this.db.prepare('INSERT INTO decisions (conversation_id, summary, context) VALUES (?, ?, ?)')
      .run(conversationId, summary, context);
  }

  getSnippets(conversationId?: number) {
    if (conversationId) {
      return this.db.prepare('SELECT * FROM code_snippets WHERE conversation_id = ?').all(conversationId);
    }
    return this.db.prepare('SELECT * FROM code_snippets').all();
  }

  getDecisions(conversationId?: number) {
    if (conversationId) {
      return this.db.prepare('SELECT * FROM decisions WHERE conversation_id = ?').all(conversationId);
    }
    return this.db.prepare('SELECT * FROM decisions').all();
  }

  count(): number {
    return (this.db.prepare('SELECT COUNT(*) as c FROM conversations').get() as any).c;
  }

  close() {
    this.db.close();
  }
}
