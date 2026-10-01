"use strict";

// ---- element refs ----
const $ = (id) => document.getElementById(id);
const els = {
  textModel: $("text-model"), imageModel: $("image-model"), creativity: $("creativity"),
  basePrompt: $("base-prompt"), remix: $("remix-phrases"),
  width: $("width"), height: $("height"), seed: $("seed"),
  play: $("btn-play"), pause: $("btn-pause"),
  dot: $("status-dot"), status: $("status-text"),
  grid: $("image-grid"), error: $("error-banner"),
  lightbox: $("lightbox"), lbImg: $("lb-img"), lbMeta: $("lb-meta"),
  lbClose: $("lb-close"), lbUse: $("lb-use"), lbDownload: $("lb-download"),
};

// ---- state ----
let generating = false;      // is the continuous loop running?
let loopToken = 0;           // bumped to cancel in-flight loops
let lightboxWasGenerating = false; // resume after closing lightbox?
let currentLightbox = null;   // image object shown in lightbox

const images = [];           // every generated image, kept for download

// ---- startup config ----
async function loadConfig() {
  try {
    const [crRes, modRes] = await Promise.all([
      fetch("/api/creativity").then(r => r.json()),
      fetch("/api/models").then(r => r.json()).catch(() => ({ models: [] })),
    ]);
    els.creativity.innerHTML = "";
    for (const l of crRes.levels) {
      const o = document.createElement("option");
      o.value = l.id; o.textContent = l.label;
      if (l.id === crRes.default) o.selected = true;
      els.creativity.appendChild(o);
    }
    if (modRes.models && modRes.models.length) {
      fillModels(els.textModel, modRes.models, "gpt");
      fillModels(els.imageModel, modRes.models, "dall-e");
    } else {
      // provider unreachable — leave free-text-less selects but allow typing base prompt
      markError("Could not fetch model list from provider. Check .env / PROVIDER_BASE_URL.");
      fillModels(els.textModel, [], "");
      fillModels(els.imageModel, [], "");
    }
  } catch (e) {
    markError("Config load failed: " + e);
  }
}

function fillModels(select, models, preferSubstring) {
  select.innerHTML = "";
  if (!models.length) {
    const o = document.createElement("option");
    o.textContent = "(no models)"; o.disabled = true; o.selected = true;
    select.appendChild(o);
    return;
  }
  const preferred = models.find(m => m.toLowerCase().includes(preferSubstring));
  for (const m of models) {
    const o = document.createElement("option");
    o.value = m; o.textContent = m;
    if (m === preferred) o.selected = true;
    select.appendChild(o);
  }
  if (!preferred && models.length) select.firstChild.selected = true;
}

function markError(msg) {
  els.error.textContent = msg;
  els.error.classList.add("is-visible");
}
function clearError() { els.error.classList.remove("is-visible"); }

// ---- generation loop ----
function setGenerating(on) {
  generating = on;
  els.dot.classList.toggle("is-generating", on);
  els.status.textContent = on ? "Generating" : "Paused";
  els.play.classList.toggle("is-active", on);
  els.pause.classList.toggle("is-active", !on);
}

async function loop(myToken) {
  while (generating && myToken === loopToken) {
    const req = {
      text_model: els.textModel.value,
      image_model: els.imageModel.value,
      base_prompt: els.basePrompt.value,
      remix_phrases: els.remix.value.split("\n").map(s => s.trim()).filter(Boolean),
      creativity: els.creativity.value,
      width: parseInt(els.width.value, 10) || 1024,
      height: parseInt(els.height.value, 10) || 1024,
      seed: parseSeed(),
    };
    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({})).then(d => d.detail || res.statusText);
        throw new Error(detail);
      }
      const data = await res.json();
      addImage(data);
      clearError();
    } catch (e) {
      markError("Generation failed: " + (e.message || e));
      // back off briefly so a persistent error doesn't hammer the provider
      await sleep(2000);
    }
  }
}

function parseSeed() {
  const v = els.seed.value.trim();
  if (v === "") return null;
  const n = parseInt(v, 10);
  return Number.isFinite(n) ? n : null;
}

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// ---- image rendering ----
function addImage(data) {
  const idx = images.length + 1;
  const item = { ...data.metadata, image: data.image, idx };
  images.push(item);

  const card = document.createElement("div");
  card.className = "card-post";

  const imgWrap = document.createElement("div");
  imgWrap.className = "card-image";

  const img = document.createElement("img");
  img.src = data.image;
  img.alt = data.metadata.prompt;
  imgWrap.appendChild(img);

  const useOverlay = document.createElement("div");
  useOverlay.className = "use-overlay";
  useOverlay.textContent = "Use as Base Prompt";
  imgWrap.appendChild(useOverlay);

  const badge = document.createElement("div");
  badge.className = "badge-overlay";
  const dlBtn = document.createElement("button");
  dlBtn.className = "icon-btn"; dlBtn.textContent = "⬇"; dlBtn.title = "Download";
  const expBtn = document.createElement("button");
  expBtn.className = "icon-btn"; expBtn.textContent = "⤢"; expBtn.title = "Inspect";
  badge.appendChild(expBtn); badge.appendChild(dlBtn);
  imgWrap.appendChild(badge);

  const eyebrow = document.createElement("div");
  eyebrow.className = "card-eyebrow";
  eyebrow.textContent = `Image ${idx} · ${data.metadata.image_model} · ${data.metadata.size} · seed ${data.metadata.seed} · ${data.metadata.creativity_label}`;

  const promptEl = document.createElement("div");
  promptEl.className = "card-prompt";
  promptEl.textContent = data.metadata.prompt;

  card.appendChild(imgWrap);
  card.appendChild(eyebrow);
  card.appendChild(promptEl);

  // click image (not badges) -> inspect lightbox; badges handle their own actions
  imgWrap.addEventListener("click", (ev) => {
    if (ev.target.closest(".badge-overlay")) return;
    openLightbox(item);
  });
  dlBtn.addEventListener("click", (ev) => { ev.stopPropagation(); download(item); });
  expBtn.addEventListener("click", (ev) => { ev.stopPropagation(); openLightbox(item); });

  els.grid.prepend(card);
}

// ---- lightbox (pauses generation while open) ----
function openLightbox(item) {
  currentLightbox = item;
  lightboxWasGenerating = generating;
  if (generating) setGenerating(false);   // opening lightbox pauses the loop
  loopToken++;                             // cancel in-flight loop iteration

  els.lbImg.src = item.image;
  els.lbMeta.innerHTML = "";
  for (const [label, key] of [
    ["Prompt", "prompt"], ["Base Prompt", "base_prompt"],
    ["Remix Phrases", "remix_phrases"], ["Text Model", "text_model"],
    ["Image Model", "image_model"], ["Size", "size"], ["Seed", "seed"],
    ["Creativity", "creativity_label"],
  ]) {
    const row = document.createElement("div");
    row.className = "meta-row";
    const lab = document.createElement("div"); lab.className = "meta-label"; lab.textContent = label;
    const val = document.createElement("div"); val.className = "meta-value";
    const v = item[key];
    val.textContent = Array.isArray(v) ? v.join(", ") : String(v);
    row.appendChild(lab); row.appendChild(val);
    els.lbMeta.appendChild(row);
  }
  els.lightbox.classList.add("is-open");
}

function closeLightbox() {
  els.lightbox.classList.remove("is-open");
  els.lbImg.src = "";
  currentLightbox = null;
  if (lightboxWasGenerating) setGenerating(true);  // resume if it was running
}

// ---- promote an image's prompt to the new base prompt ----
function useAsBase(item) {
  els.basePrompt.value = item.prompt;
  // feedback: briefly highlight the field
  els.basePrompt.focus();
}

// ---- download (image + accompanying metadata sidecar) ----
function download(item) {
  // PNG with metadata embedded as tEXt chunks, so a single file carries it.
  const png = embedPngText(item.image, {
    prompt: item.prompt, "base prompt": item.base_prompt,
    model: item.image_model, size: item.size, seed: String(item.seed),
    creativity: item.creativity_label, "text model": item.text_model,
    "remix phrases": (item.remix_phrases || []).join(" | "),
  });
  triggerDownload(png, `image-${item.idx}-${item.seed}.png`);
}

function triggerDownload(dataUrl, filename) {
  const a = document.createElement("a");
  a.href = dataUrl; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
}

// Minimal PNG tEXt-chunk inserter: inserts chunks right after IHDR so the
// metadata travels inside the (still perfectly viewable) PNG file.
function embedPngText(dataUrl, texts) {
  const b64 = dataUrl.split(",")[1];
  const binStr = atob(b64);
  const bytes = new Uint8Array(binStr.length);
  for (let i = 0; i < binStr.length; i++) bytes[i] = binStr.charCodeAt(i);
  const sig = bytes.subarray(0, 8);
  // first chunk after signature = IHDR (length 13 + type + data + crc = 25 bytes)
  const ihdrEnd = 8 + 4 + 4 + 13 + 4;
  const before = bytes.subarray(0, ihdrEnd);
  const after = bytes.subarray(ihdrEnd);

  const enc = new TextEncoder();
  let chunkBlob = new Uint8Array(0);
  for (const [key, val] of Object.entries(texts)) {
    const kw = enc.encode(key);
    const tx = enc.encode(String(val));
    const data = new Uint8Array(kw.length + 1 + tx.length);
    data.set(kw, 0); data[kw.length] = 0; data.set(tx, kw.length + 1);
    chunkBlob = concat(chunkBlob, makeChunk("tEXt", data));
  }
  const out = new Uint8Array(before.length + chunkBlob.length + after.length);
  out.set(before, 0); out.set(chunkBlob, before.length); out.set(after, before.length + chunkBlob.length);
  // re-verify PNG signature preserved (it is — we never touched it)
  void sig;
  return "data:image/png;base64," + bytesToBase64(out);
}

// Chunk-safe base64: avoids spreading a huge array into String.fromCharCode,
// which would blow the call stack for large PNGs.
function bytesToBase64(bytes) {
  const CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  let out = "";
  for (let i = 0; i < bytes.length; i += 0x8000) {
    const slice = bytes.subarray(i, Math.min(i + 0x8000, bytes.length));
    let bin = "";
    for (let j = 0; j < slice.length; j++) bin += String.fromCharCode(slice[j]);
    out += btoa(bin);
  }
  return out;
}

function makeChunk(type, data) {
  const typeBytes = encAscii(type);
  const len = new Uint8Array(4);
  new DataView(len.buffer).setUint32(0, data.length, false);
  const crc = new Uint8Array(4);
  new DataView(crc.buffer).setUint32(0, crc32(concat(typeBytes, data)), false);
  return concat(concat(len, typeBytes), concat(data, crc));
}

function encAscii(s) {
  const a = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i) & 0x7f;
  return a;
}

function concat(a, b) {
  const out = new Uint8Array(a.length + b.length);
  out.set(a, 0); out.set(b, a.length);
  return out;
}

// standard PNG CRC32 (poly 0xEDB88320)
const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    t[n] = c >>> 0;
  }
  return t;
})();
function crc32(bytes) {
  let c = 0xFFFFFFFF;
  for (let i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

// ---- wire up controls ----
els.play.addEventListener("click", () => {
  if (generating) return;
  setGenerating(true);
  loopToken++;
  loop(loopToken);
});
els.pause.addEventListener("click", () => {
  setGenerating(false);
  loopToken++;   // stop the in-flight loop from starting another generation
});
els.lbClose.addEventListener("click", closeLightbox);
els.lightbox.addEventListener("click", (e) => { if (e.target === els.lightbox) closeLightbox(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && els.lightbox.classList.contains("is-open")) closeLightbox(); });
els.lbUse.addEventListener("click", () => { if (currentLightbox) { useAsBase(currentLightbox); closeLightbox(); } });
els.lbDownload.addEventListener("click", () => { if (currentLightbox) download(currentLightbox); });

loadConfig();