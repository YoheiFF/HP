"""外部サービス連携エージェント"""
from __future__ import annotations

import logging
from typing import Any

from core.agent_base import AgentBase, AgentResult

logger = logging.getLogger(__name__)


class IntegrationAgent(AgentBase):
    """Slack・GitHub・Notion等の外部サービス連携を担当するエージェント"""

    async def run(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        context = context or {}
        system = self.config.get(
            "system_prompt",
            (
                "あなたは外部サービス連携の専門家です。"
                "Slack、GitHub、Notion等のAPIを使ってタスクを実行します。"
                "APIレスポンスを解析し、必要な情報を日本語で報告してください。"
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
            logger.error("IntegrationAgent failed: %s", e, exc_info=True)
            return AgentResult(agent_name=self.name, success=False, output="", error=str(e))

    async def handle_tool_call(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        handler = self._tool_handlers.get(tool_name)
        if handler is None:
            return {"error": f"Tool not found: {tool_name}"}
        result = await handler(**tool_input)
        return result if isinstance(result, dict) else {"result": result}
