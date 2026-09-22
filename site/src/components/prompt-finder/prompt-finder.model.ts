export interface PromptFinderRow {
  id: string;
  title: string;
  tags: string;
  score: string;
  /** Inline declaration carrying the score as a share of the best, for the bar. */
  bar: string;
  chosen: boolean;
}

/** What the prompt-finder view reads. */
export interface PromptFinderModel {
  query: string;
  rows: readonly PromptFinderRow[];
  count: string;
  empty: string;
}
