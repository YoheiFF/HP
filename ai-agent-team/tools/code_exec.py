"""コード実行ツール（サブプロセス）"""
from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any

from core.tool_base import ToolBase

logger = logging.getLogger(__name__)


class CodeExec(ToolBase):
    name = "code_exec"
    description = "Pythonコードを安全なサブプロセスで実行する"

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "実行するPythonコード",
                },
                "timeout": {
                    "type": "integer",
                    "description": "タイムアウト秒数（デフォルト30）",
                    "default": 30,
                },
            },
            "required": ["code"],
        }

    async def execute(self, code: str, timeout: int = 30) -> Any:
        max_timeout = self.config.get("max_timeout", 60)
        timeout = min(timeout, max_timeout)

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                "-c",
                code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                return {"error": f"Execution timed out after {timeout}s"}

            return {
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "returncode": proc.returncode,
            }
        except Exception as e:
            logger.error("Code execution failed: %s", e)
            return {"error": str(e)}
