import { field, html, styled, Template } from 'vanilla-mvc';
import type { PromptFinderController } from './prompt-finder.controller.ts';
import type { PromptFinderModel } from './prompt-finder.model.ts';
import { promptFinderStyle } from './prompt-finder.style.ts';

export const promptFinderTemplate = new Template<PromptFinderModel, PromptFinderController>(
  (m, c) => html`
    <div class="prompt-finder" ${styled(promptFinderStyle, m)}>
      <label class="search">
        <span class="search-label">Search the sample library</span>
        <input type="search" autocomplete="off" spellcheck="false" .value=${m.query} @input=${field(c.handler('search'))}>
      </label>
      <p class="count" aria-live="polite">${m.count}</p>
      <fieldset class="hits">
        <legend class="visually-hidden">Matching prompts, best first</legend>
        ${m.rows.map((row) => html`
          <label data-key=${row.id} class=${row.chosen ? 'hit chosen' : 'hit'}>
            <input type="radio" name="prompt" value=${row.id} .checked=${row.chosen} @change=${field(c.handler('choose'))}>
            <span class="title">${row.title}</span>
            <span class="id">${row.id}</span>
            <span class="tags">${row.tags}</span>
            <span class="score" style=${row.bar}><span class="bar"></span><span class="num">${row.score}</span></span>
          </label>`)}
      </fieldset>
      <p class="empty">${m.empty}</p>
    </div>
  `,
);
