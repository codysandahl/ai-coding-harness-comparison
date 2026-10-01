"""Tests for the generation loop."""

from __future__ import annotations

import asyncio

from app.generation.generator import Generator
from app.generation.creativity import load_creativity_config
from conftest import FakeClient

CONFIG_PATH = __import__("pathlib").Path(__file__).resolve().parent.parent / "creativity.yaml"


def _config():
    return load_creativity_config(CONFIG_PATH)


async def _drain(queue):
    events = []
    while not queue.empty():
        events.append(await queue.get())
    return events


def test_generate_once_produces_complete_metadata(store, config):
    client = FakeClient()
    gen = Generator(client=client, store=store, creativity_config=config, interval=0)
    asyncio.run(gen._generate_once())

    events = asyncio.run(_drain(gen.queue))
    image_events = [e for e in events if e["type"] == "image"]
    assert len(image_events) == 1
    meta = image_events[0]["metadata"]
    for field in ("model", "size", "creativity", "prompt"):
        assert meta.get(field), f"missing metadata field {field}"
    assert meta["size"] == "1024x1024"
    assert meta["creativity"] == "normal"
    assert client.image_calls[0][0] == "variant 1"  # prompt fed to image model


def test_empty_base_prompt_emits_hint(store_empty, config):
    store_empty.settings.base_prompt = ""
    client = FakeClient()
    gen = Generator(client=client, store=store_empty, creativity_config=config, interval=0)
    asyncio.run(gen._generate_once())
    events = asyncio.run(_drain(gen.queue))
    assert any(e["type"] == "hint" for e in events)
    assert client.image_calls == []


def test_loop_produces_several(store, config):
    client = FakeClient()
    gen = Generator(client=client, store=store, creativity_config=config, interval=0)

    async def _run():
        gen.set_running(True)
        for _ in range(10):
            await asyncio.sleep(0.02)
        gen.set_running(False)
        await gen.shutdown()

    asyncio.run(_run())
    assert len(client.chat_calls) >= 1
    assert len(client.image_calls) >= 1


def test_remix_selection_bounds(store, config):
    client = FakeClient()
    gen = Generator(client=client, store=store, creativity_config=config, interval=0)
    phrases = ["a", "b", "c", "d", "e"]

    async def _run():
        counts = []
        for _ in range(100):
            selected = await gen._select_remix(phrases)
            counts.append(len([p for p in selected.split(",") if p]))
        return counts

    counts = asyncio.run(_run())
    assert all(1 <= n <= len(phrases) for n in counts)
    assert len(set(counts)) > 1  # selection actually varies
