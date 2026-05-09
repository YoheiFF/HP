"""ツール基底クラス（Claude tool_use スキーマ自動生成）"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ToolBase(ABC):
    """すべてのツールが継承する基底クラス"""

    name: str = ""
    description: str = ""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", True)

    def get_definition(self) -> dict[str, Any]:
        """Claude tool_use 形式のスキーマを返す"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.get_input_schema(),
        }

    @abstractmethod
    def get_input_schema(self) -> dict[str, Any]:
        """JSON Schema形式のパラメータスキーマを返す"""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """ツールを実行する"""
        ...

    async def __call__(self, **kwargs: Any) -> Any:
        if not self.enabled:
            return {"error": f"Tool '{self.name}' is disabled"}
        return await self.execute(**kwargs)
