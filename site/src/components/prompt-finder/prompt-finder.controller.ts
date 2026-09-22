import { Controller, type FieldChange } from 'vanilla-mvc';
import type { ApplicationDomain } from '../../application/application-domain.ts';
import type { Library } from '../../application/library.ts';
import type { PromptChosen } from '../../events/prompt-chosen.ts';
import type { PromptsRanked } from '../../events/prompts-ranked.ts';
import type { PromptFinderModel } from './prompt-finder.model.ts';

export class PromptFinderController extends Controller<PromptFinderModel, ApplicationDomain> {
  #library!: Library;
  #chosen = '';

  protected createModel(): PromptFinderModel {
    return { query: '', rows: [], count: '', empty: '' };
  }

  protected override onCreate(): void {
    this.#library = this.domain.library;
  }

  protected override onInterconnect(): void {
    this.handle('search', this.#search);
    this.handle('choose', this.#choose);
    this.subscribe<PromptsRanked>('PromptsRanked', this.#ranked);
    this.subscribe<PromptChosen>('PromptChosen', this.#promptChosen);
  }

  #search({ value }: FieldChange): void {
    this.#library.search(String(value ?? ''));
  }

  #choose({ value }: FieldChange): void {
    this.#library.choose(String(value));
  }

  #ranked({ query, hits, total }: PromptsRanked): void {
    this.model.query = query;
    this.model.rows = hits.map((hit) => ({
      id: hit.id,
      title: hit.title,
      tags: hit.tags.join(', '),
      score: hit.score.toFixed(1),
      bar: `--share: ${hit.share.toFixed(3)}`,
      chosen: hit.id === this.#chosen,
    }));
    this.model.count = query.trim()
      ? `${hits.length} of ${total} prompts match`
      : `Type a word to search ${total} prompts`;
    this.model.empty = query.trim() && !hits.length
      ? `Nothing matches “${query.trim()}”. Try a tag such as git, sql or testing.`
      : '';
    this.changed();
  }

  #promptChosen({ id }: PromptChosen): void {
    this.#chosen = id;
    this.model.rows = this.model.rows.map((row) => ({ ...row, chosen: row.id === id }));
    this.changed();
  }
}
