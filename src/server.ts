import express from 'express';
import { Storage } from './storage';
import { SearchEngine } from './search';

export function createServer(storage: Storage, port = 3000) {
  const app = express();
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  const search = new SearchEngine();

  function reindex() {
    search.index(storage.getAll(10000));
  }
  reindex();

  const HTML = `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Conversation Archive</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0d1117;color:#c9d1d9;max-width:900px;margin:0 auto;padding:20px}
h1{color:#58a6ff;margin-bottom:20px}
input[type=text]{width:100%;padding:12px;border:1px solid #30363d;background:#161b22;color:#c9d1d9;border-radius:6px;font-size:16px;margin-bottom:20px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;margin-bottom:12px}
.card h3{color:#58a6ff;margin-bottom:8px}
.card .meta{color:#8b949e;font-size:13px;margin-bottom:8px}
.tag{display:inline-block;background:#1f6feb33;color:#58a6ff;padding:2px 8px;border-radius:12px;font-size:12px;margin-right:4px}
.msg{border-left:3px solid #30363d;padding:4px 12px;margin:4px 0;font-size:14px}
.msg.assistant{border-color:#58a6ff}
a{color:#58a6ff;text-decoration:none}
.stats{color:#8b949e;margin-bottom:20px}
</style></head><body>
<h1>📚 Conversation Archive</h1>
<div class="stats" id="stats"></div>
<form action="/search" method="get"><input type="text" name="q" placeholder="Search conversations..." autofocus></form>
<div id="results"></div>
<script>
fetch('/api/stats').then(r=>r.json()).then(d=>{document.getElementById('stats').textContent=d.count+' conversations archived'});
fetch('/api/conversations').then(r=>r.json()).then(render);
document.querySelector('form').onsubmit=e=>{e.preventDefault();const q=e.target.q.value;
fetch('/api/search?q='+encodeURIComponent(q)).then(r=>r.json()).then(render)};
function render(convs){const el=document.getElementById('results');el.innerHTML=convs.map(c=>
'<div class="card"><h3><a href="/conversation/'+c.id+'">'+esc(c.title)+'</a></h3>'+
'<div class="meta">'+c.source+' · '+new Date(c.created_at).toLocaleDateString()+' · '+c.messages.length+' messages</div>'+
(c.tags||[]).map(t=>'<span class="tag">'+esc(t)+'</span>').join('')+
'</div>').join('')}
function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML}
</script></body></html>`;

  const DETAIL = (c: any, snippets: any[], decisions: any[]) => `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${c.title} - Conversation Archive</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}body{font-family:system-ui,sans-serif;background:#0d1117;color:#c9d1d9;max-width:900px;margin:0 auto;padding:20px}
h1{color:#58a6ff;margin-bottom:8px}h2{color:#c9d1d9;margin:16px 0 8px;font-size:18px}
.meta{color:#8b949e;margin-bottom:20px}.tag{display:inline-block;background:#1f6feb33;color:#58a6ff;padding:2px 8px;border-radius:12px;font-size:12px;margin-right:4px}
.msg{border-left:3px solid #30363d;padding:8px 12px;margin:8px 0;white-space:pre-wrap;font-size:14px}.msg.assistant{border-color:#58a6ff;background:#161b22}
pre{background:#161b22;padding:12px;border-radius:6px;overflow-x:auto;margin:8px 0}
a{color:#58a6ff}
</style></head><body>
<a href="/">← Back</a>
<h1>${c.title}</h1>
<div class="meta">${c.source} · ${new Date(c.created_at).toLocaleDateString()} · ${c.messages.length} messages</div>
${(c.tags || []).map((t: string) => `<span class="tag">${t}</span>`).join('')}
<h2>Messages</h2>
${c.messages.map((m: any) => `<div class="msg ${m.role}"><strong>${m.role}:</strong> ${m.content.slice(0, 2000)}</div>`).join('')}
${snippets.length ? '<h2>Code Snippets</h2>' + snippets.map((s: any) => `<pre><code>// ${s.language}\n${s.code}</code></pre>`).join('') : ''}
${decisions.length ? '<h2>Key Decisions</h2>' + decisions.map((d: any) => `<div class="msg">📌 ${d.summary}</div>`).join('') : ''}
</body></html>`;

  app.get('/', (_req, res) => res.send(HTML));
  
  app.get('/api/stats', (_req, res) => res.json({ count: storage.count() }));
  
  app.get('/api/conversations', (_req, res) => {
    res.json(storage.getAll(50));
  });

  app.get('/api/search', (req, res) => {
    const q = String(req.query.q || '');
    if (!q) return res.json([]);
    // Try FTS first
    const ftsResults = storage.search(q);
    if (ftsResults.length) return res.json(ftsResults);
    // Fall back to TF-IDF
    const tfidfResults = search.search(q);
    const convs = tfidfResults.map(r => storage.getById(r.id)).filter(Boolean);
    res.json(convs);
  });

  app.get('/conversation/:id', (req, res) => {
    const conv = storage.getById(Number(req.params.id));
    if (!conv) return res.status(404).send('Not found');
    const snippets = storage.getSnippets(conv.id) as any[];
    const decisions = storage.getDecisions(conv.id) as any[];
    res.send(DETAIL(conv, snippets, decisions));
  });

  app.get('/api/snippets', (_req, res) => res.json(storage.getSnippets()));
  app.get('/api/decisions', (_req, res) => res.json(storage.getDecisions()));

  app.post('/api/conversations/:id/tags', (req, res) => {
    const tags = req.body.tags || [];
    storage.addTags(Number(req.params.id), tags);
    res.json({ ok: true });
  });

  return app.listen(port, () => {
    console.log(`🚀 Conversation Archive running at http://localhost:${port}`);
  });
}
