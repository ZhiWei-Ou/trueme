"use strict";

const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { test } = require("node:test");
const { createContext, runInContext } = require("node:vm");
const source = readFileSync(`${__dirname}/../src/trueme/web/static/app.js`, "utf8");

test("a failed frame request clears the previous face box", async () => {
  let boxVisible = false;
  const drawing = {
    strokeRect() { boxVisible = true; },
    clearRect(...bounds) {
      assert.deepEqual(bounds, [0, 0, 640, 480]);
      boxVisible = false;
    },
  };
  const nodes = new Map();
  const context = createContext({
    document: {
      querySelector: () => null,
      getElementById(id) {
        if (!nodes.has(id)) nodes.set(id, Object.assign(new EventTarget(), {
          style: {}, classList: { toggle() {} }, replaceChildren() {}, getContext: () => drawing,
          videoWidth: 640, videoHeight: 480,
        }));
        return nodes.get(id);
      },
      createElement: () => ({
        getContext: () => ({ drawImage() {} }),
        toBlob: (callback) => callback({ type: "image/jpeg" }),
      }),
    },
    navigator: {},
    performance,
    fetch: async (path) => {
      if (path === "/api/status") {
        return { ok: true, json: async () => ({ reference_set: false }) };
      }
      throw new TypeError("Failed to fetch");
    },
    setTimeout(callback) {
      runInContext("running = false", context);
      callback();
    },
  });
  runInContext(source, context);
  runInContext(`
    running = true;
    showFrame({frame: {width: 640, height: 480}, faces: 1, face: [10, 20, 100, 100],
               cosine_similarity: 0.6, quality_warnings: []});
  `, context);
  assert.equal(boxVisible, true);
  await runInContext("loop()", context);
  assert.equal(boxVisible, false);
});
