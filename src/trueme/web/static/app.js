"use strict";

// Thresholds match the README score guide: 0.363 is the published SFace/LFW
// reference; 0.5 is an informal rule of thumb.
const REFERENCE = 0.363;
const COMFORT = 0.5;
const FRAME_WIDTH = 640;
const FRAME_INTERVAL_MS = 200;

const $ = (id) => document.getElementById(id);
const video = $("video");
const overlay = $("overlay");
const capture = document.createElement("canvas");

let stream = null;
let running = false;
let referenceSet = false;

async function api(method, path, body) {
  const options = { method };
  if (body) {
    options.body = body;
    options.headers = { "Content-Type": body.type || "image/jpeg" };
  }
  const response = await fetch(path, options);
  const value = await response.json();
  if (!response.ok) throw new Error(value.error.message);
  return value;
}

function setReferenceState(isSet, message) {
  referenceSet = isSet;
  $("reference-clear").disabled = !isSet;
  $("reference-status").textContent = message;
  if (!isSet) {
    $("reference-preview").hidden = true;
    $("reference-empty").hidden = false;
  }
}

$("reference-input").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  event.target.value = "";
  if (!file) return;
  $("reference-status").textContent = "Analyzing…";
  try {
    const result = await api("POST", "/api/reference", file);
    const preview = $("reference-preview");
    if (preview.src) URL.revokeObjectURL(preview.src);
    preview.src = URL.createObjectURL(file);
    preview.hidden = false;
    $("reference-empty").hidden = true;
    setReferenceState(true, result.quality_warnings.join(" ") || "Reference ready.");
  } catch (error) {
    setReferenceState(referenceSet, error.message);
  }
});

$("reference-clear").addEventListener("click", async () => {
  await api("DELETE", "/api/reference");
  setReferenceState(false, "");
  showScore(null);
});

$("camera-toggle").addEventListener("click", () => (running ? stopCamera() : startCamera()));

async function startCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    $("camera-status").textContent =
      "Camera access needs a secure context: open the page through localhost or 127.0.0.1.";
    return;
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
  } catch (error) {
    $("camera-status").textContent = `Camera unavailable: ${error.message}`;
    return;
  }
  video.srcObject = stream;
  await video.play();
  running = true;
  $("camera-hint").hidden = true;
  $("camera-toggle").textContent = "Stop camera";
  $("camera-status").textContent = "";
  loop();
}

function stopCamera() {
  running = false;
  stream?.getTracks().forEach((track) => track.stop());
  stream = null;
  video.srcObject = null;
  overlay.getContext("2d").clearRect(0, 0, overlay.width, overlay.height);
  $("camera-hint").hidden = false;
  $("camera-toggle").textContent = "Start camera";
  showScore(null);
}

async function loop() {
  while (running) {
    const started = performance.now();
    try {
      showFrame(await api("POST", "/api/frame", await grabFrame()));
    } catch (error) {
      $("camera-status").textContent = error.message;
    }
    const elapsed = performance.now() - started;
    await new Promise((resolve) => setTimeout(resolve, Math.max(0, FRAME_INTERVAL_MS - elapsed)));
  }
}

function grabFrame() {
  const scale = Math.min(1, FRAME_WIDTH / video.videoWidth);
  capture.width = Math.round(video.videoWidth * scale);
  capture.height = Math.round(video.videoHeight * scale);
  capture.getContext("2d").drawImage(video, 0, 0, capture.width, capture.height);
  return new Promise((resolve) => capture.toBlob(resolve, "image/jpeg", 0.85));
}

function showFrame(result) {
  if (!running) return;
  overlay.width = result.frame.width;
  overlay.height = result.frame.height;
  const context = overlay.getContext("2d");
  if (result.face) {
    const [x, y, width, height] = result.face;
    context.lineWidth = Math.max(2, overlay.width / 200);
    context.strokeStyle = scoreColor(result.cosine_similarity);
    context.strokeRect(x, y, width, height);
  }
  if (result.faces === 0) $("camera-status").textContent = "No face in view.";
  else if (result.faces > 1) $("camera-status").textContent = `${result.faces} faces in view; keep exactly one.`;
  else $("camera-status").textContent = referenceSet ? "" : "Choose a reference photo to see a score.";
  showScore(result.cosine_similarity);
  $("warnings").replaceChildren(
    ...result.quality_warnings.map((text) => Object.assign(document.createElement("li"), { textContent: text }))
  );
}

function scoreColor(score) {
  if (score === null) return "#c9cbbf";
  return score >= COMFORT ? "#7fa36b" : score >= REFERENCE ? "#b9c7ad" : "#e0a660";
}

function showScore(score) {
  const marker = $("marker");
  if (score === null) {
    $("score").textContent = "—";
    $("verdict").textContent = "";
    marker.hidden = true;
    return;
  }
  $("score").textContent = score.toFixed(3);
  $("verdict").textContent =
    score >= COMFORT
      ? "Comfortably you — the camera's warming up to you."
      : score >= REFERENCE
        ? "Meets the reference."
        : "Below the reference — camera, let's get acquainted again.";
  marker.hidden = false;
  marker.style.left = `${Math.min(1, Math.max(0, score)) * 100}%`;
}

api("GET", "/api/status").then((status) => {
  if (status.reference_set) setReferenceState(true, "A reference from an earlier visit is loaded.");
});
