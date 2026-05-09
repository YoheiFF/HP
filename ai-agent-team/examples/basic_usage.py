"""基本的な使い方のサンプル"""
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.orchestrator import Orchestrator

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


async def main() -> None:
    orchestrator = Orchestrator(config_dir="../config")

    # --- 例1: 単純な質問（エージェント不要）---
    print("=" * 60)
    print("例1: 単純な質問")
    result = await orchestrator.run("Pythonのリスト内包表記とは何ですか？")
    print(result)

    # --- 例2: コード生成 ---
    print("\n" + "=" * 60)
    print("例2: コード生成")
    result = await orchestrator.run(
        "Pythonでフィボナッチ数列を返すジェネレータ関数を実装してください。"
        "型ヒントとdocstringも含めてください。"
    )
    print(result)

    # --- 例3: 複合タスク（複数エージェント）---
    print("\n" + "=" * 60)
    print("例3: 複合タスク")
    result = await orchestrator.run(
        "FastAPIを使ったTODOアプリのREST APIを設計し、"
        "エンドポイント一覧のドキュメントも作成してください。"
    )
    print(result)

    # --- 例4: セッション付き（会話履歴保存）---
    print("\n" + "=" * 60)
    print("例4: セッション付き")
    session_id = "demo-session-001"
    result = await orchestrator.run(
        "機械学習プロジェクトのディレクトリ構造を提案してください。",
        session_id=session_id,
    )
    print(result)

    # 同じセッションで追加質問
    result = await orchestrator.run(
        "その構造でのテストコードはどこに置けばいいですか？",
        session_id=session_id,
    )
    print("\n--- フォローアップ ---")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
