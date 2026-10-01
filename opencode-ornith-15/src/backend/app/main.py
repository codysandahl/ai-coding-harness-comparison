"""FastAPI application: routes, lifespan, and SSE endpoint."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings
from .models import CREATIVITY_LEVELS
from .providers.openai_client import OpenAIClient
from .generation.creativity import load_creativity_config
from .generation.generator import Generator
from .session.store import SessionStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR.parent / "static"
CREATIVITY_PATH = BASE_DIR.parent / "creativity.yaml"


@asynccontextmanager
async def lifespan(app: FastAPI):
    overrides = getattr(app.state, "_overrides", {}) or {}
    settings = overrides.get("settings") or Settings.load()
    store = overrides.get("store") or SessionStore(max_images=settings.max_images)
    creativity_config = (
        overrides.get("creativity_config") or load_creativity_config(settings.creativity_config_path())
    )
    client = overrides.get("client") or OpenAIClient(settings)
    generator = overrides.get("generator") or Generator(
        client=client,
        store=store,
        creativity_config=creativity_config,
        interval=settings.generation_interval_seconds,
    )

    app.state.settings = settings
    app.state.store = store
    app.state.creativity_config = creativity_config
    app.state.client = client
    app.state.generator = generator

    generator.set_running(True)

    try:
        yield
    finally:
        generator.set_running(False)
        await generator.shutdown()
        await client.close()


def build_app(
    client=None,
    store=None,
    creativity_config=None,
    generator=None,
    settings=None,
) -> FastAPI:
    app = FastAPI(title="Local AI Image Explorer", lifespan=lifespan)
    app.state._overrides = {
        "client": client,
        "store": store,
        "creativity_config": creativity_config,
        "generator": generator,
        "settings": settings,
    }

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/creativity-levels")
    async def creativity_levels() -> dict:
        cfg = app.state.creativity_config
        return {
            "levels": list(CREATIVITY_LEVELS),
            "defaults": app.state.settings.creativity,
            "descriptions": {level: cfg[level]["description"] for level in CREATIVITY_LEVELS},
        }

    @app.get("/api/models")
    async def models() -> dict:
        default_text = app.state.settings.text_model
        default_image = app.state.settings.image_model
        try:
            ids = [m for m in await app.state.client.list_models() if m]
        except Exception:  # noqa: BLE001 - fall back to configured defaults
            logger.warning("Using configured text/image models as fallback")
            ids = []
        text_models = ids if ids else [default_text]
        image_models = ids if ids else [default_image]
        if default_text not in text_models:
            text_models.insert(0, default_text)
        if default_image not in image_models:
            image_models.insert(0, default_image)
        return {
            "text_models": text_models,
            "image_models": image_models,
            "defaults": {"text_model": default_text, "image_model": default_image},
        }

    @app.get("/api/settings")
    async def get_settings() -> dict:
        return app.state.store.settings.to_dict()

    @app.post("/api/settings")
    async def update_settings(body: dict) -> dict:
        app.state.store.settings.from_dict(body)
        return app.state.store.settings.to_dict()

    @app.post("/api/generate")
    async def set_generate(body: dict) -> dict:
        running = bool(body.get("running", True))
        app.state.generator.set_running(running)
        return {"running": app.state.generator.running}

    @app.get("/api/generate")
    async def get_generate() -> dict:
        return {"running": app.state.generator.running}

    @app.get("/api/images")
    async def list_images() -> list[dict]:
        return [rec.metadata() for rec in app.state.store.all()]

    @app.get("/api/images/{image_id}")
    async def get_image(image_id: str, request: Request) -> Response:
        record = app.state.store.get(image_id)
        if record is None:
            return Response(status_code=404, content="Not found")
        return Response(content=record.image_bytes, media_type=record.content_type)

    @app.get("/api/images/{image_id}/download")
    async def download_image(image_id: str) -> Response:
        record = app.state.store.get(image_id)
        if record is None:
            return Response(status_code=404, content="Not found")
        filename = f"image-{record.id}.{record.content_type.split('/')[-1]}"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(content=record.image_bytes, media_type=record.content_type, headers=headers)

    @app.get("/api/events")
    async def events():
        async def stream():
            yield f"data: {json.dumps({'type': 'ready'})}\n\n"
            queue = app.state.generator.queue
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"

        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.get("/")
    async def index() -> Response:
        return Response(content=(STATIC_DIR / "index.html").read_text(encoding="utf-8"), media_type="text/html")

    app.mount("/", StaticFiles(directory=str(STATIC_DIR)), name="static")
    return app


app = build_app()
