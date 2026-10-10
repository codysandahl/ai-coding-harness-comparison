const $ = (id) => document.getElementById(id);
const els = {
  textModel: $("textModel"), imageModel: $("imageModel"), base: $("base"), remix: $("remix"),
  creativity: $("creativity"), width: $("width"), height: $("height"), seed: $("seed"),
  toggle: $("toggle"), error: $("error"), grid: $("grid"), empty: $("empty"),
  lightbox: $("lightbox"), lbImg: $("lbImg"), lbMeta: $("lbMeta"),
  lbDownload: $("lbDownload"), lbClose: $("lbClose"),
};

const state = {
  running: false,
  runId: 0,
  ctrl: null,
  prefetch: null,   // {base, promise} of the next prompt, started while the current image renders
  recent: [],       // recent prompts sent back to the server to avoid repeats
  current: null,    // image shown in lightbox: {blob, meta}
};

// ---------- setup ----------

async function loadSetup() {
  const [models, levels] = await Promise.all([
    fetch("/api/models").then((r) => r.json()),
    fetch("/api/creativity").then((r) => r.json()),
  ]);
  for (const sel of [els.textModel, els.imageModel]) {
    sel.innerHTML = models.models.map((m) => `<option>${m}</option>`).join("");
  }
  // Backend only sends a default when it is set in env and present in the provider's list.
  if (models.defaultText) els.textModel.value = models.defaultText;
  if (models.defaultImage) els.imageModel.value = models.defaultImage;
  els.creativity.innerHTML = levels.levels.map((l) => `<option>${l}</option>`).join("");
  els.creativity.value = levels.levels.includes("normal") ? "normal" : levels.levels[0];
}

// ---------- helpers ----------

function showError(msg) { els.error.textContent = msg || ""; }

async function post(url, body, signal) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || `Request failed (${r.status})`);
  return data;
}

function remixPhrases() {
  return els.remix.value.split("\n").map((s) => s.trim()).filter(Boolean);
}

function base64ToBlob(b64, mime) {
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  return new Blob([bytes], { type: mime });
}

// ---------- generation loop ----------

function fetchPrompt(base, signal) {
  return post("/api/prompt", {
    base,
    remix: remixPhrases(),
    creativity: els.creativity.value,
    model: els.textModel.value,
    recent: state.recent,
  }, signal);
}

// Attach a no-op catch so an aborted, never-awaited prefetch does not raise an unhandled rejection.
function startPrefetch(signal) {
  const base = els.base.value.trim();
  const promise = fetchPrompt(base, signal).then((d) => d.prompt);
  promise.catch(() => {});
  return { base, promise };
}

async function loop(runId) {
  const signal = state.ctrl.signal;
  while (state.running && runId === state.runId) {
    try {
      // Reuse the prefetched prompt only if the base prompt has not changed since it was requested.
      const pre = state.prefetch && state.prefetch.base === els.base.value.trim()
        ? state.prefetch
        : startPrefetch(signal);
      state.prefetch = null;
      const prompt = await pre.promise;
      if (runId !== state.runId) break;

      state.prefetch = startPrefetch(signal); // next prompt generates while this image renders
      const seedValue = els.seed.value.trim();
      const meta = {
        model: els.imageModel.value,
        size: `${els.width.value}x${els.height.value}`,
        seed: seedValue === "" ? Math.floor(Math.random() * 2 ** 31) : Number(seedValue),
        creativity: els.creativity.value,
        prompt,
      };
      const img = await post("/api/image", {
        prompt, model: meta.model, size: meta.size, seed: meta.seed,
      }, signal);
      if (runId !== state.runId) break;

      addTile(base64ToBlob(img.b64, img.mime), meta);
      state.recent.push(prompt);
      state.recent = state.recent.slice(-5);
      showError("");
    } catch (err) {
      if (err.name === "AbortError") break;
      showError(err.message);
      stop();
      break;
    }
  }
}

function start() {
  if (!els.base.value.trim()) return showError("Enter a base prompt first.");
  if (!els.imageModel.value || !els.textModel.value) return showError("Choose both models.");
  showError("");
  state.running = true;
  state.runId++;
  state.ctrl = new AbortController();
  state.prefetch = null;
  els.toggle.textContent = "Pause";
  loop(state.runId);
}

function stop() {
  state.running = false;
  state.runId++;
  if (state.ctrl) state.ctrl.abort();
  state.prefetch = null;
  els.toggle.textContent = "Start";
}

els.toggle.addEventListener("click", () => (state.running ? stop() : start()));

// ---------- grid ----------

function addTile(blob, meta) {
  const url = URL.createObjectURL(blob);
  const fig = document.createElement("figure");
  fig.className = "tile";
  fig.innerHTML = `<img alt=""><button class="expand" type="button">Expand</button>
    <figcaption></figcaption>`;
  const img = fig.querySelector("img");
  img.src = url;
  fig.querySelector("figcaption").textContent = `seed ${meta.seed} · ${meta.creativity}`;

  // Click the image to promote its prompt; Expand opens the lightbox.
  img.addEventListener("click", () => promote(meta.prompt));
  fig.querySelector(".expand").addEventListener("click", () => openLightbox(blob, meta));

  els.empty.hidden = true;
  els.grid.prepend(fig);
}

function promote(prompt) {
  els.base.value = prompt;
  // Discard a prefetched prompt built from the old base; the loop will refetch on its next turn.
  state.prefetch = null;
  showError("");
}

// ---------- lightbox ----------

function openLightbox(blob, meta) {
  stop(); // opening the lightbox pauses generation
  state.current = { blob, meta };
  els.lbImg.src = URL.createObjectURL(blob);
  els.lbMeta.innerHTML = [
    ["Model", meta.model], ["Size", meta.size], ["Seed", meta.seed],
    ["Creativity", meta.creativity], ["Prompt", meta.prompt],
  ].map(([k, v]) => `<dt>${k}</dt><dd>${escapeHtml(String(v))}</dd>`).join("");
  els.lightbox.hidden = false;
}

function closeLightbox() {
  els.lightbox.hidden = true;
  state.current = null;
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

els.lbClose.addEventListener("click", closeLightbox);
els.lightbox.addEventListener("click", (e) => { if (e.target === els.lightbox) closeLightbox(); });
els.lbDownload.addEventListener("click", () => state.current && download(state.current.blob, state.current.meta));

// ---------- download (only path that writes to disk) ----------

async function download(blob, meta) {
  const png = blob.type === "image/png" ? blob : await toPng(blob);
  saveBlob(png, `image-explorer-${meta.seed}-${Date.now()}.png`);
}

async function toPng(blob) {
  const bitmap = await createImageBitmap(blob);
  const canvas = document.createElement("canvas");
  canvas.width = bitmap.width;
  canvas.height = bitmap.height;
  canvas.getContext("2d").drawImage(bitmap, 0, 0);
  return new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
}

function saveBlob(blob, filename) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}


loadSetup().catch((e) => showError("Could not load models: " + e.message));
