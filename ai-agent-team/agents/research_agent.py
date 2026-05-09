"""リサーチ・情報収集エージェント"""
from __future__ import annotations

import logging
from typing import Any

from core.agent_base import AgentBase, AgentResult

logger = logging.getLogger(__name__)


class ResearchAgent(AgentBase):
    """Web検索や情報収集・要約を担当するエージェント"""

    async def run(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        context = context or {}
        system = self.config.get(
            "system_prompt",
            (
                "あなたは優秀なリサーチャーです。"
                "Web検索を使って最新情報を収集し、正確にまとめます。"
                "情報の出典を明記してください。"
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
            return AgentResult(agent_name=self.name, success=True, output=output)
        except Exception as e:
            logger.error("ResearchAgent failed: %s", e, exc_info=True)
            return AgentResult(agent_name=self.name, success=False, output="", error=str(e))

    async def handle_tool_call(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        handler = self._tool_handlers.get(tool_name)
        if handler is None:
            return {"error": f"Tool not found: {tool_name}"}
        result = await handler(**tool_input)
        return result if isinstance(result, dict) else {"result": result}
