/** A run of a prompt body: literal text, or a `{{variable}}` to be filled in. */
export interface PromptPart {
  kind: 'text' | 'variable';
  /** The literal text, or the variable's name. */
  text: string;
}
