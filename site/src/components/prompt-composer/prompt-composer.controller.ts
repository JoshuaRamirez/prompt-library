import { Controller, type FieldChange } from 'vanilla-mvc';
import type { ApplicationDomain } from '../../application/application-domain.ts';
import type { Clipboard } from '../../application/clipboard.ts';
import type { Library } from '../../application/library.ts';
import type { PromptChosen } from '../../events/prompt-chosen.ts';
import type { PromptRendered } from '../../events/prompt-rendered.ts';
import type { TextCopied } from '../../events/text-copied.ts';
import type { PromptComposerModel } from './prompt-composer.model.ts';

const COPY = 'Copy prompt';

export class PromptComposerController extends Controller<PromptComposerModel, ApplicationDomain> {
  #library!: Library;
  #clipboard!: Clipboard;

  protected createModel(): PromptComposerModel {
    return { title: '', id: '', parts: [], output: '', status: '', ready: false, filled: 0, copyLabel: COPY };
  }

  protected override onCreate(): void {
    this.#library = this.domain.library;
    this.#clipboard = this.domain.clipboard;
  }

  protected override onInterconnect(): void {
    this.handle('fill', this.#fill);
    this.handle('copy', this.#copy);
    this.subscribe<PromptChosen>('PromptChosen', this.#promptChosen);
    this.subscribe<PromptRendered>('PromptRendered', this.#promptRendered);
    this.subscribe<TextCopied>('TextCopied', this.#textCopied);
  }

  #fill({ name, value }: FieldChange): void {
    this.#library.fill(name, String(value ?? ''));
  }

  #copy(): Promise<void> {
    return this.#clipboard.copy('prompt', this.model.output);
  }

  #promptChosen({ id, title, parts }: PromptChosen): void {
    this.model.id = id;
    this.model.title = title;
    this.model.parts = parts.map((part, index) => ({
      key: `${id}-${index}`, kind: part.kind, text: part.text, value: '', size: part.text.length + 1,
    }));
    this.changed();
  }

  #promptRendered({ values, text, unfilled }: PromptRendered): void {
    this.model.parts = this.model.parts.map((part) => {
      if (part.kind === 'text') return part;
      const value = values[part.text] ?? '';
      return { ...part, value, size: Math.max(part.text.length, value.length) + 1 };
    });
    const blanks = new Set(this.model.parts.filter((p) => p.kind === 'variable').map((p) => p.text)).size;
    this.model.output = text;
    this.model.ready = unfilled.length === 0;
    this.model.filled = blanks ? (blanks - unfilled.length) / blanks : 1;
    this.model.status = unfilled.length === 0
      ? 'Ready to send.'
      : `${unfilled.length} ${unfilled.length === 1 ? 'blank' : 'blanks'} left: ${unfilled.join(', ')}`;
    this.model.copyLabel = COPY;
    this.changed();
  }

  #textCopied({ target, ok }: TextCopied): void {
    if (target !== 'prompt') return;
    this.model.copyLabel = ok ? 'Copied' : 'Select the text to copy it';
    this.changed();
  }
}
