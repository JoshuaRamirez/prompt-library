export interface PromptComposerPart {
  key: string;
  kind: 'text' | 'variable';
  /** Literal text, or the variable's name. */
  text: string;
  value: string;
  /** Width of the blank, in characters. */
  size: number;
}

/** What the prompt-composer view reads. */
export interface PromptComposerModel {
  title: string;
  id: string;
  parts: readonly PromptComposerPart[];
  output: string;
  status: string;
  ready: boolean;
  /** Share of the blanks filled in, 0..1. */
  filled: number;
  copyLabel: string;
}
