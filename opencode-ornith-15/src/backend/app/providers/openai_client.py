"""OpenAI API-compatible client for text and image generation.

The client talks to any provider exposing an OpenAI-compatible surface. It does
not send ``temperature`` or ``seed`` (unsupported by the OpenAI image API);
divergence is controlled entirely through creativity-level prompt guidance.
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass

import httpx

from ..config import Settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 120.0


def detect_content_type(data: bytes) -> str:
    """Infer a MIME type from leading magic bytes."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


@dataclass
class ImageResult:
    bytes: bytes
    content_type: str
    revised_prompt: str | None = None


class OpenAIClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.provider_base_url
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=settings.auth_headers(),
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def list_models(self) -> list[str]:
        try:
            resp = await self._client.get(self.settings.models_endpoint)
            resp.raise_for_status()
            payload = resp.json()
        except Exception:
            logger.warning(
                "Could not list models from %s",
                self.base_url + self.settings.models_endpoint,
                exc_info=True,
            )
            raise
        models = []
        for item in payload.get("data", []):
            model_id = item.get("id")
            if model_id:
                models.append(model_id)
        return models

    async def create_chat(self, system: str, user: str) -> str:
        payload = {
            "model": self.settings.text_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        resp = await self._client.post(self.settings.text_endpoint, json=payload)
        resp.raise_for_status()
        payload_out = resp.json()
        choices = payload_out.get("choices")
        if not choices:
            raise RuntimeError(f"Unexpected chat response: {payload_out!r}")
        return choices[0].get("message", {}).get("content", "").strip()

    async def create_image(self, prompt: str, size: str, model: str) -> ImageResult:
        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "n": 1,
        }
        resp = await self._client.post(self.settings.image_endpoint, json=payload)
        resp.raise_for_status()
        payload_out = resp.json()
        if not payload_out.get("data"):
            raise RuntimeError(f"Unexpected image response: {payload_out!r}")
        first = payload_out["data"][0]

        revised = first.get("revised_prompt")
        b64 = first.get("b64_json")
        if b64:
            raw = base64.b64decode(b64)
            return ImageResult(bytes=raw, content_type=detect_content_type(raw), revised_prompt=revised)

        image_url = first.get("url")
        if not image_url:
            raise RuntimeError(f"No image data in response: {first!r}")
        img_resp = await httpx.AsyncClient(timeout=DEFAULT_TIMEOUT).get(image_url)
        img_resp.raise_for_status()
        return ImageResult(
            bytes=img_resp.content,
            content_type=detect_content_type(img_resp.content),
            revised_prompt=revised,
        )
