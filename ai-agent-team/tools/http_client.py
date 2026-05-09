"""HTTPクライアントツール（外部API呼び出し）"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from core.tool_base import ToolBase

logger = logging.getLogger(__name__)


class HttpClient(ToolBase):
    name = "http_client"
    description = "外部APIへHTTPリクエストを送信する"

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                    "description": "HTTPメソッド",
                },
                "url": {
                    "type": "string",
                    "description": "リクエストURL",
                },
                "headers": {
                    "type": "object",
                    "description": "HTTPヘッダー（省略可）",
                },
                "body": {
                    "type": "object",
                    "description": "リクエストボディ（省略可、JSON）",
                },
                "timeout": {
                    "type": "integer",
                    "description": "タイムアウト秒数（デフォルト30）",
                    "default": 30,
                },
            },
            "required": ["method", "url"],
        }

    async def execute(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> Any:
        max_timeout = self.config.get("max_timeout", 60)
        timeout = min(timeout, max_timeout)
        headers = headers or {}

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                resp = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body,
                )
                try:
                    response_body = resp.json()
                except Exception:
                    response_body = resp.text

                return {
                    "status_code": resp.status_code,
                    "headers": dict(resp.headers),
                    "body": response_body,
                }
            except httpx.HTTPError as e:
                logger.error("HTTP request failed: %s", e)
                return {"error": str(e)}
