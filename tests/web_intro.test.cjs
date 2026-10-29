"use strict";

const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { test } = require("node:test");
const { runInNewContext } = require("node:vm");
const source = readFileSync(`${__dirname}/../src/trueme/web/static/app.js`, "utf8");

function page({ reducedMotion = false } = {}) {
  let finish;
  const finished = new Promise((resolve) => { finish = resolve; });
  const intro = {
    isConnected: true,
    remove() { this.isConnected = false; },
    getAnimations: () => reducedMotion ? [] : [{ finished }],
  };
  const document = Object.assign(new EventTarget(), {
    hidden: false,
    body: {},
    querySelector: () => intro.isConnected ? intro : null,
    getElementById: () => new EventTarget(),
    createElement: () => ({}),
  });
  document.activeElement = document.body;
  const window = new EventTarget();
  runInNewContext(source, {
    document, window, AbortController, navigator: {},
    fetch: async () => ({ ok: true, json: async () => ({ reference_set: false }) }),
  });
  return { document, window, intro, finish };
}

const settle = () => new Promise((resolve) => setImmediate(resolve));

test("completed opening stays removed across repeated app switches", async () => {
  const { document, window, intro, finish } = page();
  assert.equal(intro.isConnected, true);
  finish();
  await settle();
  for (let i = 0; i < 3; i++) {
    window.dispatchEvent(new Event("blur"));
    window.dispatchEvent(new Event("focus"));
    document.dispatchEvent(new Event("focusin"));
    assert.equal(intro.isConnected, false);
  }
});

test("switching apps during the opening dismisses it permanently", () => {
  const { window, intro } = page();
  window.dispatchEvent(new Event("blur"));
  window.dispatchEvent(new Event("focus"));
  assert.equal(intro.isConnected, false);
});

test("keyboard focus dismisses the opening", () => {
  const { document, intro } = page();
  document.dispatchEvent(new Event("focusin"));
  assert.equal(intro.isConnected, false);
});

test("reduced motion leaves no opening overlay", async () => {
  const { intro } = page({ reducedMotion: true });
  await settle();
  assert.equal(intro.isConnected, false);
});
