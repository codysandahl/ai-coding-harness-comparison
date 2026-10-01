import os
import json
import uuid
import asyncio
import random
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
CREATIVITY_CONFIG_PATH = os.environ.get(
    "CREATIVITY_CONFIG",
    os.path.join(os.path.dirname(__file__), "creativity.json"),
)

creativity_config = {}
try:
    with open(CREATIVITY_CONFIG_PATH, "r") as f:
        creativity_config = json.load(f).get("levels", {})
except (FileNotFoundError, json.JSONDecodeError):
    creativity_config = {
        "low": {
            "divergence": "minimal",
            "system_prompt": "Make small word-level changes to the base prompt. Preserve the original structure and subject.",
        },
        "medium": {
            "divergence": "moderate",
            "system_prompt": "Rephrase the prompt more substantially. Add or remove descriptive elements while keeping the core subject.",
        },
        "high": {
            "divergence": "significant",
            "system_prompt": "Diverge noticeably from the base prompt. Introduce new imagery, settings, or styles while preserving the core subject.",
        },
    }

models_cache: Optional[dict] = None
available_text_models: list = []
available_image_models: list = []


async def fetch_openai_models() -> dict:
    global models_cache, available_text_models, available_image_models
    if models_cache:
        return models_cache

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{OPENAI_BASE_URL}/models",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            )
            resp.raise_for_status()
            models_cache = resp.json()
            model_list = models_cache.get("data", [])
            available_text_models = [
                m["id"]
                for m in model_list
                if "gpt" in m["id"].lower() or "chatgpt" in m["id"].lower()
            ]
            # Filter out models known to not work for chat completions
            known_bad_text_models = {"chatgpt-5.4", "chatgpt-5.4-mini", "chatgpt-5.4-nano", "gpt-image-2"}
            available_text_models = [m for m in available_text_models if m not in known_bad_text_models]
            available_image_models = [
                m["id"]
                for m in model_list
                if "dall" in m["id"].lower() or "image" in m["id"].lower()
            ]
            if not available_text_models:
                available_text_models = [
                    m["id"]
                    for m in model_list
                    if "text" in m["id"].lower() or "chat" in m["id"].lower()
                ]
            if not available_image_models:
                available_image_models = [
                    m["id"]
                    for m in model_list
                    if "dall" in m["id"].lower() or "image" in m["id"].lower()
                ]
        except Exception:
            models_cache = {"data": []}
            available_text_models = []
            available_image_models = []

    return models_cache


class GenerationStore:
    def __init__(self):
        self.images: list[dict] = []
        self.paused = False
        self.current_prompt = ""
        self.lock = asyncio.Lock()

    async def add_image(self, image_data: dict):
        async with self.lock:
            image_data["id"] = str(uuid.uuid4())
            image_data["created_at"] = datetime.utcnow().isoformat()
            self.images.insert(0, image_data)

    async def get_images(self, limit: int = 50) -> list[dict]:
        async with self.lock:
            return self.images[:limit]

    async def clear(self):
        async with self.lock:
            self.images.clear()


store = GenerationStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await fetch_openai_models()
    yield


app = FastAPI(title="Local AI Image Explorer", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/models")
async def get_models():
    data = await fetch_openai_models()
    return {
        "text_models": available_text_models,
        "image_models": available_image_models,
        "all_models": [m["id"] for m in data.get("data", [])],
    }


@app.get("/creativity")
async def get_creativity_levels():
    return creativity_config


@app.post("/generate-text")
async def generate_text(
    base_prompt: str = "",
    creativity: str = "medium",
    remix_phrases: list[str] = [],
):
    if not base_prompt:
        raise HTTPException(status_code=400, detail="base_prompt is required")

    sys_prompt = creativity_config.get(
        creativity, creativity_config.get("medium", {})
    ).get("system_prompt", "")

    remix_text = "\n".join(remix_phrases) if remix_phrases else ""

    messages = [
        {
            "role": "system",
            "content": (
                f"{sys_prompt}\n\n"
                f"Base prompt: {base_prompt}\n"
                f"Remix phrases to incorporate: {remix_text if remix_text else 'none'}\n\n"
                "Generate a single new prompt variation. Output ONLY the prompt text, nothing else."
            ),
        },
        {"role": "user", "content": "Generate a new prompt variation."},
    ]

    text_model = os.environ.get("TEXT_MODEL", "").strip()
    if not text_model:
        text_model = available_text_models[0] if available_text_models else "gpt-4o-mini"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": text_model,
                    "messages": messages,
                    "max_tokens": 200,
                    "temperature": 0.8,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            new_prompt = data["choices"][0]["message"]["content"].strip()
            return {"prompt": new_prompt, "model": text_model, "creativity": creativity}
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"API error: {e.response.text}",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/generate-image")
async def generate_image(
    prompt: str = "",
    size: str = "1024x1024",
    model: str = "",
    seed: Optional[int] = None,
):
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    image_model = model.strip() if model.strip() else os.environ.get("IMAGE_MODEL", "dall-e-3")
    if not image_model:
        image_model = "dall-e-3"

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            payload = {
                "model": image_model,
                "prompt": prompt,
                "size": size,
                "n": 1,
                "response_format": "url",
            }

            resp = await client.post(
                f"{OPENAI_BASE_URL}/images/generations",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            image_url = data["data"][0]["url"]

            image_record = {
                "prompt": prompt,
                "model": image_model,
                "size": size,
                "seed": seed or random.randint(100000, 999999),
                "url": image_url,
                "creativity": "medium",
            }

            await store.add_image(image_record)
            return image_record
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"API error: {e.response.text}",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.get("/generate-stream")
async def generate_stream(
    base_prompt: str = "",
    creativity: str = "medium",
    remix_phrases: List[str] = Query(default=[]),
    size: str = "1024x1024",
    image_model: str = "",
    text_model: str = "",
    seed_override: Optional[int] = None,
):
    if not base_prompt:
        raise HTTPException(status_code=400, detail="base_prompt is required")
    return StreamingResponse(
        event_generator(base_prompt, creativity, remix_phrases, size, image_model, text_model, seed_override),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


async def event_generator(base_prompt, creativity, remix_phrases, size, image_model, text_model, seed_override):
    print(f"DEBUG: event_generator started, base_prompt={base_prompt!r}, creativity={creativity!r}, remix_phrases={remix_phrases!r}")
    import sys
    print(f"DEBUG: remix_phrases type={type(remix_phrases)}, value={remix_phrases}", file=sys.stderr)
    current_prompt = base_prompt
    generation_count = 0

    while not store.paused:
        generation_count += 1
        print(f"DEBUG: generation loop iteration {generation_count}")
        current_seed = (
            seed_override if seed_override is not None else random.randint(100000, 999999)
        )

        try:
            sys_prompt = creativity_config.get(
                creativity, creativity_config.get("medium", {})
            ).get("system_prompt", "")

            remix_text = "\n".join(remix_phrases) if remix_phrases else ""

            messages = [
                {
                    "role": "system",
                    "content": (
                        f"{sys_prompt}\n\n"
                        f"Base prompt: {current_prompt}\n"
                        f"Remix phrases to incorporate: {remix_text if remix_text else 'none'}\n\n"
                        "Generate a single new prompt variation. Output ONLY the prompt text, nothing else."
                    ),
                },
                {"role": "user", "content": "Generate a new prompt variation."},
            ]

            gen_text_model = text_model.strip() if text_model.strip() else (
                available_text_models[0] if available_text_models else "gpt-4o-mini"
            )

            print(f"DEBUG: Using text model={gen_text_model!r}, OPENAI_BASE_URL={OPENAI_BASE_URL!r}", file=sys.stderr)
            async with httpx.AsyncClient(timeout=30.0) as text_client:
                print("DEBUG: Sending text request...", file=sys.stderr)
                text_resp = await text_client.post(
                    f"{OPENAI_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": gen_text_model,
                        "messages": messages,
                        "max_tokens": 200,
                    },
                )
                print("DEBUG: Text response received", file=sys.stderr)
                text_resp.raise_for_status()
                text_data = text_resp.json()
                new_prompt = text_data["choices"][0]["message"]["content"].strip()
                print(f"DEBUG: New prompt: {new_prompt[:50]!r}...", file=sys.stderr)
        except Exception as e:
            error_msg = json.dumps({"error": f"Text generation failed: {str(e)}"})
            yield f"event: error\ndata: {error_msg}\n\n"
            await asyncio.sleep(10)
            continue

        # Generate image
        gen_image_model = image_model.strip() if image_model.strip() else (
            os.environ.get("IMAGE_MODEL", "dall-e-3")
        )
        if not gen_image_model:
            gen_image_model = "dall-e-3"

        try:
            async with httpx.AsyncClient(timeout=60.0) as img_client:
                img_payload = {
                    "model": gen_image_model,
                    "prompt": new_prompt,
                    "size": size,
                    "n": 1,
                    "response_format": "url",
                }

                img_resp = await img_client.post(
                    f"{OPENAI_BASE_URL}/images/generations",
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=img_payload,
                )
                img_resp.raise_for_status()
                img_data = img_resp.json()
                image_url = img_data["data"][0].get("url")
                b64_json = img_data["data"][0].get("b64_json")
                if image_url:
                    pass
                elif b64_json:
                    image_url = f"data:image/png;base64,{b64_json}"

                image_record = {
                    "id": str(uuid.uuid4()),
                    "prompt": new_prompt,
                    "model": gen_image_model,
                    "size": size,
                    "seed": current_seed,
                    "url": image_url,
                    "creativity": creativity,
                    "created_at": datetime.utcnow().isoformat(),
                }

                await store.add_image(image_record)

                yield f"event: image\ndata: {json.dumps(image_record)}\n\n"

                current_prompt = new_prompt

        except httpx.HTTPStatusError as e:
            error_text = e.response.text.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
            error_msg = json.dumps({"error": f"Text generation failed: {error_text}"})
            yield f"event: error\ndata: {error_msg}\n\n"
            print(f"DEBUG: Text gen error: {e.response.status_code}", file=sys.stderr)
            await asyncio.sleep(10)
            continue
        except Exception as e:
            error_msg = json.dumps({"error": f"Image generation failed: {str(e)}"})
            yield f"event: error\ndata: {error_msg}\n\n"
            await asyncio.sleep(10)
            continue

        await asyncio.sleep(0.5)

    yield f"event: stopped\ndata: {json.dumps({'message': 'Generation stopped'})}\n\n"


@app.get("/images")
async def list_images(limit: int = 50):
    return await store.get_images(limit)


@app.delete("/images")
async def clear_images():
    await store.clear()
    return {"status": "ok"}


@app.post("/pause")
async def pause_generation():
    store.paused = True
    return {"status": "paused"}


@app.post("/resume")
async def resume_generation():
    store.paused = False
    return {"status": "resumed"}


@app.get("/pause/status")
async def get_pause_status():
    return {"paused": store.paused}


@app.post("/images/{image_id}/use-as-prompt")
async def use_as_prompt(image_id: str):
    async with store.lock:
        for img in store.images:
            if img["id"] == image_id:
                new_prompt = img["prompt"]
                base_prompt_input = new_prompt
                return {
                    "prompt": new_prompt,
                    "model": img["model"],
                    "size": img["size"],
                    "seed": img["seed"],
                    "creativity": img.get("creativity", "medium"),
                }
    raise HTTPException(status_code=404, detail="Image not found")


@app.get("/download/{image_id}")
async def download_image(image_id: str):
    async with store.lock:
        for img in store.images:
            if img["id"] == image_id:
                return FileResponse(
                    img["url"],
                    media_type="image/png",
                    filename=f"image-{image_id[:8]}.png",
                )
    raise HTTPException(status_code=404, detail="Image not found")


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
