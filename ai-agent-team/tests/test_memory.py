"""メモリバックエンドのテスト"""
import asyncio
import os
import tempfile

import pytest

from memory.backends.json_backend import JsonBackend
from memory.backends.sqlite_backend import SqliteBackend
from core.memory import MemoryManager


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


# --- JsonBackend ---

@pytest.mark.asyncio
async def test_json_backend_set_get(tmp_dir):
    backend = JsonBackend(os.path.join(tmp_dir, "test.json"))
    await backend.set("foo", "bar")
    assert await backend.get("foo") == "bar"


@pytest.mark.asyncio
async def test_json_backend_delete(tmp_dir):
    backend = JsonBackend(os.path.join(tmp_dir, "test.json"))
    await backend.set("key", 42)
    await backend.delete("key")
    assert await backend.get("key") is None


@pytest.mark.asyncio
async def test_json_backend_list_keys(tmp_dir):
    backend = JsonBackend(os.path.join(tmp_dir, "test.json"))
    await backend.set("a", 1)
    await backend.set("b", 2)
    keys = await backend.list_keys()
    assert set(keys) == {"a", "b"}


# --- SqliteBackend ---

@pytest.mark.asyncio
async def test_sqlite_backend_set_get(tmp_dir):
    backend = SqliteBackend(os.path.join(tmp_dir, "test.db"))
    await backend.set("hello", {"world": True})
    result = await backend.get("hello")
    assert result == {"world": True}


@pytest.mark.asyncio
async def test_sqlite_backend_default(tmp_dir):
    backend = SqliteBackend(os.path.join(tmp_dir, "test.db"))
    result = await backend.get("missing", default="fallback")
    assert result == "fallback"


# --- MemoryManager ---

@pytest.mark.asyncio
async def test_memory_manager_namespace(tmp_dir):
    manager = MemoryManager(backend="json", storage_dir=tmp_dir)
    await manager.set("key", "value1", namespace="ns1")
    await manager.set("key", "value2", namespace="ns2")
    assert await manager.get("key", namespace="ns1") == "value1"
    assert await manager.get("key", namespace="ns2") == "value2"


@pytest.mark.asyncio
async def test_memory_manager_conversation(tmp_dir):
    manager = MemoryManager(backend="json", storage_dir=tmp_dir)
    await manager.append_conversation("session1", "user", "こんにちは")
    await manager.append_conversation("session1", "assistant", "こんにちは！")
    history = await manager.get_conversation("session1")
    assert len(history) == 2
    assert history[0]["role"] == "user"


@pytest.mark.asyncio
async def test_memory_manager_session(tmp_dir):
    manager = MemoryManager(backend="json", storage_dir=tmp_dir)
    manager.set_session("temp", 123)
    assert manager.get_session("temp") == 123
    manager.clear_session()
    assert manager.get_session("temp") is None
