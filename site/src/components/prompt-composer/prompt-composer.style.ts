import { css, Style } from 'vanilla-mvc';
import type { PromptComposerModel } from './prompt-composer.model.ts';

/** The meter binds the model's share of blanks filled: a measurement, so a bound hole, not a class. */
export const promptComposerStyle = new Style<PromptComposerModel>(
  (m) => css`
    :scope.prompt-composer { display: grid; gap: 0.9rem; align-content: start; }
    .heading { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.25rem 0.75rem; }
    .title { font-weight: 700; font-size: 1.1rem; }
    .id { font-family: var(--mono); font-size: 0.8rem; color: var(--ink-soft); }
    .body { font-size: 1.35rem; line-height: 2.1; max-inline-size: 34em; text-wrap: pretty; }
    .blank {
      font: inherit; font-size: 1.05rem; line-height: 1.3; color: var(--on-mark);
      background: var(--mark); border: 0; border-bottom: 2px solid var(--mark-edge);
      border-radius: 3px; padding: 0.05rem 0.35rem; margin: 0 0.1rem;
    }
    .blank::placeholder { color: var(--on-mark); opacity: 0.62; font-style: italic; }
    .blank:focus { outline: 2px solid var(--link); outline-offset: 2px; }
    .meter { block-size: 4px; border-radius: 2px; background: var(--rule); overflow: hidden; }
    .fill {
      block-size: 100%; background: var(--mark-edge);
      inline-size: calc(${m.filled} * 100%); transition: inline-size 200ms ease-out;
    }
    .status { font-size: 0.9rem; color: var(--ink-soft); }
    .output { border-inline-start: 3px solid var(--rule-strong); padding-inline-start: 1rem; }
    .output-label { font-size: 0.85rem; font-weight: 600; color: var(--ink-soft); }
    .output-text { font-family: var(--mono); font-size: 0.88rem; line-height: 1.65; white-space: pre-wrap; }
    .copy { justify-self: start; }
    @media (prefers-reduced-motion: reduce) { .fill { transition: none; } }
  `,
);
