"""Tests for the HTTP API surface."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import build_app
from app.models import ImageRecord, RuntimeSettings
from app.session.store import SessionStore
from app.generation.creativity import load_creativity_config
from conftest import FakeClient, FakeGenerator, FAKE_PNG

CONFIG_PATH = __import__("pathlib").Path(__file__).resolve().parent.parent / "creativity.yaml"


def build_test_app():
    settings = Settings()
    store = SessionStore(max_images=50)
    store.settings = RuntimeSettings(
        base_prompt="a lighthouse",
        remix_phrases=["dramatic clouds", "golden hour"],
        width=1024,
        height=1024,
        text_model="gpt-4o-mini",
        image_model="gpt-image-2",
    )
    return build_app(
        client=FakeClient(),
        store=store,
        creativity_config=load_creativity_config(CONFIG_PATH),
        generator=FakeGenerator(),
        settings=settings,
    )


def test_models_endpoint():
    with TestClient(build_test_app()) as client:
        data = client.get("/api/models").json()
        assert "gpt-4o-mini" in data["text_models"]
        assert "gpt-image-2" in data["image_models"]


def test_settings_get_and_update():
    with TestClient(build_test_app()) as client:
        data = client.get("/api/settings").json()
        assert data["text_model"] == "gpt-4o-mini"

        updated = client.post(
            "/api/settings",
            json={"base_prompt": "a new world", "width": 1536},
            headers={"Content-Type": "application/json"},
        ).json()
        assert updated["base_prompt"] == "a new world"
        assert updated["width"] == 1536


def test_generate_status():
    with TestClient(build_test_app()) as client:
        data = client.get("/api/generate").json()
        assert "running" in data
        resp = client.post(
            "/api/generate",
            json={"running": False},
            headers={"Content-Type": "application/json"},
        ).json()
        assert resp["running"] is False


def test_image_endpoint_serves_bytes():
    app = build_test_app()
    record = ImageRecord(
        prompt="p", model="gpt-image-2", size="1024x1024",
        creativity="wild", content_type="image/png", image_bytes=FAKE_PNG,
    )
    with TestClient(app) as client:
        app.state.store.add(record)
        resp = client.get(f"/api/images/{record.id}")
        assert resp.status_code == 200
        assert resp.content == FAKE_PNG
        assert resp.headers["content-type"] == "image/png"


def test_download_returns_image_without_metadata_sidecar():
    app = build_test_app()
    record = ImageRecord(
        prompt="p", model="gpt-image-2", size="1024x1024",
        creativity="wild", content_type="image/png", image_bytes=FAKE_PNG,
    )
    with TestClient(app) as client:
        app.state.store.add(record)
        resp = client.get(f"/api/images/{record.id}/download")
        assert resp.status_code == 200
        # Only the image bytes are returned - no metadata payload.
        assert resp.content == FAKE_PNG
        assert resp.headers["content-type"] == "image/png"
        assert resp.headers["content-disposition"].startswith('attachment; filename="image')
        assert ".png\"" in resp.headers["content-disposition"]


def test_images_list():
    app = build_test_app()
    with TestClient(app) as client:
        app.state.store.add(
            ImageRecord(prompt="p", model="gpt-image-2", size="1024x1024",
                        creativity="normal", content_type="image/png", image_bytes=FAKE_PNG)
        )
        data = client.get("/api/images").json()
        assert len(data) == 1
        assert data[0]["prompt"] == "p"


def test_unknown_image_404():
    with TestClient(build_test_app()) as client:
        assert client.get("/api/images/does-not-exist").status_code == 404
