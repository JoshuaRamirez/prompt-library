/** One ranked search result, as the finder lists it. */
export interface PromptHit {
  id: string;
  title: string;
  tags: readonly string[];
  score: number;
  /** Score as a share of the best score in this search, 0..1. */
  share: number;
}
