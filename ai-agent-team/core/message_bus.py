"""エージェント間の非同期メッセージング"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """エージェント間メッセージ"""
    sender: str
    recipient: str
    content: Any
    message_type: str = "task"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


Handler = Callable[[Message], Awaitable[None]]


class MessageBus:
    """エージェント間の非同期メッセージバス"""

    def __init__(self):
        self._queues: dict[str, asyncio.Queue[Message]] = {}
        self._handlers: dict[str, list[Handler]] = {}
        self._history: list[Message] = []

    def subscribe(self, agent_name: str, handler: Handler) -> None:
        """エージェントのメッセージハンドラを登録する"""
        self._handlers.setdefault(agent_name, []).append(handler)
        if agent_name not in self._queues:
            self._queues[agent_name] = asyncio.Queue()

    async def publish(self, message: Message) -> None:
        """メッセージを送信する"""
        self._history.append(message)
        logger.debug("Message: %s → %s [%s]", message.sender, message.recipient, message.message_type)

        if message.recipient in self._queues:
            await self._queues[message.recipient].put(message)

        for handler in self._handlers.get(message.recipient, []):
            try:
                await handler(message)
            except Exception as e:
                logger.error("Handler error for %s: %s", message.recipient, e)

    async def receive(self, agent_name: str, timeout: float = 30.0) -> Message | None:
        """エージェントのメッセージを受信する"""
        queue = self._queues.get(agent_name)
        if queue is None:
            return None
        try:
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def get_history(self, agent_name: str | None = None) -> list[Message]:
        """メッセージ履歴を返す（agent_name指定時はそのエージェント関連のみ）"""
        if agent_name is None:
            return list(self._history)
        return [
            m for m in self._history
            if m.sender == agent_name or m.recipient == agent_name
        ]

    def clear_history(self) -> None:
        self._history.clear()
