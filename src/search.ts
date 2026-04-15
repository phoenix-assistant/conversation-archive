import type { Conversation } from './storage';

interface TfIdfDoc {
  id: number;
  terms: Map<string, number>;
  magnitude: number;
}

export class SearchEngine {
  private docs: TfIdfDoc[] = [];
  private idf: Map<string, number> = new Map();
  private totalDocs = 0;

  index(conversations: (Conversation & { id: number })[]) {
    this.totalDocs = conversations.length;
    const df = new Map<string, number>();

    this.docs = conversations.map(conv => {
      const text = [conv.title, ...conv.messages.map(m => m.content), ...conv.tags].join(' ');
      const terms = this.tokenize(text);
      const tf = new Map<string, number>();

      for (const t of terms) {
        tf.set(t, (tf.get(t) || 0) + 1);
      }
      // Track document frequency
      for (const t of new Set(terms)) {
        df.set(t, (df.get(t) || 0) + 1);
      }

      return { id: conv.id, terms: tf, magnitude: 0 };
    });

    // Compute IDF
    for (const [term, count] of df) {
      this.idf.set(term, Math.log(this.totalDocs / (1 + count)));
    }

    // Compute TF-IDF weights and magnitudes
    for (const doc of this.docs) {
      let mag = 0;
      for (const [term, count] of doc.terms) {
        const weight = count * (this.idf.get(term) || 0);
        doc.terms.set(term, weight);
        mag += weight * weight;
      }
      doc.magnitude = Math.sqrt(mag);
    }
  }

  search(query: string, limit = 10): { id: number; score: number }[] {
    const qTerms = this.tokenize(query);
    const qTf = new Map<string, number>();
    for (const t of qTerms) qTf.set(t, (qTf.get(t) || 0) + 1);

    let qMag = 0;
    const qWeights = new Map<string, number>();
    for (const [term, count] of qTf) {
      const w = count * (this.idf.get(term) || 0);
      qWeights.set(term, w);
      qMag += w * w;
    }
    qMag = Math.sqrt(qMag);
    if (qMag === 0) return [];

    const results: { id: number; score: number }[] = [];
    for (const doc of this.docs) {
      if (doc.magnitude === 0) continue;
      let dot = 0;
      for (const [term, w] of qWeights) {
        dot += w * (doc.terms.get(term) || 0);
      }
      const score = dot / (qMag * doc.magnitude);
      if (score > 0) results.push({ id: doc.id, score });
    }

    return results.sort((a, b) => b.score - a.score).slice(0, limit);
  }

  private tokenize(text: string): string[] {
    return text.toLowerCase().replace(/[^a-z0-9\s]/g, ' ').split(/\s+/).filter(t => t.length > 2);
  }
}
