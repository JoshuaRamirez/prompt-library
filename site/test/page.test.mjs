// The published page, driven in headless Chrome through vanilla-mvc/testing: served under
// /prompt-library/ as GitHub Pages serves it, searched, chosen from and filled in.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { launch, serve } from 'vanilla-mvc/testing';

test('the demo searches, chooses and fills in a prompt', async (t) => {
  let browser;
  try { browser = await launch(); } catch (error) {
    return t.skip(`no Chrome to drive: ${error.message}`);
  }
  const server = await serve({ args: ['server.mjs'], env: { PORT: '0' }, cwd: new URL('..', import.meta.url).pathname });
  const page = await browser.newPage();
  const clearSearch = () => page.evaluate(`(() => { const i = document.querySelector('.search input');
    i.value = ''; i.dispatchEvent(new Event('input', { bubbles: true })); })()`);
  try {
    await page.goto(`${server.url}/prompt-library/`);
    await page.waitFor('.hit');

    assert.equal(await page.count('.hit'), 3, 'the first query, review, matches three prompts');
    assert.equal(await page.text('.hit.chosen .title'), 'Code review checklist');
    assert.match(await page.text('.status'), /2 blanks left/);
    assert.equal(await page.attribute('.prompt-composer .copy', 'disabled'), '', 'nothing to copy while blanks are empty');

    await clearSearch();
    await page.type('.search input', 'git');
    assert.equal(await page.count('.hit'), 2);
    assert.equal(await page.text('.hit.chosen .title'), 'Commit message from a diff', 'the best hit is chosen when the old one drops out');

    await page.type('input.blank[name="style"]', 'Conventional Commits');
    await page.type('input.blank[name="max_length"]', '50');
    assert.equal(await page.text('.status'), 'Ready to send.');
    assert.match(await page.text('.output-text'), /in the Conventional Commits format\. Keep the subject under 50 characters/);
    assert.equal(await page.attribute('.prompt-composer .copy', 'disabled'), null);

    await page.click('.hit[data-key="release-notes"]');
    assert.equal(await page.text('.prompt-composer .title'), 'Release notes from commits');
    assert.equal(await page.value('input.blank[name="last_tag"]'), '', 'a new prompt starts with empty blanks');

    await clearSearch();
    await page.type('.search input', 'zzz');
    assert.equal(await page.count('.hit'), 0);
    assert.match(await page.text('.empty'), /Nothing matches “zzz”/);

    const diagrams = await page.evaluate(`fetch('diagrams/').then((r) => r.status)`);
    assert.equal(diagrams, 200, 'the diagrams ship alongside the page');
    assert.deepEqual(await page.errors(), []);
  } finally {
    await page.close();
    await browser.close();
    await server.stop();
  }
});
