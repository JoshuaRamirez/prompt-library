import { ApplicationElement } from 'vanilla-mvc';
import type { TextCopied } from '../events/text-copied.ts';

/** Puts text on the clipboard and says whether it got there. */
export class Clipboard extends ApplicationElement {
  async copy(target: string, text: string): Promise<void> {
    let ok = true;
    try { await navigator.clipboard.writeText(text); } catch { ok = false; }
    this.publish<TextCopied>({ type: 'TextCopied', target, ok });
  }
}
