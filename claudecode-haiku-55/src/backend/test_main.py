from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_creativity_levels_have_three():
    levels = client.get("/api/creativity").json()["levels"]
    assert len(levels) >= 3


def test_prompt_uses_creativity_guidance(monkeypatch):
    seen = {}

    async def fake(method, path, **kwargs):
        seen["system"] = kwargs["json"]["messages"][0]["content"]
        return {"choices": [{"message": {"content": "a new prompt"}}]}

    monkeypatch.setattr(main, "call_provider", fake)
    resp = client.post("/api/prompt", json={
        "base": "a cat", "remix": ["neon", "rain"], "creativity": "wild", "model": "m",
    })
    assert resp.json() == {"prompt": "a new prompt"}
    assert "a cat" in seen["system"]
    assert main.load_creativity()["wild"] in seen["system"]


def test_image_returns_b64(monkeypatch):
    async def fake(method, path, **kwargs):
        assert kwargs["json"]["size"] == "1024x1024"
        return {"data": [{"b64_json": "AAAA"}]}

    monkeypatch.setattr(main, "call_provider", fake)
    resp = client.post("/api/image", json={"prompt": "p", "model": "m", "seed": 7})
    assert resp.json() == {"b64": "AAAA", "mime": "image/png"}
