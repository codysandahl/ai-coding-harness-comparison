"""Local AI Image Explorer backend.

Loads environment configuration, exposes the creativity levels and available
models, and performs one full generation (prompt + image) per request. The
frontend drives the continuous loop — calling /api/generate repeatedly and
pausing by simply stopping the calls — which keeps pause semantics clean.
"""
import random
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import creativity
import provider

load_dotenv()  # reads PROVIDER_BASE_URL / PROVIDER_API_KEY from .env

app = FastAPI(title="Local AI Image Explorer")

_FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


class GenerateRequest(BaseModel):
    text_model: str
    image_model: str
    base_prompt: str
    remix_phrases: list[str]
    creativity: str
    width: int = 1024
    height: int = 1024
    seed: int | None = None


@app.get("/api/creativity")
def get_creativity():
    levels = creativity.load_levels()
    return {"levels": [{"id": l["id"], "label": l["label"]} for l in levels],
            "default": levels[1]["id"] if len(levels) >= 2 else levels[0]["id"]}


@app.get("/api/models")
async def get_models():
    try:
        return {"models": await provider.list_models()}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"provider error: {e}")


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    # ponytail: OpenAI's API doesn't accept a seed param, so this is tracked
    # app-side only — recorded in metadata per the spec, never sent to the
    # provider. Fresh per generation unless the user overrides it.
    seed = req.seed if req.seed is not None else random.randint(0, 2**31 - 1)
    size = f"{req.width}x{req.height}"

    try:
        level = creativity.get_level(req.creativity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        prompt = await provider.generate_prompt(
            text_model=req.text_model,
            base_prompt=req.base_prompt,
            remix_phrases=req.remix_phrases,
            creativity_guidance=level["guidance"],
        )
        image = await provider.generate_image(
            image_model=req.image_model,
            prompt=prompt,
            size=size,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"generation failed: {e}")

    return {
        "image": image,
        "metadata": {
            "prompt": prompt,
            "text_model": req.text_model,
            "image_model": req.image_model,
            "size": size,
            "seed": seed,
            "creativity": req.creativity,
            "creativity_label": level["label"],
            "base_prompt": req.base_prompt,
            "remix_phrases": req.remix_phrases,
        },
    }


if _FRONTEND.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND), html=True), name="frontend")


@app.exception_handler(HTTPException)
async def _json_errors(_, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})