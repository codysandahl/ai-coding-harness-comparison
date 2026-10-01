import asyncio
import base64
import time
from dataclasses import dataclass, asdict
from typing import Optional, List

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

class GenerationState:
    def __init__(self):
        self.base_prompt = ""
        self.remix_phrases: List[str] = []
        self.creativity_level = "normal"
        self.text_model = "gpt-4o-mini"
        self.image_model = "dall-e-3"
        self.width = 512
        self.height = 512
        self.seed: Optional[int] = None
        self.images: List[tuple[ImageMetadata, str]] = []  # (metadata, base64)
        self.paused = False
        self.running = False
        self._lock = asyncio.Lock()
        self._generation_event = asyncio.Event()
        self._generation_task: Optional[asyncio.Task] = None
    
    def _generate_seed(self) -> int:
        if self.seed is not None:
            return self.seed
        import random
        return random.randint(0, 2**32 - 1)
    
    async def start_generation(self):
        async with self._lock:
            if self.running and not self.paused:
                return
            self.running = True
            self.paused = False
            self._generation_event.set()
            self._generation_task = asyncio.create_task(self._generation_loop())
    
    async def pause_generation(self):
        async with self._lock:
            self.paused = True
    
    async def resume_generation(self):
        async with self._lock:
            self.paused = False
            self._generation_event.set()
    
    async def stop_generation(self):
        async with self._lock:
            self.running = False
            self.paused = True
            self._generation_event.clear()
    
    async def _generation_loop(self):
        while self.running:
            async with self._lock:
                if self.paused:
                    await self._generation_event.wait()
                    continue
                
                if not self.base_prompt:
                    await asyncio.sleep(1)
                    continue
                
                # Generate image
                try:
                    from backend.providers.openai_client import OpenAIClient
                    client = OpenAIClient()
                    metadata, base64_image = await client.generate_image(
                        base_prompt=self.base_prompt,
                        remix_phrases=self.remix_phrases,
                        creativity_level=self.creativity_level,
                        model=self.image_model,
                        width=self.width,
                        height=self.height,
                        seed=self._generate_seed()
                    )
                    
                    # Store image (max 20)
                    self.images.append((metadata, base64_image))
                    if len(self.images) > 20:
                        self.images = self.images[-20:]
                    
                except Exception as e:
                    print(f"Generation error: {e}")
            
            # Wait until next interval (10 seconds or less)
            await asyncio.sleep(8)  # Leave some room for network latency
    
    def set_base_prompt(self, prompt: str):
        self.base_prompt = prompt
    
    def set_remix_phrases(self, phrases: str):
        self.remix_phrases = [p.strip() for p in phrases.split("\n") if p.strip()]
    
    def set_creativity_level(self, level: str):
        self.creativity_level = level
    
    def set_models(self, text: str, image: str):
        self.text_model = text
        self.image_model = image
    
    def set_size(self, width: int, height: int):
        self.width = width
        self.height = height
    
    def set_seed(self, seed: Optional[str]):
        if seed and seed.isdigit():
            self.seed = int(seed)
        elif seed == "random" or not seed:
            self.seed = None
        else:
            self.seed = None
    
    def get_state(self) -> dict:
        return {
            "base_prompt": self.base_prompt,
            "remix_phrases": "\n".join(self.remix_phrases),
            "creativity_level": self.creativity_level,
            "text_model": self.text_model,
            "image_model": self.image_model,
            "width": self.width,
            "height": self.height,
            "seed": self.seed if self.seed is not None else "",
            "images": [
                {
                    "metadata": m.to_dict(),
                    "data": b  # base64 string
                } for m, b in self.images
            ],
            "paused": self.paused,
            "running": self.running
        }

# Global state instance
state = GenerationState()
