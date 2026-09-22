// Serves _site/ the way GitHub Pages does: under /prompt-library/, files only, 404 otherwise.
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, join, normalize, sep } from 'node:path';

const PORT = Number(process.env.PORT ?? 4500);
const ROOT = join(import.meta.dirname, '_site');
const BASE = '/prompt-library/';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.json': 'application/json' };

const server = createServer(async (req, res) => {
  const path = decodeURIComponent(new URL(req.url ?? '/', 'http://localhost').pathname);
  if (path === '/' || path === '/prompt-library') {
    res.writeHead(302, { location: BASE });
    return res.end();
  }
  let file = normalize(join(ROOT, path.slice(BASE.length - 1)));
  try {
    if (!path.startsWith(BASE) || !(file + sep).startsWith(ROOT + sep)) throw new Error('outside');
    if ((await stat(file)).isDirectory()) file = join(file, 'index.html');
    const body = await readFile(file);
    res.writeHead(200, { 'content-type': TYPES[extname(file)] ?? 'application/octet-stream' });
    res.end(body);
  } catch {
    res.writeHead(404, { 'content-type': 'text/plain' });
    res.end('Not found');
  }
});

server.listen(PORT, '127.0.0.1', () => console.log(`http://127.0.0.1:${server.address().port}${BASE}`));
