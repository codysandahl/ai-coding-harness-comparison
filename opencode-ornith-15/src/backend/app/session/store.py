"""In-memory session store.

Generated images are held only in memory and are written to disk solely when the
user explicitly downloads one. Nothing here touches the filesystem.
"""

from __future__ import annotations

from ..models import ImageRecord, RuntimeSettings


class SessionStore:
    def __init__(self, max_images: int) -> None:
        self.settings = RuntimeSettings()
        self.max_images = max_images
        self._images: dict[str, ImageRecord] = {}
        self._order: list[str] = []

    def add(self, record: ImageRecord) -> ImageRecord:
        self._images[record.id] = record
        self._order.append(record.id)
        self._prune()
        return record

    def get(self, image_id: str) -> ImageRecord | None:
        return self._images.get(image_id)

    def all(self) -> list[ImageRecord]:
        return [self._images[i] for i in self._order if i in self._images]

    def _prune(self) -> None:
        while len(self._order) > self.max_images:
            oldest = self._order.pop(0)
            self._images.pop(oldest, None)
