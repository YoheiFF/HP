"""Web検索ツール（Brave Search API）"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from core.tool_base import ToolBase

logger = logging.getLogger(__name__)


class WebSearch(ToolBase):
    name = "web_search"
    description = "インターネットで情報を検索する"

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "検索クエリ",
                },
                "num_results": {
                    "type": "integer",
                    "description": "取得件数（デフォルト5）",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    async def execute(self, query: str, num_results: int = 5) -> Any:
        api_key = self.config.get("api_key", "")
        if not api_key:
            return {"error": "Brave Search API key is not configured"}

        base_url = self.config.get("base_url", "https://api.search.brave.com/res/v1/web/search")
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }
        params = {"q": query, "count": num_results}

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(base_url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("web", {}).get("results", [])
                return [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "description": r.get("description"),
                    }
                    for r in results
                ]
            except httpx.HTTPError as e:
                logger.error("Web search failed: %s", e)
                return {"error": str(e)}
