"""すべてのエージェントが継承する基底クラス"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import anthropic

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """エージェント実行結果"""
    agent_name: str
    success: bool
    output: str
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class AgentBase(ABC):
    """エージェント基底クラス。新しいエージェントはこれを継承する。"""

    def __init__(
        self,
        name: str,
        client: anthropic.AsyncAnthropic,
        config: dict[str, Any],
        memory: Any = None,
    ):
        self.name = name
        self.client = client
        self.config = config
        self.memory = memory
        self.model = config.get("model", "claude-sonnet-4-6")
        self.max_tokens = config.get("max_tokens", 4096)
        self.system_prompt = config.get("system_prompt", "")
        self._tool_definitions: list[dict[str, Any]] = []

    def register_tool(self, tool_definition: dict[str, Any]) -> None:
        """ツール定義を登録する"""
        self._tool_definitions.append(tool_definition)

    def get_tools(self) -> list[dict[str, Any]]:
        """このエージェントが使えるツール定義一覧を返す"""
        return self._tool_definitions

    async def call_claude(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
    ) -> anthropic.types.Message:
        """Claude APIを呼び出す（ツールループ込み）"""
        all_tools = tools or self._tool_definitions
        sys = system or self.system_prompt

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
        }
        if sys:
            kwargs["system"] = sys
        if all_tools:
            kwargs["tools"] = all_tools

        response = await self.client.messages.create(**kwargs)

        # ツール呼び出しがある場合はループ処理
        while response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await self.handle_tool_call(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    })

            messages = [
                *messages,
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": tool_results},
            ]
            kwargs["messages"] = messages
            response = await self.client.messages.create(**kwargs)

        return response

    async def handle_tool_call(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        """ツール呼び出しを処理する（サブクラスでオーバーライド可能）"""
        raise NotImplementedError(f"Tool '{tool_name}' is not implemented in {self.name}")

    def _extract_text(self, response: anthropic.types.Message) -> str:
        """レスポンスからテキストを抽出する"""
        texts = [block.text for block in response.content if block.type == "text"]
        return "\n".join(texts)

    @abstractmethod
    async def run(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        """タスクを実行する。すべてのエージェントが実装する必須メソッド。"""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
