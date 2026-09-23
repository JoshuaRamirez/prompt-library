// Puts the published site together in _site/: the page, its compiled modules, the vendored
// framework, fonts, and the D3 diagrams from ../docs/diagrams. The Pages workflow uploads _site/.
//
// The page is some sixty small ES modules. Left alone, the browser finds them one import at a
// time, so the page loads as a waterfall; index.html gets a modulepreload link for every module
// main.js reaches statically, and the browser fetches them all at once.
import { cp, readFile, rm, writeFile } from 'node:fs/promises';
import { dirname, join, relative, resolve } from 'node:path';

const here = join(import.meta.dirname, '..');
const out = join(here, '_site');

await rm(out, { recursive: true, force: true });
for (const entry of ['index.html', 'styles.css', 'favicon.svg', 'social.png', 'fonts', 'vendor']) {
  await cp(join(here, entry), join(out, entry), { recursive: true });
}
await cp(join(here, 'dist'), join(out, 'dist'), { recursive: true, filter: (source) => !source.endsWith('.d.ts') });
await cp(join(here, '..', 'docs', 'diagrams'), join(out, 'diagrams'), { recursive: true });

const page = await readFile(join(out, 'index.html'), 'utf8');
const { imports } = JSON.parse(page.match(/<script type="importmap">([\s\S]*?)<\/script>/)[1]);
const IMPORT = /\b(?:import|export)\s*(?:[\w*{}\s,$]*?\bfrom\s*)?['"]([^'"]+)['"]/g;

function locate(specifier, from) {
  if (specifier.startsWith('.')) return resolve(dirname(from), specifier);
  const mapped = imports[specifier];
  if (!mapped) throw new Error(`assemble: ${relative(out, from)} imports "${specifier}", which the import map does not name`);
  return resolve(out, mapped);
}

const reached = new Set();
async function walk(file) {
  if (reached.has(file)) return;
  reached.add(file);
  const source = await readFile(file, 'utf8');
  for (const [, specifier] of source.matchAll(IMPORT)) await walk(locate(specifier, file));
}
const entry = join(out, 'dist', 'main.js');
await walk(entry);
reached.delete(entry);

const links = [...reached].map((file) => `    <link rel="modulepreload" href="${relative(out, file)}" />`).sort().join('\n');
const tag = '    <script type="module" src="dist/main.js"></script>';
if (!page.includes(tag)) throw new Error('assemble: index.html no longer loads dist/main.js as expected');
await writeFile(join(out, 'index.html'), page.replace(tag, `${links}\n${tag}`));
console.log(`assembled ${relative(process.cwd(), out) || out}: ${reached.size} modules preloaded`);
