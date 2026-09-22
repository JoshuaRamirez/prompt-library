import { css, Style } from 'vanilla-mvc';
import type { InstallPanelModel } from './install-panel.model.ts';

export const installPanelStyle = new Style<InstallPanelModel>(
  () => css`
    :scope.install-panel {
      display: grid; gap: 0.75rem; align-content: start;
      padding: 1.25rem 1.25rem 1rem; border-radius: 6px;
      background: var(--sheet); border: 1px solid var(--rule);
    }
    .lead-in, .aside { font-size: 0.9rem; color: var(--ink-soft); }
    pre { margin: 0; font: 0.86rem/1.7 var(--mono); }
    .line { display: block; white-space: pre-wrap; overflow-wrap: break-word; padding-left: 1.5em; text-indent: -1.5em; }
    .word { white-space: nowrap; }
    .copy { justify-self: start; }
  `,
);
