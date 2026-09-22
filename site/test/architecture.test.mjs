// This application's architecture, checked by vanilla-mvc's own rules on the syntax tree.
// `npx vanilla-mvc rules` prints each with its reason and a wrong and right example.
//
// `atLeast` is a floor per rule, counted on src/ as it stands. Raise it as the application grows,
// never lower it: a rule that finds nothing to check is a rule that is not running.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { applicationRules } from 'vanilla-mvc/architecture';

applicationRules({
  test,
  assert,
  base: new URL('..', import.meta.url).pathname,
  root: 'src',
  app: 'src/',
  within: ['vanilla-mvc', 'src/'],
  styling: { folder: 'vanilla-mvc/css', from: /\.(template|style)\.ts$/ },
  events: ['src/events'],
  atLeast: { models: 4, events: 4, controllers: 4, handlers: 4, waits: 1, calls: 1, tags: 1 },
});
