"""Creativity level configuration loaded from creativity.yaml.

Editable without code changes — the guidance that governs each level lives
here, not in application logic.
"""
from pathlib import Path
import yaml

_CONFIG_PATH = Path(__file__).parent / "creativity.yaml"
_cache: list[dict] | None = None


def load_levels() -> list[dict]:
    global _cache
    if _cache is None:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        _cache = data["levels"]
    return _cache


def get_level(level_id: str) -> dict:
    for lvl in load_levels():
        if lvl["id"] == level_id:
            return lvl
    raise ValueError(f"unknown creativity level: {level_id}")