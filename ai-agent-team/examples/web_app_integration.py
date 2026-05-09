"""FastAPI Webアプリとの統合サンプル"""
from __future__ import annotations

import logging
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.orchestrator import Orchestrator

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Agent Team API", version="0.1.0")
orchestrator = Orchestrator(config_dir="../config")


# --- リクエスト/レスポンスモデル ---

class TaskRequest(BaseModel):
    task: str
    session_id: str | None = None


class TaskResponse(BaseModel):
    result: str
    session_id: str


class MemorySetRequest(BaseModel):
    key: str
    value: object
    namespace: str = "global"


# --- エンドポイント ---

@app.post("/run", response_model=TaskResponse)
async def run_task(req: TaskRequest) -> TaskResponse:
    """タスクをエージェントチームに実行させる"""
    session_id = req.session_id or str(uuid.uuid4())
    try:
        result = await orchestrator.run(task=req.task, session_id=session_id)
        return TaskResponse(result=result, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents")
async def list_agents() -> dict:
    """利用可能なエージェント一覧"""
    return {"agents": orchestrator.get_available_agents()}


@app.get("/memory/{key}")
async def get_memory(key: str, namespace: str = "global") -> dict:
    """メモリから値を取得"""
    memory = orchestrator.get_memory()
    value = await memory.get(key, namespace=namespace)
    return {"key": key, "namespace": namespace, "value": value}


@app.post("/memory")
async def set_memory(req: MemorySetRequest) -> dict:
    """メモリに値を保存"""
    memory = orchestrator.get_memory()
    await memory.set(req.key, req.value, namespace=req.namespace)
    return {"success": True}


@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str) -> dict:
    """会話履歴を取得"""
    memory = orchestrator.get_memory()
    history = await memory.get_conversation(session_id)
    return {"session_id": session_id, "history": history}


@app.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str) -> dict:
    """会話履歴を削除"""
    memory = orchestrator.get_memory()
    await memory.clear_conversation(session_id)
    return {"success": True}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# --- 起動 ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
