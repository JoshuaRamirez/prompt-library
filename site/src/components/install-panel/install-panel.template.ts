import { html, styled, Template } from 'vanilla-mvc';
import type { InstallPanelController } from './install-panel.controller.ts';
import type { InstallPanelModel } from './install-panel.model.ts';
import { installPanelStyle } from './install-panel.style.ts';

export const installPanelTemplate = new Template<InstallPanelModel, InstallPanelController>(
  (m, c) => html`
    <div class="install-panel" ${styled(installPanelStyle, m)}>
      <p class="lead-in">Inside Claude Code, run:</p>
      <pre><code>${m.commands.map((line) => html`<span class="line">${line}</span>`)}</code></pre>
      <button type="button" class="copy" @click=${c.handler('copy')}>${m.copyLabel}</button>
      <p class="aside">Needs Python 3.9 or newer, on macOS or Linux.</p>
    </div>
  `,
);
