"""The MCP server, exercised through the official SDK's stdio client (a real client)."""

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

pytestmark = pytest.mark.assistant

REPO = Path(__file__).resolve().parents[2]


def call(tmp_path: Path, name: str | None = None, arguments: dict | None = None):
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "evidence_anchor.mcp_server"],
        cwd=REPO,
        env={"ANCHOR_INDEX": str(tmp_path / "index.db"), "ANCHOR_FAKE_EMBEDDER": "1",
             "PYTHONIOENCODING": "utf-8", **({"PATH": os.environ["PATH"]})},
    )

    async def run():
        async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            if name is None:
                return await session.list_tools()
            return await session.call_tool(name, arguments or {})

    return asyncio.run(run())


def error_of(result) -> dict:
    assert result.is_error is True
    text = result.content[0].text  # the SDK prefixes "Error executing tool <name>: "
    return json.loads(text[text.index("{"):])


def test_lists_exactly_three_tools(tmp_path: Path):
    tools = call(tmp_path)

    assert sorted(t.name for t in tools.tools) == ["get_test_result", "run_test", "search_requirements"]


def test_search_requirements_returns_cited_hits(tmp_path: Path):
    result = call(tmp_path, "search_requirements", {"query": "ronda cerrada RF-02"})
    data = result.structured_content

    assert result.is_error is False
    assert data["hits"] and data["hits"][0]["chunk_id"].startswith("SRC-")
    assert "sufficient" in data and "threshold" in data


def test_search_requirements_blank_query_is_an_error(tmp_path: Path):
    assert error_of(call(tmp_path, "search_requirements", {"query": "  "}))["error"] == "invalid_query"


def test_get_test_result_reads_the_recorded_run(tmp_path: Path):
    data = call(tmp_path, "get_test_result", {"test_id": "U-02"}).structured_content

    assert data["status"] == "passed"
    assert data["source"] == "stored"


def test_get_test_result_invalid_id_returns_error_code(tmp_path: Path):
    assert error_of(call(tmp_path, "get_test_result", {"test_id": "U-02; rm -rf"}))["error"] == "invalid_test_id"


def test_get_test_result_unknown_id_returns_not_found(tmp_path: Path):
    assert error_of(call(tmp_path, "get_test_result", {"test_id": "U-99"}))["error"] == "not_found"


def test_run_test_u01_passes_live(tmp_path: Path):
    data = call(tmp_path, "run_test", {"test_id": "U-01"}).structured_content

    assert data["status"] == "passed"
    assert data["source"] == "live"
