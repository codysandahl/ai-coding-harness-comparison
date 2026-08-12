import os
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from backend.providers.openai_client import OpenAIClient

# Load environment variables from .env file in project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')

# Configure logging based on LOG_LEVEL environment variable
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO), format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Get the directory of this file
BASE_DIR = Path(__file__).parent

# CORS middleware
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
if isinstance(allowed_origins, list):
    allow_origins_list = allowed_origins
else:
    allow_origins_list = allowed_origins.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/")
async def root():
    return {"status": "Local AI Image Explorer API"}

@app.get("/api/models")
async def get_models():
    """Fetch available models from the configured provider."""
    try:
        client = OpenAIClient()
        models = await client.list_models()
        return {"models": models}
    except Exception as e:
        return {
            "models": [
                {"id": "gpt-4o-mini", "object": "model", "owned_by": "openai"},
                {"id": "gpt-3.5-turbo", "object": "model", "owned_by": "openai"},
                {"id": "dall-e-3", "object": "model", "owned_by": "openai"},
                {"id": "dall-e-2", "object": "model", "owned_by": "openai"},
            ]
        }

@app.post("/api/generation/produce")
async def produce_image(
    base_prompt: str = Body(...),
    remix_phrases: list = Body(default=[]),
    creativity_level: str = Body("normal"),
    model: str = Body("dall-e-3"),
    width: int = Body(512),
    height: int = Body(512),
    seed: int = Body(default=None)
):
    """Generate a single image and return it immediately."""
    try:
        client = OpenAIClient()
        metadata, base64_image = await client.generate_image(
            base_prompt=base_prompt,
            remix_phrases=remix_phrases,
            creativity_level=creativity_level,
            model=model,
            width=width,
            height=height,
            seed=seed
        )
        return {"image": base64_image, "metadata": metadata.to_dict()}
    except Exception as e:
        logger.exception("Generation error: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
