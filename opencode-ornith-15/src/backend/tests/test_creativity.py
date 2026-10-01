"""Tests for creativity guidance loading and divergence."""

from __future__ import annotations

from app.generation.creativity import load_creativity_config
from app.models import CREATIVITY_LEVELS

CONFIG_PATH = __import__("pathlib").Path(__file__).resolve().parent.parent / "creativity.yaml"


def test_all_levels_present():
    cfg = load_creativity_config(CONFIG_PATH)
    for level in CREATIVITY_LEVELS:
        assert level in cfg
        assert cfg[level]["system"].strip()


def test_guidance_differs_between_levels():
    cfg = load_creativity_config(CONFIG_PATH)
    systems = {level: cfg[level]["system"].lower() for level in CREATIVITY_LEVELS}
    assert systems["mild"] != systems["normal"]
    assert systems["normal"] != systems["wild"]
    assert systems["mild"] != systems["wild"]


def test_divergence_scales_with_level():
    cfg = load_creativity_config(CONFIG_PATH)
    mild = cfg["mild"]["system"].lower()
    wild = cfg["wild"]["system"].lower()
    # Wild guidance pushes toward bigger change; mild toward keeping close.
    assert "close" in mild or "very close" in mild
    assert "boldly" in wild or "reimagine" in wild or "fresh" in wild
