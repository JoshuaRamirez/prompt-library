/** The chosen prompt with the values given so far substituted in. */
export interface PromptRendered {
  type: 'PromptRendered';
  id: string;
  values: Readonly<Record<string, string>>;
  text: string;
  unfilled: readonly string[];
}
