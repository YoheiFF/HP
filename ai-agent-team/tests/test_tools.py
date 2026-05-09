"""ツールのテスト"""
import os
import pytest

from tools.file_ops import FileOps
from tools.code_exec import CodeExec


@pytest.fixture
def file_ops(tmp_path):
    return FileOps({"enabled": True, "base_dir": str(tmp_path)})


@pytest.fixture
def code_exec():
    return CodeExec({"enabled": True, "max_timeout": 10})


# --- FileOps ---

@pytest.mark.asyncio
async def test_file_ops_write_read(file_ops):
    result = await file_ops(operation="write", path="test.txt", content="hello")
    assert result["success"] is True

    result = await file_ops(operation="read", path="test.txt")
    assert result["content"] == "hello"


@pytest.mark.asyncio
async def test_file_ops_exists(file_ops):
    result = await file_ops(operation="exists", path="nonexistent.txt")
    assert result["exists"] is False

    await file_ops(operation="write", path="exists.txt", content="x")
    result = await file_ops(operation="exists", path="exists.txt")
    assert result["exists"] is True


@pytest.mark.asyncio
async def test_file_ops_list(file_ops):
    await file_ops(operation="write", path="a.txt", content="a")
    await file_ops(operation="write", path="b.txt", content="b")
    result = await file_ops(operation="list", path=".")
    names = [e["name"] for e in result["entries"]]
    assert "a.txt" in names
    assert "b.txt" in names


@pytest.mark.asyncio
async def test_file_ops_path_traversal(file_ops):
    result = await file_ops(operation="read", path="../secret.txt")
    assert "error" in result


# --- CodeExec ---

@pytest.mark.asyncio
async def test_code_exec_simple(code_exec):
    result = await code_exec(code="print('hello')")
    assert result["stdout"].strip() == "hello"
    assert result["returncode"] == 0


@pytest.mark.asyncio
async def test_code_exec_error(code_exec):
    result = await code_exec(code="raise ValueError('oops')")
    assert result["returncode"] != 0
    assert "ValueError" in result["stderr"]


@pytest.mark.asyncio
async def test_code_exec_timeout(code_exec):
    result = await code_exec(code="import time; time.sleep(100)", timeout=1)
    assert "error" in result
    assert "timed out" in result["error"]
