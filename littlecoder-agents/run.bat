set LOG_LEVEL=DEBUG
uv run python -m uvicorn src.backend.main:app --reload --host 0.0.0.0 --port 8000
