import type { SamplePrompt } from './sample-prompts.ts';

/**
 * The plugin's ranking, ported from lib/promptlib/search/keyword_strategy.py: field-weighted term
 * frequency, a substring match at 0.4 of a whole-word one, and a bonus when the whole query appears
 * as a phrase. Same weights, same stop words, same tie-break on id.
 */
const WEIGHTS: ReadonlyArray<[keyof SamplePrompt, number]> = [
  ['title', 3], ['tags', 2.5], ['category', 2], ['prompt', 1], ['notes', 0.5],
];
const PHRASE_BONUS = 2;
const STOP_WORDS = new Set('a an the and or of to in for on with is are be as by that this it you your'.split(' '));
const WORD = /[a-z0-9_]+/g;

export interface Ranked { prompt: SamplePrompt; score: number }

export class KeywordSearch {
  static tokenize(text: string): string[] {
    return (text.toLowerCase().match(WORD) ?? []).filter((t) => t.length >= 2 && !STOP_WORDS.has(t));
  }

  static tokenizeQuery(text: string): string[] {
    const tokens = KeywordSearch.tokenize(text);
    return tokens.length ? tokens : text.toLowerCase().match(WORD) ?? [];
  }

  static rank(query: string, prompts: readonly SamplePrompt[]): Ranked[] {
    const terms = KeywordSearch.tokenizeQuery(query);
    if (!terms.length) return [];
    const phrase = query.trim().toLowerCase();
    return prompts
      .map((prompt) => ({ prompt, score: KeywordSearch.#score(prompt, terms, phrase) }))
      .filter((hit) => hit.score > 0)
      .sort((a, b) => b.score - a.score || (a.prompt.id < b.prompt.id ? -1 : 1));
  }

  static #score(prompt: SamplePrompt, terms: string[], phrase: string): number {
    let total = 0;
    for (const [column, weight] of WEIGHTS) {
      const value = prompt[column];
      const text = Array.isArray(value) ? value.join(' ') : String(value);
      if (text) total += KeywordSearch.#fieldScore(text, terms, phrase, weight);
    }
    return total;
  }

  static #fieldScore(text: string, terms: string[], phrase: string, weight: number): number {
    const counts = new Map<string, number>();
    for (const token of KeywordSearch.tokenize(text)) counts.set(token, (counts.get(token) ?? 0) + 1);
    const lowered = text.toLowerCase();
    let score = 0;
    for (const term of terms) {
      const occurrences = counts.get(term) ?? 0;
      if (occurrences) score += weight * (1 + Math.log(occurrences));
      else if (lowered.includes(term)) score += weight * 0.4;
    }
    if (score > 0 && phrase && lowered.includes(phrase)) score += weight * PHRASE_BONUS;
    return score;
  }
}
