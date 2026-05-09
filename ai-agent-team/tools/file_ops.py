"""ファイル操作ツール"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import aiofiles

from core.tool_base import ToolBase

logger = logging.getLogger(__name__)


class FileOps(ToolBase):
    name = "file_ops"
    description = "ファイルの読み書き・一覧・削除を行う"

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._base_dir = Path(config.get("base_dir", "./workspace")).resolve()
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, path: str) -> Path:
        """ベースディレクトリ外へのパストラバーサルを防ぐ"""
        resolved = (self._base_dir / path).resolve()
        if not str(resolved).startswith(str(self._base_dir)):
            raise ValueError(f"Access denied: {path}")
        return resolved

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "list", "delete", "exists"],
                    "description": "操作種別",
                },
                "path": {
                    "type": "string",
                    "description": "ファイルパス（ベースディレクトリからの相対パス）",
                },
                "content": {
                    "type": "string",
                    "description": "書き込むコンテンツ（write時のみ）",
                },
            },
            "required": ["operation", "path"],
        }

    async def execute(
        self,
        operation: str,
        path: str,
        content: str = "",
    ) -> Any:
        try:
            target = self._safe_path(path)
        except ValueError as e:
            return {"error": str(e)}

        if operation == "read":
            if not target.exists():
                return {"error": f"File not found: {path}"}
            async with aiofiles.open(target, encoding="utf-8") as f:
                return {"content": await f.read()}

        elif operation == "write":
            target.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(target, "w", encoding="utf-8") as f:
                await f.write(content)
            return {"success": True, "path": str(target.relative_to(self._base_dir))}

        elif operation == "list":
            if not target.exists():
                return {"error": f"Directory not found: {path}"}
            entries = [
                {"name": e.name, "is_dir": e.is_dir()}
                for e in sorted(target.iterdir())
            ]
            return {"entries": entries}

        elif operation == "delete":
            if not target.exists():
                return {"error": f"Path not found: {path}"}
            if target.is_dir():
                import shutil
                shutil.rmtree(target)
            else:
                target.unlink()
            return {"success": True}

        elif operation == "exists":
            return {"exists": target.exists()}

        return {"error": f"Unknown operation: {operation}"}
