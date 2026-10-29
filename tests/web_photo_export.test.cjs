"use strict";

const assert = require("node:assert/strict");
const { test } = require("node:test");
const { readFileSync } = require("node:fs");
const { runInNewContext } = require("node:vm");
const { photoCrop, PHOTO_SIZES, customPhotoSize } = require("../src/trueme/web/static/photo-export.js");

test("custom sizes convert millimeters to pixels and reject invalid dimensions", () => {
  assert.deepEqual(customPhotoSize("152.4", "101.6"), {
    width: 1800, height: 1200, mm: "152.4 × 101.6", widthMM: 152.4, heightMM: 101.6,
  });
  for (const value of ["", "NaN", "Infinity", "-1", "9", "301"]) {
    assert.equal(customPhotoSize(value, "35"), null);
    assert.equal(customPhotoSize("25", value), null);
  }
});

test("portrait and landscape crops preserve aspect ratio and stay inside the source", () => {
  for (const [width, height] of [[1600, 1200], [900, 1600]]) {
    for (const size of Object.values(PHOTO_SIZES)) {
      const ratio = size.width / size.height;
      const centered = photoCrop(width, height, ratio, 1, 0.5, 0.5);
      assert.ok(Math.abs(centered.width / centered.height - ratio) < 1e-10);
      assert.ok(Math.abs(centered.x * 2 + centered.width - width) < 1e-10);
      assert.ok(Math.abs(centered.y * 2 + centered.height - height) < 1e-10);
      const zoomed = photoCrop(width, height, ratio, 2, 1, 1);
      assert.equal(zoomed.width, centered.width / 2);
      assert.ok(Math.abs(zoomed.x + zoomed.width - width) < 1e-10);
      assert.ok(Math.abs(zoomed.y + zoomed.height - height) < 1e-10);
    }
  }
});

const settle = () => new Promise((resolve) => setImmediate(resolve));

function editor({ fail = false } = {}) {
  const nodes = new Map();
  const requests = [];
  const draws = [];
  const fills = [];
  const downloads = [];
  const pixels = { type: "image/png" };
  const document = {
    body: { append() {} },
    getElementById(id) {
      if (!nodes.has(id)) nodes.set(id, Object.assign(new EventTarget(), {
        value: "", hidden: false, disabled: false,
        showModal() { this.open = true; },
        getContext: () => ({ fillRect(...args) { fills.push(args); }, drawImage(...args) { draws.push(args); } }),
        toBlob: (callback) => callback(pixels),
      }));
      return nodes.get(id);
    },
    createElement: () => ({
      click() { downloads.push(this.download); }, remove() {},
    }),
  };
  document.getElementById("reference-preview").src = "blob:original-reference";
  document.getElementById("reference-preview").dataset = { filename: "张三 工作照.v2.PNG" };
  document.getElementById("photo-size").value = "one-inch";
  document.getElementById("photo-format").value = "jpeg";
  runInNewContext(readFileSync(`${__dirname}/../src/trueme/web/static/photo-export.js`, "utf8"), {
    document, AbortController,
    Image: class {
      complete = true;
      naturalWidth = 1600;
      naturalHeight = 1200;
      async decode() {}
    },
    fetch: async (url, options) => {
      requests.push({ url, options });
      if (fail) throw new TypeError("Failed to fetch");
      return { ok: true, blob: async () => ({ type: url.endsWith("format=png") ? "image/png" : "image/jpeg" }) };
    },
    URL: { createObjectURL: () => "blob:jpeg", revokeObjectURL() {} },
    setTimeout: (callback) => callback(),
  });
  return { nodes, requests, draws, fills, downloads, pixels };
}

test("exports the reference crop only after an explicit download click", async () => {
  const { nodes, requests, draws, downloads, pixels } = editor();
  nodes.get("photo-export").dispatchEvent(new Event("click"));
  await settle();
  assert.equal(requests.length, 0);
  assert.equal(draws[0][0].src, "blob:original-reference");
  assert.deepEqual(draws[0].slice(-4), [0, 0, 295, 413]);
  nodes.get("photo-size").value = "two-inch";
  nodes.get("photo-size").dispatchEvent(new Event("input"));
  assert.deepEqual(draws.at(-1).slice(-4), [0, 0, 413, 579]);
  nodes.get("photo-download").dispatchEvent(new Event("click"));
  await settle();
  assert.equal(requests[0].url, "/api/photo-export?size=two-inch&format=jpeg");
  assert.equal(requests[0].options.method, "POST");
  assert.equal(requests[0].options.body, pixels);
  assert.deepEqual(downloads, ["张三 工作照.v2-two-inch.jpg"]);
  assert.equal(nodes.get("reference-preview").src, "blob:original-reference");
  nodes.get("photo-dialog").dispatchEvent(new Event("close"));
  assert.equal(nodes.get("photo-crop").width, 0);
  assert.equal(nodes.get("photo-download").disabled, true);
});

test("a disconnected backend produces no download and allows retry", async () => {
  const { nodes, downloads } = editor({ fail: true });
  nodes.get("photo-export").dispatchEvent(new Event("click"));
  await settle();
  nodes.get("photo-download").dispatchEvent(new Event("click"));
  await settle();
  assert.deepEqual(downloads, []);
  assert.equal(nodes.get("photo-download").disabled, false);
  assert.equal(nodes.get("photo-export-status").textContent, "Failed to fetch");
});

test("custom dimensions disable invalid exports and download the requested landscape size", async () => {
  const { nodes, requests, downloads, draws } = editor();
  nodes.get("photo-export").dispatchEvent(new Event("click"));
  await settle();
  nodes.get("photo-size").value = "custom";
  nodes.get("photo-width").value = "";
  nodes.get("photo-height").value = "101.6";
  nodes.get("photo-size").dispatchEvent(new Event("input"));
  assert.equal(nodes.get("photo-custom-size").hidden, false);
  assert.equal(nodes.get("photo-download").disabled, true);
  nodes.get("photo-width").value = "152.4";
  nodes.get("photo-width").dispatchEvent(new Event("input"));
  assert.equal(nodes.get("photo-download").disabled, false);
  assert.deepEqual(draws.at(-1).slice(-4), [0, 0, 1800, 1200]);
  nodes.get("photo-download").dispatchEvent(new Event("click"));
  await settle();
  assert.equal(requests[0].url, "/api/photo-export?size=custom&width_mm=152.4&height_mm=101.6&format=jpeg");
  assert.deepEqual(downloads, ["张三 工作照.v2-152.4x101.6mm.jpg"]);
});

test("PNG preserves an unfilled canvas and uses the original filename with png extension", async () => {
  const { nodes, requests, downloads, fills } = editor();
  nodes.get("photo-export").dispatchEvent(new Event("click"));
  await settle();
  assert.equal(fills.length, 1);
  nodes.get("photo-format").value = "png";
  nodes.get("photo-format").dispatchEvent(new Event("input"));
  assert.equal(fills.length, 1);
  assert.equal(nodes.get("photo-download").textContent, "Download PNG");
  nodes.get("photo-download").dispatchEvent(new Event("click"));
  await settle();
  assert.equal(requests[0].url, "/api/photo-export?size=one-inch&format=png");
  assert.deepEqual(downloads, ["张三 工作照.v2-one-inch.png"]);
  nodes.get("photo-format").value = "jpeg";
  nodes.get("photo-format").dispatchEvent(new Event("input"));
  assert.equal(fills.length, 2);
});
