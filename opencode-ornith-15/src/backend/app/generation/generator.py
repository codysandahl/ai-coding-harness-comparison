"""Continuous generation loop.

The loop produces one (prompt, image) pair per cycle, derives each new prompt
from the current base prompt plus a varied selection of remix phrases, and
enqueues the resulting metadata. Cadence is shaped so that the gap between
successfully displayed images is ``generation_interval_seconds`` under normal
conditions.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections.abc import Awaitable, Callable

from ..models import ImageRecord, RuntimeSettings
from ..providers.openai_client import OpenAIClient
from .creativity import level_guidance

logger = logging.getLogger(__name__)


class Generator:
    def __init__(
        self,
        client: OpenAIClient,
        store,
        creativity_config: dict,
        interval: float,
    ) -> None:
        self._client = client
        self._store = store
        self._creativity_config = creativity_config
        self._interval = interval
        self._running = False
        self._task: asyncio.Task | None = None
        self._queue: asyncio.Queue = asyncio.Queue()
        self._rng = random.Random()

    @property
    def running(self) -> bool:
        return self._running

    @property
    def queue(self) -> asyncio.Queue:
        return self._queue

    def set_running(self, running: bool) -> None:
        self._running = running
        if running and self._task is None:
            self._task = asyncio.create_task(self._loop(), name="generator-loop")

    async def shutdown(self) -> None:
        self._running = False
        if self._task is not None:
            await self._task
            self._task = None

    async def _loop(self) -> None:
        while self._running:
            start = time.monotonic()
            try:
                await self._generate_once()
            except Exception:  # noqa: BLE001 - keep the loop alive on provider errors
                logger.exception("Generation cycle failed")
                await self._queue.put({"type": "error", "detail": "Generation failed"})
                await asyncio.sleep(self._interval)
                continue
            elapsed = time.monotonic() - start
            await asyncio.sleep(max(0.0, self._interval - elapsed))

    async def _select_remix(self, phrases: list[str]) -> str:
        cleaned = [p.strip() for p in phrases if p.strip()]
        if not cleaned:
            return ""
        count = self._rng.randint(1, len(cleaned))
        sampled = self._rng.sample(cleaned, count)
        return ", ".join(sampled)

    async def _generate_once(self) -> None:
        settings = self._store.settings

        if not settings.base_prompt.strip():
            await self._queue.put({"type": "hint", "detail": "Set a base prompt to start generating"})
            return

        remix_pool = await self._select_remix(settings.remix_phrases)
        user = (
            f"Base prompt: {settings.base_prompt}\n\n"
            f"Remix phrases (incorporate a varied subset):\n{remix_pool or '(none)'}"
        )
        system = level_guidance(self._creativity_config, settings.creativity)

        prompt = await self._client.create_chat(system, user)
        if not prompt:
            await self._queue.put({"type": "hint", "detail": "Text model returned an empty prompt"})
            return

        size = f"{settings.width}x{settings.height}"
        result = await self._client.create_image(prompt, size, settings.image_model)

        record = ImageRecord(
            prompt=prompt,
            model=settings.image_model,
            size=size,
            creativity=settings.creativity,
            content_type=result.content_type,
            image_bytes=result.bytes,
        )
        self._store.add(record)
        await self._queue.put({"type": "image", "metadata": record.metadata()})
