import { css, Style } from 'vanilla-mvc';
import type { SitePageModel } from './site-page.model.ts';

export const sitePageStyle = new Style<SitePageModel>(
  () => css`
    :scope.site-page {
      max-inline-size: 72rem; margin-inline: auto; padding-inline: clamp(1.25rem, 4vw, 3rem);
    }
    .masthead {
      display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 1rem;
      padding-block: 1.5rem; border-bottom: 1px solid var(--rule);
    }
    .wordmark { font-weight: 800; font-size: 1.1rem; color: var(--ink); text-decoration: none; letter-spacing: -0.01em; }
    nav { display: flex; gap: 1.5rem; }
    nav a { color: var(--ink-soft); text-decoration: none; }
    nav a:hover { color: var(--ink); text-decoration: underline; }

    main > section { padding-block: clamp(3rem, 7vw, 5.5rem); border-bottom: 1px solid var(--rule); }
    main > section:last-child { border-bottom: 0; }

    .hero { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr); gap: clamp(2rem, 5vw, 4.5rem); align-items: end; }
    h1 {
      font-size: clamp(2.9rem, 7.4vw, 5.6rem); line-height: 0.98; letter-spacing: -0.035em;
      font-weight: 800; text-wrap: balance; max-inline-size: 11ch;
    }
    .lede { margin-top: 1.5rem; font-size: clamp(1.1rem, 1.6vw, 1.3rem); line-height: 1.55; color: var(--ink-soft); max-inline-size: 34em; }

    h2 { font-size: clamp(1.7rem, 3vw, 2.3rem); line-height: 1.1; letter-spacing: -0.02em; font-weight: 800; }
    h3 { font-size: 1.15rem; font-weight: 700; }

    .demo { padding-top: clamp(2.5rem, 5vw, 4rem); }
    .demo-head { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 2fr); gap: 2rem; align-items: baseline; margin-bottom: 2rem; }
    .demo-head p { color: var(--ink-soft); max-inline-size: 38em; }
    .demo-grid {
      display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr); gap: clamp(1.5rem, 4vw, 3.5rem);
      padding: clamp(1.25rem, 3vw, 2.25rem); border-radius: 10px;
      background: var(--desk); border: 1px solid var(--rule);
    }

    .ways h2 { margin-bottom: 2rem; }
    .ways-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: clamp(1.5rem, 3vw, 3rem); }
    .way { display: grid; gap: 0.75rem; align-content: start; padding-top: 1rem; border-top: 3px solid var(--ink); }
    .way p { color: var(--ink-soft); }
    .way .example { color: var(--ink); font-size: 1.05rem; }
    .commands { display: grid; grid-template-columns: auto 1fr; gap: 0.4rem 0.9rem; margin: 0; }
    .commands dd { margin: 0; color: var(--ink-soft); }
    .way pre { margin: 0; font: 0.82rem/1.7 var(--mono); overflow-x: auto; padding: 0.9rem 1rem; background: var(--sheet); border: 1px solid var(--rule); border-radius: 6px; }

    .file { display: grid; gap: 1.75rem; }
    .file-text { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 2fr); gap: 2rem; align-items: baseline; }
    .file-text p { color: var(--ink-soft); max-inline-size: 38em; }
    .csv {
      margin: 0; overflow-x: auto; font: 0.8rem/2 var(--mono); padding: 0.4rem 1.25rem 0.4rem 1.75rem;
      background: var(--sheet); border: 1px solid var(--rule); border-radius: 6px;
      background-image: linear-gradient(to right, transparent 1.1rem, var(--margin) 1.1rem, var(--margin) calc(1.1rem + 1px), transparent calc(1.1rem + 1px)),
        repeating-linear-gradient(to bottom, transparent 0 calc(1.6rem - 1px), var(--rule) calc(1.6rem - 1px) 1.6rem);
      background-position: 0 0, 0 0.4rem;
    }

    .machine { display: grid; gap: 1.25rem; max-inline-size: 46rem; }
    .machine ul { display: grid; gap: 0.75rem; padding-left: 1.2rem; }
    .machine li::marker { color: var(--ink-soft); }

    .built { display: grid; gap: 1rem; max-inline-size: 46rem; }
    .built p { color: var(--ink-soft); }

    .colophon { padding-block: 2rem 3rem; border-top: 1px solid var(--rule); color: var(--ink-soft); font-size: 0.9rem; }

    @media (max-width: 860px) {
      .hero, .demo-head, .demo-grid, .file-text, .ways-grid { grid-template-columns: minmax(0, 1fr); }
      .hero { align-items: start; }
    }
  `,
);
