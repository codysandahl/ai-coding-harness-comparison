"""Core data models."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

# Fixed, selectable creativity levels. Guidance for each lives in creativity.yaml.
CREATIVITY_LEVELS: tuple[str, ...] = ("mild", "normal", "wild")

DEFAULT_TEXT_MODEL = "gpt-4o-mini"
DEFAULT_IMAGE_MODEL = "gpt-image-2"
DEFAULT_SIZE = "1024x1024"
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 1024


@dataclass
class RuntimeSettings:
    """User-editable generation settings, mutated at runtime by the UI."""

    base_prompt: str = ""
    remix_phrases: list[str] = field(default_factory=list)
    creativity: str = "normal"
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    text_model: str = DEFAULT_TEXT_MODEL
    image_model: str = DEFAULT_IMAGE_MODEL

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_prompt": self.base_prompt,
            "remix_phrases": self.remix_phrases,
            "creativity": self.creativity,
            "width": self.width,
            "height": self.height,
            "text_model": self.text_model,
            "image_model": self.image_model,
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        if isinstance(data.get("base_prompt"), str):
            self.base_prompt = data["base_prompt"]
        if isinstance(data.get("remix_phrases"), list):
            self.remix_phrases = [str(x) for x in data["remix_phrases"]]
        if isinstance(data.get("creativity"), str):
            self.creativity = data["creativity"]
        if isinstance(data.get("width"), int):
            self.width = data["width"]
        if isinstance(data.get("height"), int):
            self.height = data["height"]
        if isinstance(data.get("text_model"), str):
            self.text_model = data["text_model"]
        if isinstance(data.get("image_model"), str):
            self.image_model = data["image_model"]


@dataclass
class ImageRecord:
    """A single generated image, held in memory only."""

    prompt: str
    model: str
    size: str
    creativity: str
    content_type: str
    image_bytes: bytes

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: float = field(default_factory=time.time)

    def metadata(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "model": self.model,
            "size": self.size,
            "creativity": self.creativity,
            "content_type": self.content_type,
            "created_at": self.created_at,
        }
