# Local AI Image Explorer - Backend

## Running the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or use the provided script from the project root:
- `start.bat` (Windows)

## API Endpoints

- `GET /api/state` - Get current generation state
- `POST /api/generation/start` - Start continuous generation
- `POST /api/generation/pause` - Pause generation
- `POST /api/generation/resume` - Resume generation
- `POST /api/generation/stop` - Stop generation
- `PUT /api/generation/base-prompt` - Update base prompt
- `PUT /api/generation/remix-phrases` - Update remix phrases
- `PUT /api/generation/settings` - Update generation settings
- `GET /api/images/{index}/download` - Download image with metadata

## Configuration

Edit `.env` in project root:
```
PROVIDER_BASE_URL=https://api.openai.com/v1
PROVIDER_API_KEY=your-api-key-here
IMAGE_GEN_TIMEOUT_S=60
ALLOWED_ORIGINS=http://localhost:5173
```

Adjust creativity levels in `creativity.json`:
```json
{
  "mild": {"temperature": 0.3, "top_p": 0.9},
  "normal": {"temperature": 0.6, "top_p": 0.85},
  "wild": {"temperature": 0.9, "top_p": 0.7}
}
```
