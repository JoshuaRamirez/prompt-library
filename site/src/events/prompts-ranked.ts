import type { PromptHit } from './prompt-hit.ts';

/** The library ranked its prompts against a query. */
export interface PromptsRanked {
  type: 'PromptsRanked';
  query: string;
  hits: readonly PromptHit[];
  total: number;
}
