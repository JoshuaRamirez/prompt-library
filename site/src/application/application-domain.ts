import { ApplicationElement } from 'vanilla-mvc';
import { Clipboard } from './clipboard.ts';
import { Library } from './library.ts';

/** What the site knows and does, apart from any screen. */
export class ApplicationDomain extends ApplicationElement {
  library!: Library;
  clipboard!: Clipboard;

  protected override onCreate(): void {
    this.library = this.adopt(new Library());
    this.clipboard = this.adopt(new Clipboard());
  }
}
