"""共通メモリ・状態管理"""
from __future__ import annotations

import logging
import os
from typing import Any

from memory.store import MemoryStore

logger = logging.getLogger(__name__)


class MemoryManager:
    """エージェント間で共有されるメモリ管理クラス"""

    def __init__(self, backend: str = "json", storage_dir: str = "./data/memory"):
        self._store = _create_store(backend, storage_dir)
        self._session: dict[str, Any] = {}  # セッション内一時メモリ

    # --- 永続メモリ（バックエンドに保存）---

    async def set(self, key: str, value: Any, namespace: str = "global") -> None:
        await self._store.set(f"{namespace}:{key}", value)

    async def get(self, key: str, namespace: str = "global", default: Any = None) -> Any:
        return await self._store.get(f"{namespace}:{key}", default)

    async def delete(self, key: str, namespace: str = "global") -> None:
        await self._store.delete(f"{namespace}:{key}")

    async def list_keys(self, namespace: str = "global") -> list[str]:
        all_keys = await self._store.list_keys()
        prefix = f"{namespace}:"
        return [k[len(prefix):] for k in all_keys if k.startswith(prefix)]

    # --- セッションメモリ（プロセス内のみ）---

    def set_session(self, key: str, value: Any) -> None:
        self._session[key] = value

    def get_session(self, key: str, default: Any = None) -> Any:
        return self._session.get(key, default)

    def clear_session(self) -> None:
        self._session.clear()

    # --- 会話履歴 ---

    async def append_conversation(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        history = await self.get(session_id, namespace="conversations", default=[])
        history.append({"role": role, "content": content})
        # 最新100件のみ保持
        if len(history) > 100:
            history = history[-100:]
        await self.set(session_id, history, namespace="conversations")

    async def get_conversation(self, session_id: str) -> list[dict[str, str]]:
        return await self.get(session_id, namespace="conversations", default=[])

    async def clear_conversation(self, session_id: str) -> None:
        await self.delete(session_id, namespace="conversations")


def _create_store(backend: str, storage_dir: str) -> MemoryStore:
    """バックエンド種別に応じてMemoryStoreを生成する"""
    os.makedirs(storage_dir, exist_ok=True)
    if backend == "sqlite":
        from memory.backends.sqlite_backend import SqliteBackend
        return SqliteBackend(os.path.join(storage_dir, "memory.db"))
    else:
        from memory.backends.json_backend import JsonBackend
        return JsonBackend(os.path.join(storage_dir, "memory.json"))
