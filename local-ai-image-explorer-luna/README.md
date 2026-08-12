# Local AI Image Explorer

A lightweight app for fast, iterative visual exploration with AI-generated images.

## What it does

- Continuously generates image prompts and images from a base prompt
- Uses remix phrases to create variation across generations
- Lets you pause and resume the generation loop at any time
- Lets you click a generated image to promote its prompt into the new base prompt
- Shows images in a lightbox with full metadata
- Downloads images with attached metadata

## Local development

Backend commands use `uv`; Python does not need to be on your command line.

```powershell
cd src/backend
uv sync --dev
uv run pytest test_app.py
uv run python app.py
```

In a second terminal:

```powershell
cd src/frontend
npm install
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`. The default backend is `http://127.0.0.1:8000` and uses the fake provider, so no API key is required.

## Use OpenAI

Copy `src/backend/.env.example` to `src/backend/.env`, then edit it:

```powershell
cd src/backend
Copy-Item .env.example .env
notepad .env
```

Set `PROVIDER_BASE_URL=https://api.openai.com/v1`, add your `PROVIDER_API_KEY`, and choose an image model available to your account, such as `gpt-image-1` or `dall-e-3`. Keep the key only in `.env`; never commit it. Restart `uv run python app.py` after changing it. The backend will discover models from `/v1/models` and use the configured endpoint for text and image requests.
