import type { PromptPart } from '../events/prompt-part.ts';

/** `{{variable}}` substitution, as lib/promptlib/rendering/template_renderer.py does it. */
const PLACEHOLDER = /\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}/g;

export class TemplateRenderer {
  static parts(template: string): PromptPart[] {
    const parts: PromptPart[] = [];
    let last = 0;
    for (const match of template.matchAll(PLACEHOLDER)) {
      if (match.index > last) parts.push({ kind: 'text', text: template.slice(last, match.index) });
      parts.push({ kind: 'variable', text: match[1] });
      last = match.index + match[0].length;
    }
    if (last < template.length) parts.push({ kind: 'text', text: template.slice(last) });
    return parts;
  }

  static render(template: string, values: Readonly<Record<string, string>>): { text: string; unfilled: string[] } {
    const unfilled: string[] = [];
    const text = template.replace(PLACEHOLDER, (whole, name: string) => {
      const value = values[name];
      if (value) return value;
      if (!unfilled.includes(name)) unfilled.push(name);
      return whole;
    });
    return { text, unfilled };
  }
}
