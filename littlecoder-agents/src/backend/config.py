import json
import os
from pathlib import Path

# Load creativity guidance from JSON file (editable without code changes)
CREATIVITY_CONFIG_PATH = Path(__file__).parent / "creativity.json"

def get_creativity_guidance(level: str) -> dict:
    """Load creativity guidance for the given level."""
    with open(CREATIVITY_CONFIG_PATH, "r") as f:
        config = json.load(f)
    return config.get(level, config["normal"])
