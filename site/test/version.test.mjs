// The page shows the plugin's version; it must be the one plugin.json declares.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('the page shows the version in plugin.json', async () => {
  const plugin = JSON.parse(await readFile(new URL('../../.claude-plugin/plugin.json', import.meta.url), 'utf8'));
  const controller = await readFile(new URL('../src/components/site-page/site-page.controller.ts', import.meta.url), 'utf8');
  assert.match(controller, new RegExp(`version: '${plugin.version.replaceAll('.', '\\.')}'`));
});
