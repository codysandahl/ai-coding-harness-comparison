"""OpenAI-API-compatible provider client.

Talks to any endpoint that speaks the OpenAI Chat Completions and Images
Generations APIs. Base URL is read from the environment so the provider can be
swapped without code changes.
"""
import os
import httpx

_BASE_URL = os.environ.get("PROVIDER_BASE_URL", "https://api.openai.com/v1").rstrip("/")
_API_KEY = os.environ.get("PROVIDER_API_KEY", "")


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if _API_KEY:
        h["Authorization"] = f"Bearer {_API_KEY}"
    return h


def _check(r: httpx.Response, what: str) -> None:
    # Surface the provider's own error message instead of just the status line,
    # so a 400 actually tells us WHY (bad model, temperature out of range, …).
    if r.is_error:
        body = r.text
        raise RuntimeError(f"{what} failed ({r.status_code} {r.reason_phrase}): {body}")


async def list_models() -> list[str]:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(f"{_BASE_URL}/models", headers=_headers())
        _check(r, "list models")
        data = r.json().get("data", [])
        return sorted(m["id"] for m in data if "id" in m)


async def generate_prompt(
    *, text_model: str, base_prompt: str, remix_phrases: list[str],
    creativity_guidance: str,
) -> str:
    phrases = "\n".join(f"- {p}" for p in remix_phrases if p.strip()) or "(none)"
    user = (
        f"Base prompt:\n{base_prompt}\n\n"
        f"Remix phrases (mix in one or more):\n{phrases}\n\n"
        "Return ONLY the final image prompt text, on a single line, no quotes, "
        "no preamble, no labels."
    )
    body = {
        "model": text_model,
        "messages": [
            {"role": "system", "content": creativity_guidance},
            {"role": "user", "content": user},
        ],
    }
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{_BASE_URL}/chat/completions", headers=_headers(), json=body)
        _check(r, "chat completions")
        choices = r.json().get("choices", [])
        if not choices:
            raise RuntimeError("text model returned no choices")
        return choices[0]["message"]["content"].strip().strip('"')


async def generate_image(
    *, image_model: str, prompt: str, size: str,
) -> str:
    """Return image bytes as a base64 data URL — never written to disk."""
    import base64
    body = {
        "model": image_model,
        "prompt": prompt,
        "n": 1,
        "size": size,
        "response_format": "b64_json",
    }
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{_BASE_URL}/images/generations", headers=_headers(), json=body)
        _check(r, "image generation")
        item = r.json()["data"][0]
        if "b64_json" in item and item["b64_json"]:
            b64 = item["b64_json"]
        elif item.get("url"):
            img = await c.get(item["url"])
            _check(img, "fetch image url")
            b64 = base64.b64encode(img.content).decode("ascii")
        else:
            raise RuntimeError("image response had neither b64_json nor url")
    return f"data:image/png;base64,{b64}"