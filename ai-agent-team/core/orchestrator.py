"""オーケストレーター：タスクを受付・分解・振り分け・統合する司令塔"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import anthropic
import yaml
from dotenv import load_dotenv

from .agent_base import AgentResult
from .agent_registry import AgentRegistry
from .memory import MemoryManager
from .message_bus import MessageBus

load_dotenv()
logger = logging.getLogger(__name__)

# オーケストレーターがエージェントを選択するためのツール定義
_DISPATCH_TOOL = {
    "name": "dispatch_agents",
    "description": "タスクを適切なエージェントに振り分けて実行する",
    "input_schema": {
        "type": "object",
        "properties": {
            "subtasks": {
                "type": "array",
                "description": "実行するサブタスクのリスト",
                "items": {
                    "type": "object",
                    "properties": {
                        "agent": {
                            "type": "string",
                            "description": "担当エージェント名",
                            "enum": [
                                "code_agent",
                                "research_agent",
                                "document_agent",
                                "task_agent",
                                "integration_agent",
                            ],
                        },
                        "task": {
                            "type": "string",
                            "description": "そのエージェントへの具体的な指示",
                        },
                        "parallel": {
                            "type": "boolean",
                            "description": "他のタスクと並列実行可能か",
                            "default": False,
                        },
                    },
                    "required": ["agent", "task"],
                },
            },
        },
        "required": ["subtasks"],
    },
}


class Orchestrator:
    """AIエージェントチームの司令塔"""

    def __init__(self, config_dir: str = "./config"):
        self._config_dir = Path(config_dir)
        self._agents_config = self._load_yaml("agents.yaml")
        self._tools_config = self._load_yaml("tools.yaml")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY が設定されていません。.env ファイルを確認してください。")

        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._registry = AgentRegistry()
        self._memory = MemoryManager(
            backend=os.getenv("MEMORY_BACKEND", "json"),
            storage_dir=os.getenv("MEMORY_DIR", "./data/memory"),
        )
        self._bus = MessageBus()

        orch_cfg = self._agents_config.get("agents", {}).get("orchestrator", {})
        self._model = orch_cfg.get("model", "claude-sonnet-4-6")
        self._max_tokens = orch_cfg.get("max_tokens", 4096)
        self._system_prompt = orch_cfg.get("system_prompt", "")

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        path = self._config_dir / filename
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _get_agent(self, name: str) -> Any:
        """エージェントインスタンスを取得（キャッシュ付き）"""
        if not hasattr(self, "_agent_cache"):
            self._agent_cache: dict[str, Any] = {}
        if name not in self._agent_cache:
            agent_cfg = self._agents_config.get("agents", {}).get(name, {})
            agent_cfg.update(self._agents_config.get("defaults", {}))
            # エージェント固有設定を上書き
            agent_cfg.update(self._agents_config.get("agents", {}).get(name, {}))
            self._agent_cache[name] = self._registry.create(
                name=name,
                client=self._client,
                agent_config=agent_cfg,
                tools_config=self._tools_config,
                memory=self._memory,
            )
        return self._agent_cache[name]

    async def run(self, task: str, session_id: str | None = None) -> str:
        """タスクを受け取り、エージェントチームで処理して結果を返す"""
        logger.info("Orchestrator received task: %s", task[:100])

        # 会話履歴に記録
        if session_id:
            await self._memory.append_conversation(session_id, "user", task)

        # Step 1: タスク分解（Claude がどのエージェントに何を依頼するか決定）
        subtasks = await self._plan(task)

        if not subtasks:
            # エージェント不要の単純な質問はオーケストレーター自身が回答
            return await self._direct_answer(task)

        # Step 2: サブタスク実行
        results = await self._execute_subtasks(subtasks, task)

        # Step 3: 結果統合
        final = await self._integrate(task, results)

        if session_id:
            await self._memory.append_conversation(session_id, "assistant", final)

        return final

    async def _plan(self, task: str) -> list[dict[str, Any]]:
        """Claudeにタスク分解を依頼し、サブタスクリストを返す"""
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=self._system_prompt,
            tools=[_DISPATCH_TOOL],
            tool_choice={"type": "auto"},
            messages=[{"role": "user", "content": task}],
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "dispatch_agents":
                return block.input.get("subtasks", [])

        # tool_use が呼ばれなかった → エージェント不要
        return []

    async def _execute_subtasks(
        self,
        subtasks: list[dict[str, Any]],
        original_task: str,
    ) -> list[AgentResult]:
        """サブタスクを並列/順次実行する"""
        parallel = [s for s in subtasks if s.get("parallel", False)]
        sequential = [s for s in subtasks if not s.get("parallel", False)]

        results: list[AgentResult] = []

        # 並列実行
        if parallel:
            parallel_results = await asyncio.gather(
                *[self._run_single(s, original_task) for s in parallel],
                return_exceptions=True,
            )
            for r in parallel_results:
                if isinstance(r, Exception):
                    results.append(AgentResult(
                        agent_name="unknown",
                        success=False,
                        output="",
                        error=str(r),
                    ))
                else:
                    results.append(r)

        # 順次実行
        for subtask in sequential:
            result = await self._run_single(subtask, original_task)
            results.append(result)

        return results

    async def _run_single(
        self,
        subtask: dict[str, Any],
        original_task: str,
    ) -> AgentResult:
        agent_name = subtask["agent"]
        task = subtask["task"]
        try:
            agent = self._get_agent(agent_name)
            logger.info("Running %s: %s", agent_name, task[:80])
            return await agent.run(task, context={"original_task": original_task})
        except Exception as e:
            logger.error("Agent %s failed: %s", agent_name, e, exc_info=True)
            return AgentResult(
                agent_name=agent_name,
                success=False,
                output="",
                error=str(e),
            )

    async def _integrate(self, original_task: str, results: list[AgentResult]) -> str:
        """複数エージェントの結果を統合して最終回答を生成する"""
        if len(results) == 1:
            r = results[0]
            if r.success:
                return r.output
            return f"エラーが発生しました: {r.error}"

        # 複数結果の統合プロンプト
        results_text = "\n\n".join(
            f"### {r.agent_name} の結果\n{r.output if r.success else f'エラー: {r.error}'}"
            for r in results
        )
        integration_prompt = (
            f"元のタスク:\n{original_task}\n\n"
            f"各エージェントの実行結果:\n{results_text}\n\n"
            "上記の結果を統合して、ユーザーへの最終的な回答を日本語でわかりやすくまとめてください。"
        )
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=self._system_prompt,
            messages=[{"role": "user", "content": integration_prompt}],
        )
        texts = [b.text for b in response.content if b.type == "text"]
        return "\n".join(texts)

    async def _direct_answer(self, task: str) -> str:
        """エージェントを使わずオーケストレーター自身が回答する"""
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=self._system_prompt,
            messages=[{"role": "user", "content": task}],
        )
        texts = [b.text for b in response.content if b.type == "text"]
        return "\n".join(texts)

    def get_memory(self) -> MemoryManager:
        return self._memory

    def get_available_agents(self) -> list[str]:
        return self._registry.get_available_agents()
