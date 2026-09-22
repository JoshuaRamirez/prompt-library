import { css, Style } from 'vanilla-mvc';
import type { PromptFinderModel } from './prompt-finder.model.ts';

export const promptFinderStyle = new Style<PromptFinderModel>(
  () => css`
    :scope.prompt-finder { display: grid; gap: 0.5rem; align-content: start; }
    .search { display: grid; gap: 0.35rem; }
    .search-label { font-weight: 600; }
    .search input {
      font-size: 1.15rem; padding: 0.55rem 0.75rem; border-radius: 6px;
      border: 1px solid var(--rule-strong); background: var(--sheet); color: var(--ink);
    }
    .count { font-size: 0.9rem; color: var(--ink-soft); }
    .hits { border: 0; padding: 0; margin: 0; border-top: 1px solid var(--rule); }
    .hit {
      display: grid; grid-template-columns: 1fr 6.5rem; column-gap: 1rem;
      padding: 0.6rem 0.75rem 0.6rem 1rem; border-bottom: 1px solid var(--rule);
      cursor: pointer; position: relative;
    }
    .hit:hover { background: var(--sheet); }
    .hit.chosen { background: var(--sheet); box-shadow: inset 3px 0 0 var(--link); }
    .hit input { position: absolute; opacity: 0; pointer-events: none; }
    .hit:has(input:focus-visible) { outline: 2px solid var(--link); outline-offset: -2px; }
    .title { font-weight: 600; grid-column: 1; }
    .id, .tags { grid-column: 1; font-size: 0.85rem; color: var(--ink-soft); }
    .id { font-family: var(--mono); font-size: 0.8rem; }
    .score { grid-column: 2; grid-row: 1 / span 3; align-self: center; display: grid; gap: 0.25rem; }
    .bar {
      display: block; block-size: 6px; border-radius: 3px; background: var(--link);
      inline-size: calc(var(--share, 0) * 100%); transition: inline-size 180ms ease-out;
    }
    .num { font-size: 0.8rem; color: var(--ink-soft); font-variant-numeric: tabular-nums; }
    .empty:empty { display: none; }
    .empty { color: var(--ink-soft); padding: 0.5rem 0; }
    @media (prefers-reduced-motion: reduce) { .bar { transition: none; } }
  `,
);
