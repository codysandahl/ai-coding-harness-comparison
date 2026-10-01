"""Runtime configuration loaded from environment variables / .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent


@dataclass
class Settings:
    provider_base_url: str = "https://api.openai.com/v1"
    provider_api_key: str = ""
    text_model: str = "gpt-4o-mini"
    image_model: str = "gpt-image-2"
    generation_interval_seconds: float = 10.0
    max_images: int = 500
    creativity: str = "normal"
    port: int = 8191

    text_endpoint: str = "/chat/completions"
    image_endpoint: str = "/images/generations"
    models_endpoint: str = "/models"

    creativity_config_path: Path = field(default=lambda: PROJECT_DIR / "creativity.yaml")

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv(PROJECT_DIR / ".env", override=False)

        def _get(name: str, default: str) -> str:
            return os.environ.get(name, default)

        def _get_float(name: str, default: float) -> float:
            try:
                return float(os.environ.get(name, default))
            except (TypeError, ValueError):
                return default

        def _get_int(name: str, default: int) -> int:
            try:
                return int(os.environ.get(name, default))
            except (TypeError, ValueError):
                return default

        base_url = _get("PROVIDER_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        return cls(
            provider_base_url=base_url,
            provider_api_key=_get("PROVIDER_API_KEY", ""),
            text_model=_get("TEXT_MODEL", "gpt-4o-mini"),
            image_model=_get("IMAGE_MODEL", "gpt-image-2"),
            generation_interval_seconds=_get_float("GENERATION_INTERVAL_SECONDS", 10.0),
            max_images=_get_int("MAX_IMAGES", 500),
            creativity=_get("CREATIVITY", "normal"),
            port=_get_int("PORT", 8191),
        )

    def auth_headers(self) -> dict[str, str]:
        if self.provider_api_key:
            return {"Authorization": f"Bearer {self.provider_api_key}"}
        return {}
