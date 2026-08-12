import asyncio
import httpx
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List
from dotenv import load_dotenv
from backend.types import ImageMetadata
from backend.config import get_creativity_guidance

logger = logging.getLogger(__name__)

# Load environment variables from .env file in project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')

# Load environment variables from .env file in project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')

class OpenAIClient:
    def __init__(self):
        self.base_url = os.getenv("PROVIDER_BASE_URL", "https://api.openai.com/v1")
        self.api_key = os.getenv("PROVIDER_API_KEY", "")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def list_models(self) -> List[dict]:
        """Fetch available models from the provider."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}/models",
                headers=self.headers
            )
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        return data.get("data", [])
    
    async def generate_image(
        self,
        base_prompt: str,
        remix_phrases: list,
        creativity_level: str,
        model: str,
        width: int,
        height: int,
        seed: Optional[int]
    ) -> Tuple[ImageMetadata, str]:
        # Step 1: Remix the prompt using text model
        remix_prompt = await self._remix_prompt(base_prompt, remix_phrases, creativity_level)
        
        # Step 2: Generate image using image model
        image_data = await self._create_image(remix_prompt, model, width, height, seed)
        
        # Extract image URL or base64
        if "data" in image_data and len(image_data["data"]) > 0:
            image_item = image_data["data"][0]
            
            if "url" in image_item:
                # Fetch the image from URL
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_item["url"])
                    image_bytes = response.content
                
                import base64
                base64_image = base64.b64encode(image_bytes).decode("utf-8")
                
            elif "b64_json" in image_item:
                base64_image = image_item["b64_json"]
            
            else:
                raise ValueError("Unexpected image response format")
        
        else:
            raise ValueError("No image data returned")
        
        # Create metadata
        metadata = ImageMetadata(
            prompt=remix_prompt,
            seed=seed if seed is not None else 0,
            creativity_level=creativity_level,
            model=model,
            size=(width, height),
            timestamp=asyncio.get_event_loop().time()
        )
        
        return metadata, base64_image
    
    async def _remix_prompt(
        self,
        base_prompt: str,
        remix_phrases: list,
        creativity_level: str
    ) -> str:
        guidance = get_creativity_guidance(creativity_level)
        
        # Build prompt with remix phrases
        if remix_phrases:
            remix_text = "\n".join(f"- {phrase}" for phrase in remix_phrases)
            full_prompt = f"{base_prompt}\n\nRemix with:\n{remix_text}"
        else:
            full_prompt = base_prompt
        
        # For simplicity, we'll just return the full prompt
        # In a real implementation, you'd use the text model to remix
        # But since this is an OpenAI-compatible app, we can use the same endpoint
        return full_prompt
    
    async def _create_image(
        self,
        prompt: str,
        model: str,
        width: int,
        height: int,
        seed: Optional[int]
    ) -> dict:
        """Generate an image. Seed is not supported for image models."""
        timeout = int(os.getenv("IMAGE_GEN_TIMEOUT_S", "60"))
        
        logger.info(f"Generating image with model={model}, prompt='{prompt[:50]}...', size=({width},{height})")
        
        # Known default sizes that work with most models
        fallback_sizes = [(1024, 1024), (512, 512)]
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            for attempt_size in fallback_sizes:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "n": 1,
                    "size": f"{attempt_size[0]}x{attempt_size[1]}",
                    "response_format": "b64_json"
                }
                # Note: seed parameter is not supported by image models (gpt-image-2, dall-e)
                # Removing it entirely to avoid BadRequestError
                
                logger.debug(f"Attempting size {attempt_size[0]}x{attempt_size[1]}")
                try:
                    response = await client.post(
                        f"{self.base_url}/images/generations",
                        headers=self.headers,
                        json=payload
                    )
                    logger.info(f"Received response: {response.status_code}")
                    
                    if response.status_code == 200:
                        logger.info("Image generation succeeded")
                        return response.json()
                    
                    # Check for size-related errors; continue to next fallback size
                    try:
                        error_data = response.json()
                        error_msg = str(error_data.get("error", {}).get("message", ""))
                        logger.warning(f"Generation failed: {response.status_code} - {error_msg}")
                        if "Invalid size" in error_msg or "resolution" in error_msg.lower():
                            continue
                    except Exception:
                        pass
                except Exception as e:
                    logger.error(f"Request failed: {e}")
                    continue
        
        raise ValueError(f"Image generation failed after all attempts")
