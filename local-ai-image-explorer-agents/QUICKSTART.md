# Quick Start Guide

## Prerequisites

- Python 3.10+ (already installed)
- uv package manager (already installed)
- OpenAI API key (or compatible provider)

## Setup

1. **Install dependencies** (one-time setup):
   ```bash
   uv venv src/backend/.venv
   uv pip install -r src/backend/requirements.txt --python src/backend/.venv/Scripts/python.exe
   ```

2. **Configure API credentials**:
   - Copy `.env.example` to `.env`
   - Edit `.env` and add your `PROVIDER_API_KEY`
   - Adjust other settings if needed

3. **Run the application**:
   ```bash
   run.bat
   ```
   (Or manually: `set PYTHONPATH=src && cd src\backend && uvicorn main:app --reload`)

4. **Open your browser** to: `http://localhost:8000/static/index.html`

## Usage

- Enter a base prompt and optional remix phrases in the control panel
- Click **Play** to start continuous generation (images appear every ~10s)
- Click **Pause** to stop generation
- Click any generated image to use its prompt as the new base prompt
- Open the lightbox to see full metadata and download the image with metadata

## Files Created

### Backend
- `src/backend/main.py` - FastAPI application
- `src/backend/state.py` - In-memory state management
- `src/backend/config.py` - Configuration loader
- `src/backend/providers/openai_client.py` - AI provider integration
- `src/backend/creativity.json` - Creativity level configuration

### Frontend
- `src/backend/static/index.html` - Web UI

### Utilities
- `src/backend/demo.py` - Self-check script
- `run.bat` - Startup script
- `check.bat` - Verification script

## Constraints Implemented

✅ 10-second generation interval  
✅ No disk persistence until download  
✅ Lightbox pauses generation loop  
✅ Creativity levels configurable without code changes  
✅ Separate text and image model selection  
✅ In-memory storage (max 20 images, Base64)  
✅ Full metadata on download  

## Next Steps

- Test with a valid OpenAI API key
- Adjust creativity levels in `creativity.json` if needed
- Modify design tokens in `design-system/tokens.css` if desired
