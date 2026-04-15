export interface CodeSnippet {
  language: string;
  code: string;
  context: string;
}

export interface Decision {
  summary: string;
  context: string;
}

export class Extractor {
  extractCodeSnippets(text: string): CodeSnippet[] {
    const snippets: CodeSnippet[] = [];
    const regex = /```(\w*)\n([\s\S]*?)```/g;
    let match;

    while ((match = regex.exec(text)) !== null) {
      const language = match[1] || 'text';
      const code = match[2].trim();
      // Get surrounding context (50 chars before the match)
      const start = Math.max(0, match.index - 100);
      const context = text.slice(start, match.index).trim().split('\n').pop() || '';

      if (code.length > 10) {
        snippets.push({ language, code, context });
      }
    }
    return snippets;
  }

  extractDecisions(text: string): Decision[] {
    const decisions: Decision[] = [];
    const patterns = [
      /(?:decided|decision|chose|chosen|went with|settled on|agreed|conclusion)[:\s]+(.{10,200})/gi,
      /(?:let'?s go with|we(?:'ll)? use|the approach is|final answer)[:\s]+(.{10,200})/gi,
    ];

    for (const pattern of patterns) {
      let match;
      while ((match = pattern.exec(text)) !== null) {
        const summary = match[1].trim().replace(/\n.*/s, '');
        const start = Math.max(0, match.index - 100);
        const context = text.slice(start, match.index).trim().split('\n').pop() || '';
        decisions.push({ summary, context });
      }
    }
    return decisions;
  }
}
