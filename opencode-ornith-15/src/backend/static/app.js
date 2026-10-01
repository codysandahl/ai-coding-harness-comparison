"use strict";

const els = {
  textModel: document.getElementById("text-model"),
  imageModel: document.getElementById("image-model"),
  basePrompt: document.getElementById("base-prompt"),
  remixPhrases: document.getElementById("remix-phrases"),
  creativity: document.getElementById("creativity"),
  creativityHint: document.getElementById("creativity-hint"),
  width: document.getElementById("width"),
  height: document.getElementById("height"),
  btnPlay: document.getElementById("btn-play"),
  btnPause: document.getElementById("btn-pause"),
  statusText: document.getElementById("status-text"),
  statusWrap: document.querySelector(".nav-status"),
  grid: document.getElementById("image-grid"),
  lightbox: document.getElementById("lightbox"),
  lightboxImg: document.getElementById("lightbox-img"),
  lightboxPrompt: document.getElementById("lightbox-prompt"),
  lbModel: document.getElementById("lb-model"),
  lbSize: document.getElementById("lb-size"),
  lbCreativity: document.getElementById("lb-creativity"),
  lbUse: document.getElementById("lb-use"),
  lbDownload: document.getElementById("lb-download"),
  lbClose: document.getElementById("lb-close"),
};

const MAX_CARDS = 150;
let isRunning = false;
let lightboxWasRunning = false;
let settingsTimer = null;

async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    let detail = "";
    try {
      detail = await res.text();
    } catch (_) {
      /* ignore */
    }
    throw new Error(`${res.status} ${res.statusText} ${detail}`.trim());
  }
  return res.json();
}

function populateSelect(selectEl, items, defaultValue) {
  selectEl.innerHTML = "";
  items.forEach((item) => {
    const opt = document.createElement("option");
    opt.value = item;
    opt.textContent = item;
    selectEl.appendChild(opt);
  });
  if (items.includes(defaultValue)) {
    selectEl.value = defaultValue;
  } else if (items.length) {
    selectEl.value = items[0];
  }
}

function applySettingsToUI(settings) {
  els.basePrompt.value = settings.base_prompt || "";
  els.remixPhrases.value = (settings.remix_phrases || []).join("\n");
  els.width.value = settings.width || 1024;
  els.height.value = settings.height || 1024;
  els.textModel.value = settings.text_model || els.textModel.value;
  els.imageModel.value = settings.image_model || els.imageModel.value;
  if (settings.creativity) {
    els.creativity.value = settings.creativity;
  }
}

function collectSettings() {
  return {
    base_prompt: els.basePrompt.value,
    remix_phrases: els.remixPhrases.value
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean),
    creativity: els.creativity.value,
    width: parseInt(els.width.value, 10) || 1024,
    height: parseInt(els.height.value, 10) || 1024,
    text_model: els.textModel.value,
    image_model: els.imageModel.value,
  };
}

function scheduleSync() {
  clearTimeout(settingsTimer);
  settingsTimer = setTimeout(syncSettings, 400);
}

async function syncSettings() {
  try {
    const updated = await fetchJSON("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectSettings()),
    });
    Object.assign({}, updated);
  } catch (err) {
    toast("Could not save settings: " + err.message);
  }
}

function updateStatus() {
  els.statusText.textContent = isRunning ? "Generating" : "Paused";
  els.statusWrap.classList.toggle("is-running", isRunning);
  els.btnPause.classList.toggle("is-active", !isRunning);
  els.btnPlay.classList.toggle("is-active", isRunning);
}

async function setRunning(running) {
  isRunning = running;
  updateStatus();
  try {
    await fetchJSON("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ running }),
    });
  } catch (err) {
    toast("Could not toggle generation: " + err.message);
  }
}

function toast(message) {
  const node = document.createElement("div");
  node.className = "toast";
  node.textContent = message;
  document.body.appendChild(node);
  setTimeout(() => node.remove(), 4000);
}

function createCard(meta) {
  const card = document.createElement("div");
  card.className = "card-post";

  const wrap = document.createElement("div");
  wrap.className = "card-image";
  const img = document.createElement("img");
  img.alt = meta.prompt;
  img.src = `/api/images/${meta.id}`;
  const overlay = document.createElement("div");
  overlay.className = "use-overlay";
  overlay.textContent = "Use as Base Prompt";
  wrap.append(img, overlay);

  const eyebrow = document.createElement("div");
  eyebrow.className = "card-eyebrow";
  eyebrow.textContent = `${meta.model} · ${meta.size} · ${meta.creativity}`;

  const prompt = document.createElement("div");
  prompt.className = "card-prompt";
  prompt.textContent = meta.prompt;

  card.append(wrap, eyebrow, prompt);
  card.addEventListener("click", () => openLightbox(meta));
  return card;
}

function addImage(meta) {
  const card = createCard(meta);
  els.grid.appendChild(card);
  while (els.grid.children.length > MAX_CARDS) {
    els.grid.removeChild(els.grid.firstElementChild);
  }
}

function connectSSE() {
  const source = new EventSource("/api/events");
  source.onmessage = (event) => {
    let eventObj;
    try {
      eventObj = JSON.parse(event.data);
    } catch (_) {
      return;
    }
    switch (eventObj.type) {
      case "image":
        addImage(eventObj.metadata);
        break;
      case "hint":
        toast(eventObj.detail);
        break;
      case "error":
        toast(eventObj.detail);
        break;
      default:
        break;
    }
  };
  return source;
}

function openLightbox(meta) {
  lightboxWasRunning = isRunning;
  setRunning(false);
  els.lightboxImg.src = `/api/images/${meta.id}`;
  els.lightboxPrompt.textContent = meta.prompt;
  els.lbModel.textContent = meta.model;
  els.lbSize.textContent = meta.size;
  els.lbCreativity.textContent = meta.creativity;
  els.lbDownload.href = `/api/images/${meta.id}/download`;
  els.lightbox.hidden = false;
}

function closeLightbox() {
  els.lightbox.hidden = true;
  els.lightboxImg.src = "";
  setRunning(lightboxWasRunning);
}

function bindLightbox() {
  els.lbUse.addEventListener("click", async () => {
    const prompt = els.lightboxPrompt.textContent;
    if (prompt) {
      els.basePrompt.value = prompt;
      scheduleSync();
    }
    closeLightbox();
  });
  els.lbClose.addEventListener("click", closeLightbox);
  els.lightbox.addEventListener("click", (e) => {
    if (e.target === els.lightbox) closeLightbox();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !els.lightbox.hidden) closeLightbox();
  });
}

function bindControls() {
  els.btnPlay.addEventListener("click", () => setRunning(true));
  els.btnPause.addEventListener("click", () => setRunning(false));
  [els.basePrompt, els.remixPhrases, els.width, els.height].forEach((el) =>
    el.addEventListener("input", scheduleSync),
  );
  els.creativity.addEventListener("change", scheduleSync);
  els.textModel.addEventListener("change", scheduleSync);
  els.imageModel.addEventListener("change", scheduleSync);
}

async function init() {
  try {
    const models = await fetchJSON("/api/models");
    populateSelect(els.textModel, models.text_models, models.defaults.text_model);
    populateSelect(els.imageModel, models.image_models, models.defaults.image_model);
  } catch (err) {
    toast("Could not load models: " + err.message);
  }

  try {
    const crit = await fetchJSON("/api/creativity-levels");
    populateSelect(els.creativity, crit.levels, "normal");
    els.creativity.value = "normal";
    const updateHint = () => {
      els.creativityHint.textContent = crit.descriptions[els.creativity.value] || "";
    };
    updateHint();
    els.creativity.addEventListener("change", () => {
      updateHint();
      scheduleSync();
    });
  } catch (err) {
    toast("Could not load creativity levels: " + err.message);
  }

  try {
    const settings = await fetchJSON("/api/settings");
    applySettingsToUI(settings);
  } catch (err) {
    toast("Could not load settings: " + err.message);
  }

  try {
    const gen = await fetchJSON("/api/generate");
    isRunning = gen.running;
    updateStatus();
    if (isRunning) connectSSE();
  } catch (err) {
    toast("Could not load generation status: " + err.message);
  }

  bindControls();
  bindLightbox();
}

document.addEventListener("DOMContentLoaded", init);
