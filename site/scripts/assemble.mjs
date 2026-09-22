// Puts the published site together in _site/: the page, its compiled modules, the vendored
// framework, and the D3 diagrams from ../docs/diagrams. The Pages workflow uploads _site/ as it is.
import { cp, rm } from 'node:fs/promises';
import { join } from 'node:path';

const here = join(import.meta.dirname, '..');
const out = join(here, '_site');

await rm(out, { recursive: true, force: true });
for (const entry of ['index.html', 'styles.css', 'vendor']) {
  await cp(join(here, entry), join(out, entry), { recursive: true });
}
await cp(join(here, '..', 'docs', 'diagrams'), join(out, 'diagrams'), { recursive: true });
await cp(join(here, 'dist'), join(out, 'dist'), {
  recursive: true,
  filter: (source) => !source.endsWith('.d.ts'),
});
console.log(`assembled ${out}`);
