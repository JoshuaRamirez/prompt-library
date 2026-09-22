import { Controller } from 'vanilla-mvc';
import type { ApplicationDomain } from '../../application/application-domain.ts';
import type { Clipboard } from '../../application/clipboard.ts';
import type { TextCopied } from '../../events/text-copied.ts';
import type { InstallPanelModel } from './install-panel.model.ts';

const COMMANDS = [
  '/plugin marketplace add JoshuaRamirez/claude-code-plugins',
  '/plugin install prompt-library@RedJay',
];

export class InstallPanelController extends Controller<InstallPanelModel, ApplicationDomain> {
  #clipboard!: Clipboard;

  protected createModel(): InstallPanelModel {
    return { commands: COMMANDS.map((line) => line.split(' ')), copyLabel: 'Copy commands' };
  }

  protected override onCreate(): void {
    this.#clipboard = this.domain.clipboard;
  }

  protected override onInterconnect(): void {
    this.handle('copy', this.#copy);
    this.subscribe<TextCopied>('TextCopied', this.#textCopied);
  }

  #copy(): Promise<void> {
    return this.#clipboard.copy('install', COMMANDS.join('\n'));
  }

  #textCopied({ target, ok }: TextCopied): void {
    if (target !== 'install') return;
    this.model.copyLabel = ok ? 'Copied' : 'Select the text to copy it';
    this.changed();
  }
}
