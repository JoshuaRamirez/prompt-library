import { html, styled, Template } from 'vanilla-mvc';
import type { SitePageController } from './site-page.controller.ts';
import type { SitePageModel } from './site-page.model.ts';
import { sitePageStyle } from './site-page.style.ts';

const csvExample = `id,title,prompt,tags,category,model,variables,notes,source,version,created_at,updated_at
code-review-checklist,Code review checklist,"Review the {{language}} change in {{file}}. Check error handling, naming and tests. …","review, code",engineering,,"language, file",Works best on one file at a time.,,,2026-09-20T17:02:11+00:00,2026-09-21T09:40:03+00:00
commit-message,Commit message from a diff,Write a commit message for the staged diff in the {{style}} format. …,"git, commit",engineering,,"style, max_length",,,,2026-09-20T17:05:48+00:00,2026-09-20T17:05:48+00:00`;

export const sitePageTemplate = new Template<SitePageModel, SitePageController>(
  (m) => html`
    <div class="site-page" ${styled(sitePageStyle, m)}>
      <header class="masthead">
        <a class="wordmark" href="./">prompt-library</a>
        <nav aria-label="Site">
          <a href=${m.diagrams}>Diagrams</a>
          <a href=${m.repository}>Source</a>
          <a href=${m.repository + '/releases'}>v${m.version}</a>
        </nav>
      </header>

      <main>
        <section class="hero" aria-labelledby="hero-title">
          <div class="hero-text">
            <h1 id="hero-title">Keep the prompts that work.</h1>
            <p class="lede">A prompt library for Claude Code. Save a prompt once, find it again by keyword,
              fill in its blanks and use it. The whole library is one CSV file on your machine.</p>
          </div>
          <div data-component="install-panel"></div>
        </section>

        <section class="demo" aria-labelledby="demo-title">
          <div class="demo-head">
            <h2 id="demo-title">Try it here</h2>
            <p>This is the plugin's own ranking, ported to run in your browser over seven sample prompts.
              Search, pick a result, then fill in the highlighted blanks.</p>
          </div>
          <div class="demo-grid">
            <div data-component="prompt-finder"></div>
            <div data-component="prompt-composer"></div>
          </div>
        </section>

        <section class="ways" aria-labelledby="ways-title">
          <h2 id="ways-title">Three ways in</h2>
          <div class="ways-grid">
            <div class="way">
              <h3>Ask Claude</h3>
              <p>Eight MCP tools let Claude search, read, save and fill prompts for you, and every
                session starts with a short index of what you have, one line per prompt.</p>
              <p class="example">“Use my code review prompt on <code>api/users.py</code>.”</p>
            </div>
            <div class="way">
              <h3>Slash commands</h3>
              <dl class="commands">
                <dt><code>/prompt-save</code></dt><dd>save, after checking for a near-duplicate</dd>
                <dt><code>/prompt-find</code></dt><dd>ranked keyword search</dd>
                <dt><code>/prompt-list</code></dt><dd>everything, or one tag or category</dd>
                <dt><code>/prompt-use</code></dt><dd>fill in the blanks and apply</dd>
                <dt><code>/prompt-edit</code></dt><dd>update or delete</dd>
              </dl>
            </div>
            <div class="way">
              <h3>From a shell</h3>
              <p>The same library through a CLI, <code>bin/promptlib</code> in the plugin directory, for
                scripts and other tools.</p>
              <pre><code>promptlib search code review
promptlib render code-review-checklist \\
  --set language=Go --set file=main.go</code></pre>
            </div>
          </div>
        </section>

        <section class="file" aria-labelledby="file-title">
          <div class="file-text">
            <h2 id="file-title">One file you can open</h2>
            <p>Everything lives in <code>~/.claude/prompt-library/prompts.csv</code>. Open it in a
              spreadsheet, keep it in git, back it up like any other file. Reinstalling or removing the
              plugin never touches it.</p>
          </div>
          <pre class="csv"><code>${csvExample}</code></pre>
        </section>

        <section class="machine" aria-labelledby="machine-title">
          <h2 id="machine-title">What it changes on your machine</h2>
          <ul>
            <li>Creates <code>prompts.csv</code> and a lock file beside it at your first session.</li>
            <li>Adds a session-start hook that lists your prompts, one line each. It is silent while
              the library is empty.</li>
            <li>Runs its MCP server as one shared background service for all your sessions. On first
              use that installs about 30 Python packages into <code>~/.local/state/shared-mcp</code> and
              registers a login service. It listens on 127.0.0.1 only; your prompts never leave the machine.</li>
          </ul>
          <p>To skip the background service, set <code>SHARED_MCP_DISABLE=1</code> before starting Claude
            Code. Each session then runs its own copy on the Python standard library, and nothing is
            downloaded. <a href=${m.repository + '#how-this-plugin-runs-its-mcp-server-shared-background-service'}>Removal steps</a> are in the README.</p>
        </section>

        <section class="built" aria-labelledby="built-title">
          <h2 id="built-title">How it's built</h2>
          <p>Three interactive diagrams, traced from the source: how each use case flows through the
            code, each use case broken into its steps, and how the data is structured.</p>
          <p><a class="button-link" href=${m.diagrams}>Open the diagrams</a></p>
        </section>
      </main>

      <footer class="colophon">
        <p>MIT License. Built with <a href=${m.framework}>vanilla-mvc</a>. Source and issues on
          <a href=${m.repository}>GitHub</a>.</p>
      </footer>
    </div>
  `,
);
