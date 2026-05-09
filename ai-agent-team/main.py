"""エントリーポイント：CLIまたはMCPサーバーとして起動"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Agent Team")
    subparsers = parser.add_subparsers(dest="command")

    # run コマンド
    run_parser = subparsers.add_parser("run", help="タスクを実行する")
    run_parser.add_argument("task", help="実行するタスク")
    run_parser.add_argument("--session", "-s", default=None, help="セッションID")
    run_parser.add_argument("--config", "-c", default="./config", help="設定ディレクトリ")

    # mcp コマンド
    mcp_parser = subparsers.add_parser("mcp", help="MCPサーバーとして起動")
    mcp_parser.add_argument("--config", "-c", default="./config", help="設定ディレクトリ")

    # web コマンド
    web_parser = subparsers.add_parser("web", help="FastAPI WebサーバーとしてAPIを起動")
    web_parser.add_argument("--host", default="0.0.0.0", help="ホスト")
    web_parser.add_argument("--port", type=int, default=8000, help="ポート")
    web_parser.add_argument("--config", "-c", default="./config", help="設定ディレクトリ")

    args = parser.parse_args()

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=log_level, format="%(levelname)s %(name)s: %(message)s")

    if args.command == "run":
        from core.orchestrator import Orchestrator
        orch = Orchestrator(config_dir=args.config)

        async def _run() -> None:
            result = await orch.run(args.task, session_id=args.session)
            print(result)

        asyncio.run(_run())

    elif args.command == "mcp":
        from mcp.server import MCPServer
        server = MCPServer(config_dir=args.config)
        asyncio.run(server.run())

    elif args.command == "web":
        import uvicorn
        # 設定ディレクトリをenv経由で渡す（examples/web_app_integration.py を直接使う）
        os.environ.setdefault("CONFIG_DIR", args.config)
        uvicorn.run(
            "examples.web_app_integration:app",
            host=args.host,
            port=args.port,
            log_level=log_level.lower(),
        )

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
