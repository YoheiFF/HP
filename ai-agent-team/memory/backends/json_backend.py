"""JSONファイルバックエンド"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from memory.store import MemoryStore


class JsonBackend(MemoryStore):
    """JSONファイルを永続ストレージとして使うバックエンド"""

    def __init__(self, path: str):
        self._path = path
        self._lock = asyncio.Lock()
        self._data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if os.path.exists(self._path):
            with open(self._path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._data[key] = value
            self._save()

    async def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._data.pop(key, None)
            self._save()

    async def list_keys(self) -> list[str]:
        return list(self._data.keys())
