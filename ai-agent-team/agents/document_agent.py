"""ドキュメント作成・編集エージェント"""
from __future__ import annotations

import logging
from typing import Any

from core.agent_base import AgentBase, AgentResult

logger = logging.getLogger(__name__)


class DocumentAgent(AgentBase):
    """ドキュメントの作成・編集・フォーマットを担当するエージェント"""

    async def run(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        context = context or {}
        system = self.config.get(
            "system_prompt",
            (
                "あなたは優秀なテクニカルライターです。"
                "明確で読みやすいドキュメントを作成します。"
                "Markdownを適切に使い、構造化された文書を生成してください。"
            ),
        )

        messages = [{"role": "user", "content": task}]
        if ctx := context.get("original_task"):
            messages = [
                {
                    "role": "user",
                    "content": (
                        f"元のタスク（参考）:\n{ctx}\n\n"
                        f"あなたへの具体的な指示:\n{task}"
                    ),
                }
            ]

        try:
            response = await self.call_claude(messages=messages, system=system)
            output = self._extract_text(response)

            # ファイルへの保存が指定されている場合

            if output_path := context.get("output_path"):
                file_ops = self._tool_handlers.get("file_ops")
                if file_ops:
                    await file_ops(operation="write", path=output_path, content=output)

            return AgentResult(agent_name=self.name, success=True, output=output)
        except Exception as e:
            logger.error("DocumentAgent failed: %s", e, exc_info=True)
            return AgentResult(agent_name=self.name, success=False, output="", error=str(e))

    async def handle_tool_call(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        handler = self._tool_handlers.get(tool_name)
        if handler is None:
            return {"error": f"Tool not found: {tool_name}"}
        result = await handler(**tool_input)
        return result if isinstance(result, dict) else {"result": result}
