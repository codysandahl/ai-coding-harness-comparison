"""Creativity-level guidance loaded from an editable YAML file.

Guidance is data, not code: editing ``creativity.yaml`` changes how each level
behaves without touching the application.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from ..models import CREATIVITY_LEVELS

logger = logging.getLogger(__name__)


def load_creativity_config(path: Path) -> dict[str, dict[str, str]]:
    """Load creativity guidance, guaranteeing every required level exists."""
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}

    cfg: dict[str, dict[str, str]] = {}
    for level in CREATIVITY_LEVELS:
        entry = data.get(level)
        if not isinstance(entry, dict) or not entry.get("system"):
            raise ValueError(f"Creativity level '{level}' is missing a 'system' prompt in {path}")
        cfg[level] = {
            "system": entry["system"].strip(),
            "description": str(entry.get("description", "")).strip(),
        }
    return cfg


def level_guidance(config: dict[str, dict[str, str]], level: str) -> str:
    """Return the system guidance for a creativity level (falls back to 'normal')."""
    if level not in config:
        level = "normal"
    return config[level]["system"]
