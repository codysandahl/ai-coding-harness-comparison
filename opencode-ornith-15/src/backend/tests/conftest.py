"""Shared test fixtures and fakes."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.models import RuntimeSettings  # noqa: E402
from app.session.store import SessionStore  # noqa: E402
from app.providers.openai_client import ImageResult  # noqa: E402

FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"not-a-real-png"


class FakeClient:
    """Stand-in for OpenAIClient with no network access."""

    def __init__(self, image_bytes: bytes = FAKE_PNG, content_type: str = "image/png"):
        self.image_bytes = image_bytes
        self.content_type = content_type
        self.chat_calls: list[tuple[str, str]] = []
        self.image_calls: list[tuple[str, str, str]] = []
        self._counter = 0

    async def create_chat(self, system: str, user: str) -> str:
        self.chat_calls.append((system, user))
        self._counter += 1
        return f"variant {self._counter}"

    async def create_image(self, prompt: str, size: str, model: str) -> ImageResult:
        self.image_calls.append((prompt, size, model))
        return ImageResult(bytes=self.image_bytes, content_type=self.content_type, revised_prompt=prompt)

    async def list_models(self) -> list[str]:
        return ["gpt-4o-mini", "gpt-image-2"]

    async def close(self) -> None:
        pass


class FakeGenerator:
    """No-op generator that exposes a queue without running a real loop."""

    def __init__(self):
        import asyncio

        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    @property
    def queue(self):
        return self._queue

    def set_running(self, running: bool) -> None:
        self._running = running

    async def shutdown(self) -> None:
        self._running = False


@pytest.fixture
def fake_settings() -> RuntimeSettings:
    settings = RuntimeSettings()
    settings.base_prompt = "a lighthouse at dusk, oil painting"
    settings.remix_phrases = ["dramatic clouds", "golden hour", "storm approaching"]
    settings.creativity = "normal"
    settings.width = 1024
    settings.height = 1024
    settings.text_model = "gpt-4o-mini"
    settings.image_model = "gpt-image-2"
    return settings


@pytest.fixture
def store(fake_settings) -> SessionStore:
    s = SessionStore(max_images=50)
    s.settings = fake_settings
    return s


@pytest.fixture
def store_empty() -> SessionStore:
    return SessionStore(max_images=50)


@pytest.fixture
def config():
    from app.generation.creativity import load_creativity_config

    return load_creativity_config(__import__("pathlib").Path(__file__).resolve().parent.parent / "creativity.yaml")
