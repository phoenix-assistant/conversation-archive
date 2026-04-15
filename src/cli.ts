#!/usr/bin/env node
import { Command } from 'commander';
import path from 'path';
import { Storage } from './storage';
import { Importer } from './importer';
import { SearchEngine } from './search';
import { createServer } from './server';

const program = new Command();

program
  .name('convo-archive')
  .description('Searchable knowledge base from AI conversations')
  .version('1.0.0');

function getStorage() {
  const dbPath = process.env.CONVO_DB || path.join(process.cwd(), 'conversations.db');
  return new Storage(dbPath);
}

program
  .command('import <path>')
  .description('Import conversations from files or directory')
  .option('-t, --tags <tags>', 'Comma-separated tags to apply', '')
  .action(async (inputPath: string, opts) => {
    const storage = getStorage();
    const importer = new Importer(storage);
    const absPath = path.resolve(inputPath);
    console.log(`📥 Importing from ${absPath}...`);
    const count = await importer.importPath(absPath);
    console.log(`✅ Imported ${count} conversation(s). Total: ${storage.count()}`);
    storage.close();
  });

program
  .command('search <query>')
  .description('Search conversations')
  .option('-l, --limit <n>', 'Max results', '10')
  .option('--semantic', 'Use TF-IDF semantic search')
  .action((query: string, opts) => {
    const storage = getStorage();
    
    if (opts.semantic) {
      const engine = new SearchEngine();
      engine.index(storage.getAll(10000));
      const results = engine.search(query, Number(opts.limit));
      for (const r of results) {
        const conv = storage.getById(r.id);
        if (conv) console.log(`[${r.score.toFixed(3)}] #${conv.id} ${conv.title} (${conv.source})`);
      }
    } else {
      const results = storage.search(query, Number(opts.limit));
      if (results.length === 0) {
        console.log('No results found. Try --semantic for fuzzy search.');
      }
      for (const r of results) {
        console.log(`#${r.id} ${r.title} (${r.source}) - ${r.messages.length} messages`);
      }
    }
    storage.close();
  });

program
  .command('serve')
  .description('Start web UI')
  .option('-p, --port <port>', 'Port number', '3000')
  .action((opts) => {
    const storage = getStorage();
    createServer(storage, Number(opts.port));
  });

program
  .command('stats')
  .description('Show archive statistics')
  .action(() => {
    const storage = getStorage();
    console.log(`📊 Conversations: ${storage.count()}`);
    console.log(`📝 Code snippets: ${(storage.getSnippets() as any[]).length}`);
    console.log(`📌 Decisions: ${(storage.getDecisions() as any[]).length}`);
    storage.close();
  });

program
  .command('tag <id> <tags...>')
  .description('Add tags to a conversation')
  .action((id: string, tags: string[]) => {
    const storage = getStorage();
    storage.addTags(Number(id), tags);
    console.log(`✅ Tagged conversation #${id} with: ${tags.join(', ')}`);
    storage.close();
  });

program.parse();
