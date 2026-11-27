"""The language model the agent reasons with, behind a small interface."""

from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx
import ollama


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ModelTurn:
    content: str
    thinking: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)


class ModelUnavailable(RuntimeError):
    """The language model could not be reached or failed."""


class ChatModel(Protocol):
    def chat(self, messages: list[dict], tools: list[dict]) -> ModelTurn: ...


class OllamaChatModel:
    def __init__(self, model: str, host: str, temperature: float = 0.0, seed: int = 42,
                 think: bool = False, num_ctx: int = 8192) -> None:
        self.model = model
        self.options = {"temperature": temperature, "seed": seed, "num_ctx": num_ctx}
        self.think = think
        self._client = ollama.Client(host=host, timeout=600)

    def chat(self, messages: list[dict], tools: list[dict]) -> ModelTurn:
        try:
            response = self._client.chat(
                model=self.model, messages=messages, tools=tools, options=self.options, think=self.think
            )
        except (ollama.ResponseError, httpx.HTTPError, ConnectionError) as exc:
            raise ModelUnavailable(f"model {self.model!r} unavailable: {exc}") from exc
        message = response.message
        calls = [ToolCall(c.function.name, dict(c.function.arguments or {})) for c in message.tool_calls or []]
        return ModelTurn(content=message.content or "", thinking=message.thinking, tool_calls=calls)
