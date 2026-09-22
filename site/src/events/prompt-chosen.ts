import type { PromptPart } from './prompt-part.ts';

/** A prompt was picked to fill in. */
export interface PromptChosen {
  type: 'PromptChosen';
  id: string;
  title: string;
  parts: readonly PromptPart[];
}
