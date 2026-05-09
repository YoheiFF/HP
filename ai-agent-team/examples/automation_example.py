"""業務自動化サンプル：定期レポート生成・Slack通知"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.orchestrator import Orchestrator
from core.memory import MemoryManager

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def generate_weekly_report(orchestrator: Orchestrator) -> str:
    """週次レポートを生成する例"""
    task = (
        "今週の開発チームの作業をまとめた週次レポートを作成してください。\n"
        "以下の項目を含むMarkdown形式で:\n"
        "1. 完了したタスク（仮のデータでOK）\n"
        "2. 進行中のタスク\n"
        "3. 来週の計画\n"
        "4. 気になる技術トピック"
    )
    return await orchestrator.run(task, session_id="weekly-report")


async def analyze_code_quality(orchestrator: Orchestrator, code: str) -> str:
    """コード品質分析の例"""
    task = (
        f"以下のコードをレビューしてください:\n\n```python\n{code}\n```\n\n"
        "改善点・バグ・セキュリティ問題を指摘し、改善版コードも提示してください。"
    )
    return await orchestrator.run(task)


async def research_and_summarize(orchestrator: Orchestrator, topic: str) -> str:
    """トピックのリサーチと要約の例"""
    task = f"「{topic}」について調査し、以下を含む日本語のレポートを作成してください:\n- 概要\n- 主なメリット・デメリット\n- 実際の活用事例\n- 導入時の注意点"
    return await orchestrator.run(task)


async def main() -> None:
    orchestrator = Orchestrator(config_dir="../config")

    # --- シナリオ1: 週次レポート生成 ---
    print("=" * 60)
    print("シナリオ1: 週次レポート生成")
    report = await generate_weekly_report(orchestrator)
    print(report[:500], "..." if len(report) > 500 else "")

    # レポートをメモリに保存
    memory = orchestrator.get_memory()
    await memory.set("latest_weekly_report", report, namespace="reports")
    print("\n✓ レポートをメモリに保存しました")

    # --- シナリオ2: コードレビュー ---
    print("\n" + "=" * 60)
    print("シナリオ2: コードレビュー")
    sample_code = """
def get_user(id):
    query = f"SELECT * FROM users WHERE id = {id}"
    return db.execute(query)
"""
    review = await analyze_code_quality(orchestrator, sample_code)
    print(review[:500], "..." if len(review) > 500 else "")

    # --- シナリオ3: 技術トピックのリサーチ ---
    print("\n" + "=" * 60)
    print("シナリオ3: 技術リサーチ")
    research = await research_and_summarize(orchestrator, "AIエージェントのオーケストレーションパターン")
    print(research[:500], "..." if len(research) > 500 else "")

    # --- メモリの確認 ---
    print("\n" + "=" * 60)
    print("保存されたメモリキー一覧:")
    keys = await memory.list_keys(namespace="reports")
    for key in keys:
        print(f"  - reports:{key}")


if __name__ == "__main__":
    asyncio.run(main())
