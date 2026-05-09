"""タスク管理エージェント"""
from __future__ import annotations

import json  # used for formatting task context
import logging
from typing import Any

from core.agent_base import AgentBase, AgentResult

logger = logging.getLogger(__name__)


class TaskAgent(AgentBase):
    """タスクの計画・追跡・優先順位付けを担当するエージェント"""

    async def run(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        context = context or {}
        system = self.config.get(
            "system_prompt",
            (
                "あなたは優秀なプロジェクトマネージャーです。"
                "タスクの整理・優先順位付け・進捗管理を行います。"
                "具体的なアクションアイテムと期日を明確にしてください。"
            ),
        )

        # メモリから既存タスクを読み込む
        existing_tasks = []
        if self.memory:
            existing_tasks = await self.memory.get("tasks", namespace=self.name, default=[])

        task_context = ""
        if existing_tasks:
            task_context = f"\n\n現在のタスク一覧:\n{json.dumps(existing_tasks, ensure_ascii=False, indent=2)}"

        messages = [{"role": "user", "content": task + task_context}]
        if ctx := context.get("original_task"):
            messages = [
                {
                    "role": "user",
                    "content": (
                        f"元のタスク（参考）:\n{ctx}\n\n"
                        f"あなたへの具体的な指示:\n{task}{task_context}"
                    ),
                }
            ]

        try:
            response = await self.call_claude(messages=messages, system=system)
            output = self._extract_text(response)
            return AgentResult(agent_name=self.name, success=True, output=output)
        except Exception as e:
            logger.error("TaskAgent failed: %s", e, exc_info=True)
            return AgentResult(agent_name=self.name, success=False, output="", error=str(e))

    async def handle_tool_call(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        handler = self._tool_handlers.get(tool_name)
        if handler is None:
            return {"error": f"Tool not found: {tool_name}"}
        result = await handler(**tool_input)
        return result if isinstance(result, dict) else {"result": result}
