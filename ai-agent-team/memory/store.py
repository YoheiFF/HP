"""メモリストア抽象基底クラス"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MemoryStore(ABC):
    """永続メモリバックエンドの抽象基底クラス"""

    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        """値を保存する"""
        ...

    @abstractmethod
    async def get(self, key: str, default: Any = None) -> Any:
        """値を取得する"""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """値を削除する"""
        ...

    @abstractmethod
    async def list_keys(self) -> list[str]:
        """全キーを返す"""
        ...
