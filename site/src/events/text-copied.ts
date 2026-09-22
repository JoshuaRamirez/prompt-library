/** Text went to the clipboard, or could not. `target` names what was copied. */
export interface TextCopied {
  type: 'TextCopied';
  target: string;
  ok: boolean;
}
