import base64
import json
import os
import random
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")

BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.getenv("OPENAI_API_KEY", "")
CREATIVITY_FILE = HERE / "creativity.json"
FRONTEND_DIR = HERE.parent / "frontend"

app = FastAPI()


def headers():
    return {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}


async def call_provider(method, path, **kwargs):
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.request(method, f"{BASE_URL}{path}", headers=headers(), **kwargs)
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Provider unreachable: {exc}")
    if resp.status_code >= 400:
        raise HTTPException(502, f"Provider error {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def load_creativity():
    # Re-read per request so edits to creativity.json apply without restart.
    return json.loads(CREATIVITY_FILE.read_text(encoding="utf-8"))


class PromptRequest(BaseModel):
    base: str
    remix: list[str]
    creativity: str
    model: str
    seed: int | None = None
    recent: list[str] = []


class ImageRequest(BaseModel):
    prompt: str
    model: str
    size: str = "1024x1024"
    seed: int | None = None


@app.get("/api/models")
async def models():
    data = await call_provider("GET", "/models")
    ids = sorted(m["id"] for m in data.get("data", []))
    # Defaults only apply when the env var is set and the model exists at the provider.
    default_text = os.getenv("DEFAULT_TEXT_MODEL", "")
    default_image = os.getenv("DEFAULT_IMAGE_MODEL", "")
    return {
        "models": ids,
        "defaultText": default_text if default_text in ids else None,
        "defaultImage": default_image if default_image in ids else None,
    }


@app.get("/api/creativity")
async def creativity_levels():
    return {"levels": list(load_creativity().keys())}


@app.post("/api/prompt")
async def prompt(req: PromptRequest):
    guidance = load_creativity()
    if req.creativity not in guidance:
        raise HTTPException(400, f"Unknown creativity level: {req.creativity}")

    picked = random.sample(req.remix, k=min(len(req.remix), random.choice([2, 3]))) if req.remix else []
    recent_block = "\n".join(f"- {p}" for p in req.recent[-5:]) or "(none)"
    system = (
        "You write one image-generation prompt per request.\n"
        f"Base prompt: {req.base}\n"
        f"Remix phrases to draw from: {', '.join(picked) or '(none)'}\n"
        f"Recent prompts (do NOT repeat or lightly reword these):\n{recent_block}\n\n"
        f"Creativity guidance:\n{guidance[req.creativity]}\n\n"
        "Reply with the prompt text only."
    )
    body = {
        "model": req.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": "Write the next prompt."},
        ],
    }
    data = await call_provider("POST", "/chat/completions", json=body)
    return {"prompt": data["choices"][0]["message"]["content"].strip()}


@app.post("/api/image")
async def image(req: ImageRequest):
    body = {
        "model": req.model,
        "prompt": req.prompt,
        "size": req.size,
        "n": 1,
    }
    data = await call_provider("POST", "/images/generations", json=body)
    item = data["data"][0]
    if "b64_json" in item:
        b64 = item["b64_json"]
    else:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(item["url"])
        b64 = base64.b64encode(resp.content).decode("ascii")
    return {"b64": b64, "mime": "image/png"}


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
