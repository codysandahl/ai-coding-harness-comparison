from dataclasses import dataclass, asdict
from typing import List

@dataclass
class ImageMetadata:
    prompt: str
    seed: int
    creativity_level: str
    model: str
    size: tuple[int, int]
    timestamp: float
    
    def to_dict(self):
        return {
            "prompt": self.prompt,
            "seed": self.seed,
            "creativity_level": self.creativity_level,
            "model": self.model,
            "size": list(self.size),
            "timestamp": self.timestamp
        }
