"""SQLiteバックエンド"""
from __future__ import annotations

import asyncio
import json
import sqlite3
from typing import Any

from memory.store import MemoryStore


class SqliteBackend(MemoryStore):
    """SQLiteを永続ストレージとして使うバックエンド"""

    def __init__(self, path: str):
        self._path = path
        self._lock = asyncio.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS memory "
                "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            serialized = json.dumps(value, ensure_ascii=False)
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)",
                    (key, serialized),
                )
                conn.commit()

    async def get(self, key: str, default: Any = None) -> Any:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM memory WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return default
        return json.loads(row[0])

    async def delete(self, key: str) -> None:
        async with self._lock:
            with self._connect() as conn:
                conn.execute("DELETE FROM memory WHERE key = ?", (key,))
                conn.commit()

    async def list_keys(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT key FROM memory").fetchall()
        return [r[0] for r in rows]
