import { field, html, styled, Template } from 'vanilla-mvc';
import type { PromptComposerController } from './prompt-composer.controller.ts';
import type { PromptComposerModel } from './prompt-composer.model.ts';
import { promptComposerStyle } from './prompt-composer.style.ts';

export const promptComposerTemplate = new Template<PromptComposerModel, PromptComposerController>(
  (m, c) => html`
    <div class="prompt-composer" ${styled(promptComposerStyle, m)}>
      <p class="heading"><span class="title">${m.title}</span> <span class="id">${m.id}</span></p>
      <p class="body">${m.parts.map((part) => part.kind === 'text'
        ? html`<span data-key=${part.key}>${part.text}</span>`
        : html`<input data-key=${part.key} class="blank" name=${part.text} placeholder=${part.text}
                 aria-label=${part.text} autocomplete="off" spellcheck="false" size=${part.size}
                 .value=${part.value} @input=${field(c.handler('fill'))}>`)}</p>
      <div class="meter" aria-hidden="true"><div class="fill"></div></div>
      <p class="status" aria-live="polite">${m.status}</p>
      <div class="output">
        <p class="output-label">What gets sent</p>
        <p class="output-text">${m.output}</p>
      </div>
      <button type="button" class="copy" ?disabled=${!m.ready} @click=${c.handler('copy')}>${m.copyLabel}</button>
    </div>
  `,
);
