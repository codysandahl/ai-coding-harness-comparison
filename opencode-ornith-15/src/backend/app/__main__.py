"""Entry point: run the app with the configured port."""

from __future__ import annotations

import uvicorn

from app.config import Settings


def main() -> None:
    settings = Settings.load()
    uvicorn.run("app.main:app", host="127.0.0.1", port=settings.port)


if __name__ == "__main__":
    main()
