"""The agent's side of MCP: a real MCP client session to the evidence-anchor server."""

import asyncio
import json
import os
import shlex
import sys
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Any, Protocol

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

DEFAULT_SERVER_CMD = f'"{sys.executable}" -m evidence_anchor.mcp_server'
CONNECT_TIMEOUT_S = 60
CALL_TIMEOUT_S = 300


@dataclass(frozen=True)
class ToolOutcome:
    ok: bool
    data: dict[str, Any]


class ToolGateway(Protocol):
    def specs(self) -> list[dict]: ...

    async def call(self, name: str, arguments: dict) -> ToolOutcome: ...


def _as_ollama_tool(name: str, description: str, schema: dict) -> dict:
    return {"type": "function", "function": {"name": name, "description": description, "parameters": schema}}


# Used only when the server cannot be reached, so the model can still attempt the task
# and every attempt is answered with a recorded `server_unavailable` error.
FALLBACK_SPECS = [
    _as_ollama_tool("search_requirements", "Search the feature's requirement documents.",
                    {"type": "object", "properties": {"query": {"type": "string"}, "k": {"type": "integer"}},
                     "required": ["query"]}),
    _as_ollama_tool("get_test_result", "Stored result of a catalogued test.",
                    {"type": "object", "properties": {"test_id": {"type": "string"}}, "required": ["test_id"]}),
    _as_ollama_tool("run_test", "Run one catalogued test now.",
                    {"type": "object", "properties": {"test_id": {"type": "string"}}, "required": ["test_id"]}),
]


def _parse_error(text: str) -> dict[str, Any]:
    # The SDK prefixes tool errors with "Error executing tool <name>: ".
    try:
        return json.loads(text[text.index("{"):])
    except ValueError:
        return {"error": "tool_error", "detail": text}


class McpToolGateway:
    """Async context manager. If the server cannot be started or initialized, the gateway
    stays usable and answers every call with `server_unavailable`."""

    def __init__(self, command: str | None = None) -> None:
        self.command = command or os.environ.get("ANCHOR_SERVER_CMD") or DEFAULT_SERVER_CMD
        self.unavailable: str | None = None
        self._specs: list[dict] = []
        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None

    async def __aenter__(self) -> "McpToolGateway":
        parts = shlex.split(self.command, posix=os.name != "nt")
        parts = [p.strip('"') for p in parts]
        env = {k: v for k, v in os.environ.items() if k.startswith(("ANCHOR_", "OLLAMA_"))}
        env.update({"PYTHONIOENCODING": "utf-8", "PATH": os.environ.get("PATH", "")})
        params = StdioServerParameters(command=parts[0], args=parts[1:], env=env)
        try:
            read, write = await self._stack.enter_async_context(stdio_client(params))
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await asyncio.wait_for(session.initialize(), CONNECT_TIMEOUT_S)
            listed = await asyncio.wait_for(session.list_tools(), CONNECT_TIMEOUT_S)
        except Exception as exc:  # any failure to reach the server is reported, never raised
            self.unavailable = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
            await self._close()
            return self
        self._session = session
        self._specs = [_as_ollama_tool(t.name, t.description or "", t.input_schema) for t in listed.tools]
        return self

    async def _close(self) -> None:
        try:
            await self._stack.aclose()
        except Exception:
            pass

    async def __aexit__(self, *exc_info: object) -> None:
        await self._close()

    def specs(self) -> list[dict]:
        return self._specs or FALLBACK_SPECS

    async def call(self, name: str, arguments: dict) -> ToolOutcome:
        if self._session is None:
            return ToolOutcome(False, {"error": "server_unavailable", "detail": self.unavailable or "not connected"})
        try:
            result = await asyncio.wait_for(self._session.call_tool(name, arguments), CALL_TIMEOUT_S)
        except Exception as exc:
            return ToolOutcome(False, {"error": "server_unavailable", "detail": f"{type(exc).__name__}: {exc}"})
        text = "".join(getattr(c, "text", "") for c in result.content)
        if result.is_error:
            return ToolOutcome(False, _parse_error(text))
        data = result.structured_content
        if data is None:
            data = json.loads(text) if text.strip().startswith("{") else {"text": text}
        if isinstance(data, dict) and set(data) == {"result"}:
            data = data["result"]
        return ToolOutcome(True, data)
