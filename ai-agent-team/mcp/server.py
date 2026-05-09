"""MCPサーバー：Claude DesktopやClaude Codeからこのエージェントチームを使えるようにする"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Any

import yaml

from core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class MCPServer:
    """JSON-RPC over stdioでMCPプロトコルを実装するサーバー"""

    def __init__(self, config_dir: str = "./config"):
        self._orchestrator = Orchestrator(config_dir=config_dir)
        self._config = self._load_mcp_config(config_dir)
        self._request_id: int = 0

    def _load_mcp_config(self, config_dir: str) -> dict[str, Any]:
        path = os.path.join(config_dir, "mcp.yaml")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    # --- MCP プロトコルハンドラ ---

    async def handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "ai-agent-team",
                "version": "0.1.0",
            },
        }

    async def handle_tools_list(self, params: dict[str, Any]) -> dict[str, Any]:
        tools = [
            {
                "name": "run_task",
                "description": "AIエージェントチームにタスクを実行させる",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "実行するタスク"},
                        "session_id": {"type": "string", "description": "セッションID（省略可）"},
                    },
                    "required": ["task"],
                },
            },
            {
                "name": "get_memory",
                "description": "エージェントの共有メモリから値を取得する",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string"},
                        "namespace": {"type": "string", "default": "global"},
                    },
                    "required": ["key"],
                },
            },
            {
                "name": "set_memory",
                "description": "エージェントの共有メモリに値を保存する",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string"},
                        "value": {},
                        "namespace": {"type": "string", "default": "global"},
                    },
                    "required": ["key", "value"],
                },
            },
            {
                "name": "list_agents",
                "description": "利用可能なエージェント一覧を返す",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]
        return {"tools": tools}

    async def handle_tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        args = params.get("arguments", {})

        if name == "run_task":
            result = await self._orchestrator.run(
                task=args["task"],
                session_id=args.get("session_id"),
            )
            return {"content": [{"type": "text", "text": result}]}

        elif name == "get_memory":
            memory = self._orchestrator.get_memory()
            value = await memory.get(
                args["key"],
                namespace=args.get("namespace", "global"),
            )
            return {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}]}

        elif name == "set_memory":
            memory = self._orchestrator.get_memory()
            await memory.set(
                args["key"],
                args["value"],
                namespace=args.get("namespace", "global"),
            )
            return {"content": [{"type": "text", "text": "saved"}]}

        elif name == "list_agents":
            agents = self._orchestrator.get_available_agents()
            return {"content": [{"type": "text", "text": json.dumps(agents, ensure_ascii=False)}]}

        return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}

    # --- JSON-RPC stdio ループ ---

    async def run(self) -> None:
        logger.info("MCP server started (stdio mode)")
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        loop = asyncio.get_event_loop()
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        transport, _ = await loop.connect_write_pipe(
            asyncio.BaseProtocol, sys.stdout.buffer
        )

        async def write(obj: Any) -> None:
            data = json.dumps(obj, ensure_ascii=False) + "\n"
            transport.write(data.encode("utf-8"))

        while True:
            line = await reader.readline()
            if not line:
                break
            try:
                request = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                continue

            req_id = request.get("id")
            method = request.get("method", "")
            params = request.get("params", {})

            try:
                if method == "initialize":
                    result = await self.handle_initialize(params)
                elif method == "tools/list":
                    result = await self.handle_tools_list(params)
                elif method == "tools/call":
                    result = await self.handle_tools_call(params)
                elif method == "notifications/initialized":
                    continue  # 通知は応答不要
                else:
                    await write({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Method not found: {method}"},
                    })
                    continue

                await write({"jsonrpc": "2.0", "id": req_id, "result": result})

            except Exception as e:
                logger.error("Error handling %s: %s", method, e, exc_info=True)
                await write({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": str(e)},
                })


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    server = MCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
