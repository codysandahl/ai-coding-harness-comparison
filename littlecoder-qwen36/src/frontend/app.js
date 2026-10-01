/* Local AI Image Explorer — Frontend App */

const API = ""; // relative to same origin

// ---------- State ----------
let generationRunning = false;
let currentLightboxImage = null;
let lastImageCount = 0;
let pollInterval = null;

// ---------- DOM refs ----------
const $ = (sel) => document.querySelector(sel);
const textModelSelect = $("#text-model");
const imageModelSelect = $("#image-model");
const basePromptArea = $("#base-prompt");
const remixArea = $("#remix-phrases");
const widthInput = $("#width");
const heightInput = $("#height");
const seedInput = $("#seed");
const creativityBtns = document.querySelectorAll("#creativity-buttons .btn-ghost");
const btnPause = $("#btn-pause");
const btnPlay = $("#btn-play");
const statusDot = $("#status-dot");
const statusText = $("#status-text");
const imageGrid = $("#image-grid");
const lightbox = $("#lightbox");
const lightboxImage = $("#lightbox-image");
const lightboxMeta = $("#lightbox-meta");
const lightboxBackdrop = $("#lightbox-backdrop");
const lightboxClose = $("#lightbox-close");
const lightboxUsePrompt = $("#lightbox-use-prompt");
const lightboxDownload = $("#lightbox-download");

// ---------- Init ----------
async function init() {
  await checkProvider();
  await loadModels();
  await loadImages();
  startPolling();
  bindEvents();
}

// ---------- Provider health ----------
async function checkProvider() {
  const warning = $("#provider-warning");
  const urlSpan = $("#provider-url");
  try {
    const resp = await fetch(API + "/api/models");
    if (!resp.ok) throw new Error("models endpoint failed");
    // Models endpoint succeeded — provider is reachable
    warning.style.display = "none";
  } catch {
    // Try to get the base URL from the settings endpoint
    try {
      const resp = await fetch("/api/config/creativity");
      if (resp.ok) {
        // Settings work, but models failed — likely a provider issue
        // We don't know the provider URL from here, just show a generic warning
        urlSpan.textContent = "(check OPENAI_BASE_URL)";
        warning.style.display = "block";
      }
    } catch {
      urlSpan.textContent = "(check OPENAI_BASE_URL)";
      warning.style.display = "block";
    }
  }
}

$("#provider-dismiss").addEventListener("click", () => {
  $("#provider-warning").style.display = "none";
});

// ---------- API helpers ----------
async function api(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error ${res.status}`);
  }
  return res.json();
}

async function loadModels() {
  try {
    const data = await api("/api/models");
    textModelSelect.innerHTML = "";
    imageModelSelect.innerHTML = "";
    if (data.text_models.length) {
      data.text_models.forEach((id) => {
        const o = document.createElement("option");
        o.value = id; o.textContent = id;
        textModelSelect.appendChild(o);
      });
      textModelSelect.value = data.text_models[0];
    }
    if (data.image_models.length) {
      data.image_models.forEach((id) => {
        const o = document.createElement("option");
        o.value = id; o.textContent = id;
        imageModelSelect.appendChild(o);
      });
      imageModelSelect.value = data.image_models[0];
    }
  } catch (e) {
    console.warn("Could not fetch models:", e);
  }
}

async function loadImages() {
  try {
    const data = await api("/api/images");
    lastImageCount = data.images.length;
    renderImages(data.images);
  } catch (e) {
    console.warn("Could not fetch images:", e);
  }
}

// ---------- Rendering ----------
function renderImages(images) {
  imageGrid.innerHTML = "";
  images.forEach((img) => {
    const card = document.createElement("div");
    card.className = "card-post";
    card.innerHTML = `
      <div class="card-image">
        <img src="${img.image_data}" alt="${escapeHtml(img.prompt)}" loading="lazy">
        <div class="use-overlay">Click to view</div>
      </div>
      <div class="card-eyebrow">${escapeHtml(img.model)} · ${img.width}×${img.height} · seed ${img.seed}</div>
      <div class="card-prompt">${escapeHtml(img.prompt)}</div>
    `;
    card.querySelector(".card-image").addEventListener("click", () => {
      openLightbox(img);
    });
    imageGrid.appendChild(card);
  });
}

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

// ---------- Polling ----------
function startPolling() {
  stopPolling();
  pollInterval = setInterval(async () => {
    try {
      const data = await api("/api/images");
      const newCount = data.images.length;
      if (newCount > lastImageCount) {
        // Render only new images at the top
        const newImages = data.images.slice(lastImageCount);
        lastImageCount = newCount;
        prependNewImages(newImages);
      }
    } catch (e) {
      // Silently ignore polling errors
    }
  }, 2000);
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
}

function prependNewImages(images) {
  const fragment = document.createDocumentFragment();
  images.forEach((img) => {
    const card = document.createElement("div");
    card.className = "card-post";
    card.innerHTML = `
      <div class="card-image">
        <img src="${img.image_data}" alt="${escapeHtml(img.prompt)}" loading="lazy">
        <div class="use-overlay">Click to view</div>
      </div>
      <div class="card-eyebrow">${escapeHtml(img.model)} · ${img.width}×${img.height} · seed ${img.seed}</div>
      <div class="card-prompt">${escapeHtml(img.prompt)}</div>
    `;
    card.querySelector(".card-image").addEventListener("click", () => {
      openLightbox(img);
    });
    fragment.appendChild(card);
  });
  // Insert at the beginning
  if (imageGrid.firstChild) {
    imageGrid.insertBefore(fragment, imageGrid.firstChild);
  } else {
    imageGrid.appendChild(fragment);
  }
}

// ---------- Generation control ----------
async function startGeneration() {
  try {
    await api("/api/generation/start", { method: "POST" });
    generationRunning = true;
    updateStatusUI();
  } catch (e) {
    alert(e.message);
  }
}

async function stopGeneration() {
  try {
    await api("/api/generation/stop", { method: "POST" });
    generationRunning = false;
    updateStatusUI();
  } catch (e) {
    console.error("Failed to stop generation:", e);
  }
}

async function updateStatus() {
  try {
    const data = await api("/api/generation/status");
    generationRunning = data.running;
    updateStatusUI();
  } catch (e) {
    // ignore
  }
}

function updateStatusUI() {
  if (generationRunning) {
    statusDot.classList.add("running");
    statusText.textContent = "Generating";
    btnPause.disabled = false;
    btnPlay.classList.remove("is-active");
    btnPause.classList.add("is-active");
  } else {
    statusDot.classList.remove("running");
    statusText.textContent = "Ready";
    btnPause.disabled = true;
    btnPause.classList.remove("is-active");
    btnPlay.classList.add("is-active");
  }
}

// ---------- Settings ----------
async function updateSettings() {
  try {
    await api("/api/session", {
      method: "PATCH",
      body: JSON.stringify({
        base_prompt: basePromptArea.value,
        remix_phrases: remixArea.value,
        text_model: textModelSelect.value,
        image_model: imageModelSelect.value,
        width: widthInput.value,
        height: heightInput.value,
        seed_override: seedInput.value,
        creativity_level: currentCreativity,
      }),
    });
  } catch (e) {
    console.warn("Failed to update settings:", e);
  }
}

// ---------- Creativity ----------
let currentCreativity = "normal";

creativityBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    creativityBtns.forEach((b) => b.classList.remove("is-active"));
    btn.classList.add("is-active");
    currentCreativity = btn.dataset.level;
    updateSettings();
  });
});

// ---------- Lightbox ----------
function openLightbox(img) {
  currentLightboxImage = img;
  lightboxImage.src = img.image_data;

  const date = new Date(img.timestamp * 1000).toLocaleString();
  lightboxMeta.innerHTML = `
    <dl>
      <dt>Prompt</dt><dd>${escapeHtml(img.prompt)}</dd>
      <dt>Model</dt><dd>${escapeHtml(img.model)}</dd>
      <dt>Size</dt><dd>${img.width} × ${img.height}</dd>
      <dt>Seed</dt><dd>${img.seed}</dd>
      <dt>Creativity</dt><dd>${img.creativity_level}</dd>
      <dt>Generated</dt><dd>${date}</dd>
    </dl>
  `;

  lightbox.style.display = "flex";
  // Pause generation when lightbox is open
  if (generationRunning) {
    api("/api/lightbox/open", { method: "POST" });
  }
}

function closeLightbox() {
  lightbox.style.display = "none";
  currentLightboxImage = null;
  // Resume generation if it was running
  if (generationRunning) {
    api("/api/lightbox/close", { method: "POST" });
  }
}

lightboxClose.addEventListener("click", closeLightbox);
lightboxBackdrop.addEventListener("click", closeLightbox);

lightboxUsePrompt.addEventListener("click", () => {
  if (currentLightboxImage) {
    basePromptArea.value = currentLightboxImage.prompt;
    updateSettings();
    closeLightbox();
    if (generationRunning) {
      stopGeneration();
      startGeneration();
    }
  }
});

lightboxDownload.addEventListener("click", () => {
  if (currentLightboxImage) {
    window.open(`/api/download/${currentLightboxImage.id}`, "_blank");
  }
});

// Keyboard: Escape to close lightbox
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && lightbox.style.display !== "none") {
    closeLightbox();
  }
});

// ---------- Event binding ----------
function bindEvents() {
  // Play / Pause
  btnPlay.addEventListener("click", () => {
    if (!generationRunning) startGeneration();
  });

  btnPause.addEventListener("click", () => {
    if (generationRunning) stopGeneration();
  });

  // Debounced settings update
  let settingsTimeout = null;
  function debouncedUpdate() {
    clearTimeout(settingsTimeout);
    settingsTimeout = setTimeout(updateSettings, 500);
  }

  basePromptArea.addEventListener("input", debouncedUpdate);
  remixArea.addEventListener("input", debouncedUpdate);
  widthInput.addEventListener("change", debouncedUpdate);
  heightInput.addEventListener("change", debouncedUpdate);
  seedInput.addEventListener("change", debouncedUpdate);
  textModelSelect.addEventListener("change", debouncedUpdate);
  imageModelSelect.addEventListener("change", debouncedUpdate);

  // Initial settings load
  updateSettings();
}

// ---------- Boot ----------
init();
