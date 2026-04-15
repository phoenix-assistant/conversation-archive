import fs from 'fs';
import path from 'path';
import { glob } from 'glob';
import { Storage, type Conversation, type Message } from './storage';
import { Extractor } from './extractor';

export class Importer {
  constructor(private storage: Storage) {}

  async importPath(inputPath: string): Promise<number> {
    const stat = fs.statSync(inputPath);
    let count = 0;

    if (stat.isDirectory()) {
      const files = await glob('**/*.{json,md,markdown}', { cwd: inputPath, absolute: true });
      for (const file of files) {
        count += this.importFile(file);
      }
    } else {
      count += this.importFile(inputPath);
    }
    return count;
  }

  private importFile(filePath: string): number {
    const ext = path.extname(filePath).toLowerCase();
    const raw = fs.readFileSync(filePath, 'utf-8');

    if (ext === '.md' || ext === '.markdown') {
      return this.importMarkdown(raw, filePath);
    }

    try {
      const data = JSON.parse(raw);
      if (Array.isArray(data)) {
        let count = 0;
        for (const item of data) {
          count += this.importJsonItem(item, filePath);
        }
        return count;
      }
      return this.importJsonItem(data, filePath);
    } catch {
      console.warn(`Skipping unparseable file: ${filePath}`);
      return 0;
    }
  }

  private importJsonItem(data: any, filePath: string): number {
    // Detect Claude export format
    if (data.chat_messages || data.uuid) {
      return this.importClaude(data);
    }
    // Detect ChatGPT export format
    if (data.mapping || data.title) {
      return this.importChatGPT(data);
    }
    // Generic: try messages array
    if (data.messages && Array.isArray(data.messages)) {
      const conv: Conversation = {
        title: data.title || data.name || path.basename(filePath, path.extname(filePath)),
        source: 'unknown',
        messages: data.messages.map((m: any) => ({ role: m.role || 'user', content: m.content || String(m.text || '') })),
        tags: [],
        created_at: data.created_at || data.create_time ? new Date((data.create_time || 0) * 1000).toISOString() : new Date().toISOString(),
      };
      this.storeConversation(conv);
      return 1;
    }
    return 0;
  }

  private importClaude(data: any): number {
    const messages: Message[] = (data.chat_messages || []).map((m: any) => ({
      role: m.sender === 'human' ? 'user' : 'assistant',
      content: typeof m.text === 'string' ? m.text : (m.content?.map((c: any) => c.text || '').join('\n') || ''),
      timestamp: m.created_at,
    }));

    const conv: Conversation = {
      title: data.name || data.title || 'Claude Conversation',
      source: 'claude',
      messages,
      tags: [],
      created_at: data.created_at || new Date().toISOString(),
    };
    this.storeConversation(conv);
    return 1;
  }

  private importChatGPT(data: any): number {
    const messages: Message[] = [];
    if (data.mapping) {
      const nodes = Object.values(data.mapping) as any[];
      nodes
        .filter((n: any) => n.message?.content?.parts?.length)
        .sort((a: any, b: any) => (a.message.create_time || 0) - (b.message.create_time || 0))
        .forEach((n: any) => {
          messages.push({
            role: n.message.author?.role || 'user',
            content: n.message.content.parts.join('\n'),
            timestamp: n.message.create_time ? new Date(n.message.create_time * 1000).toISOString() : undefined,
          });
        });
    }

    const conv: Conversation = {
      title: data.title || 'ChatGPT Conversation',
      source: 'chatgpt',
      messages,
      tags: [],
      created_at: data.create_time ? new Date(data.create_time * 1000).toISOString() : new Date().toISOString(),
    };
    this.storeConversation(conv);
    return 1;
  }

  private importMarkdown(raw: string, filePath: string): number {
    const messages: Message[] = [];
    // Split by headings or "User:" / "Assistant:" patterns
    const sections = raw.split(/^#{1,3}\s+|(?=(?:User|Human|Assistant|AI|Claude|ChatGPT):)/mi).filter(Boolean);
    
    for (const section of sections) {
      const roleMatch = section.match(/^(User|Human|Assistant|AI|Claude|ChatGPT):\s*/i);
      const role = roleMatch ? (/user|human/i.test(roleMatch[1]) ? 'user' : 'assistant') : 'user';
      const content = roleMatch ? section.slice(roleMatch[0].length).trim() : section.trim();
      if (content) messages.push({ role, content });
    }

    if (messages.length === 0) {
      messages.push({ role: 'user', content: raw });
    }

    const conv: Conversation = {
      title: path.basename(filePath, path.extname(filePath)),
      source: 'markdown',
      messages,
      tags: [],
      created_at: new Date(fs.statSync(filePath).mtime).toISOString(),
    };
    this.storeConversation(conv);
    return 1;
  }

  private storeConversation(conv: Conversation) {
    const id = this.storage.insert(conv);
    const extractor = new Extractor();
    const allText = conv.messages.map(m => m.content).join('\n');
    
    for (const snippet of extractor.extractCodeSnippets(allText)) {
      this.storage.insertSnippet(id, snippet.language, snippet.code, snippet.context);
    }
    for (const decision of extractor.extractDecisions(allText)) {
      this.storage.insertDecision(id, decision.summary, decision.context);
    }
  }
}
