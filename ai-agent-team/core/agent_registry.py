"""エージェントの登録・管理・動的ロード"""
from __future__ import annotations

import importlib
import logging
from typing import Any, Type

import anthropic

from .agent_base import AgentBase

logger = logging.getLogger(__name__)

# エージェント名 → モジュールパス のマッピング
_BUILTIN_AGENTS: dict[str, str] = {
    "code_agent": "agents.code_agent.CodeAgent",
    "research_agent": "agents.research_agent.ResearchAgent",
    "document_agent": "agents.document_agent.DocumentAgent",
    "task_agent": "agents.task_agent.TaskAgent",
    "integration_agent": "agents.integration_agent.IntegrationAgent",
}


class AgentRegistry:
    """エージェントの登録・インスタンス化を管理するレジストリ"""

    def __init__(self):
        self._registry: dict[str, str] = dict(_BUILTIN_AGENTS)
        self._instances: dict[str, AgentBase] = {}

    def register(self, name: str, class_path: str) -> None:
        """新しいエージェントクラスを登録する。

        name: エージェント識別子（例: "my_custom_agent"）
        class_path: クラスのフルパス（例: "my_pkg.my_agent.MyAgent"）
        """
        self._registry[name] = class_path
        logger.info("Registered agent: %s → %s", name, class_path)

    def _load_class(self, class_path: str) -> Type[AgentBase]:
        """クラスパス文字列からクラスをインポートする"""
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    def create(
        self,
        name: str,
        client: anthropic.AsyncAnthropic,
        agent_config: dict[str, Any],
        tools_config: dict[str, Any],
        memory: Any = None,
    ) -> AgentBase:
        """エージェントのインスタンスを生成する"""
        if name not in self._registry:
            raise ValueError(f"Unknown agent: {name!r}. Available: {list(self._registry)}")

        cls = self._load_class(self._registry[name])
        agent = cls(
            name=name,
            client=client,
            config=agent_config,
            memory=memory,
        )

        # ツールを登録
        self._bind_tools(agent, name, tools_config)
        return agent

    def _bind_tools(
        self,
        agent: AgentBase,
        agent_name: str,
        tools_config: dict[str, Any],
    ) -> None:
        """設定に基づいてエージェントにツールを紐付ける"""
        mapping: dict[str, list[str]] = tools_config.get("agent_tool_mapping", {})
        tool_names = mapping.get(agent_name, [])

        for tool_name in tool_names:
            try:
                tool_cls_path = f"tools.{tool_name}.{_to_class_name(tool_name)}"
                tool_cls = self._load_class(tool_cls_path)
                tool_instance = tool_cls(tools_config.get("tools", {}).get(tool_name, {}))
                agent.register_tool(tool_instance.get_definition())
                # ツールの実行ハンドラをエージェントに紐付け
                agent._tool_handlers = getattr(agent, "_tool_handlers", {})
                agent._tool_handlers[tool_name] = tool_instance
            except (ImportError, AttributeError) as e:
                logger.warning("Could not load tool %s for %s: %s", tool_name, agent_name, e)

    def get_available_agents(self) -> list[str]:
        """登録済みエージェント名一覧を返す"""
        return list(self._registry.keys())


def _to_class_name(snake_name: str) -> str:
    """snake_case → PascalCase 変換"""
    return "".join(word.capitalize() for word in snake_name.split("_"))
