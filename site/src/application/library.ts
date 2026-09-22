import { ApplicationElement } from 'vanilla-mvc';
import type { PromptChosen } from '../events/prompt-chosen.ts';
import type { PromptRendered } from '../events/prompt-rendered.ts';
import type { PromptsRanked } from '../events/prompts-ranked.ts';
import { KeywordSearch } from './keyword-search.ts';
import { samplePrompts, type SamplePrompt } from './sample-prompts.ts';
import { TemplateRenderer } from './template-renderer.ts';

/**
 * The demo library: search it, choose a prompt, fill in its variables. Everything runs in the
 * page; nothing is sent anywhere.
 */
export class Library extends ApplicationElement {
  static readonly firstQuery = 'review';

  #chosen: SamplePrompt | undefined;
  #values: Record<string, string> = {};

  protected override onActivate(): void {
    this.search(Library.firstQuery);
  }

  search(query: string): void {
    const ranked = KeywordSearch.rank(query, samplePrompts);
    const best = ranked[0]?.score ?? 1;
    this.publish<PromptsRanked>({
      type: 'PromptsRanked',
      query,
      total: samplePrompts.length,
      hits: ranked.map(({ prompt, score }) => ({
        id: prompt.id, title: prompt.title, tags: prompt.tags,
        score: Math.round(score * 100) / 100, share: score / best,
      })),
    });
    const top = ranked[0]?.prompt;
    if (top && !ranked.some(({ prompt }) => prompt === this.#chosen)) this.choose(top.id);
  }

  choose(id: string): void {
    const prompt = samplePrompts.find((p) => p.id === id);
    if (!prompt || prompt === this.#chosen) return;
    this.#chosen = prompt;
    this.#values = {};
    this.publish<PromptChosen>({ type: 'PromptChosen', id, title: prompt.title, parts: TemplateRenderer.parts(prompt.prompt) });
    this.#rendered();
  }

  fill(name: string, value: string): void {
    if (!this.#chosen) return;
    this.#values = { ...this.#values, [name]: value.trim() };
    this.#rendered();
  }

  #rendered(): void {
    const prompt = this.#chosen!;
    const { text, unfilled } = TemplateRenderer.render(prompt.prompt, this.#values);
    this.publish<PromptRendered>({ type: 'PromptRendered', id: prompt.id, values: this.#values, text, unfilled });
  }
}
