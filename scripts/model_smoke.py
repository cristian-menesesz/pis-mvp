"""Check that the local Ollama models can make tool calls and produce embeddings.

SDK notes (mcp 2.x, checked in the installed package): server class
`mcp.server.mcpserver.MCPServer` with `@server.tool()` and `server.run("stdio")`;
anticipated failures raise `mcp.server.mcpserver.exceptions.ToolError` and reach the
client as `is_error=True`; client side `mcp.client.stdio.stdio_client` +
`StdioServerParameters` and `mcp.client.session.ClientSession`.

Usage: uv run python scripts/model_smoke.py [model ...]
"""

import subprocess
import sys
import time
from datetime import UTC, datetime

import ollama

WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}


def check_tool_call(client: ollama.Client, model: str, seed: int) -> str:
    start = time.perf_counter()
    response = client.chat(
        model=model,
        messages=[{"role": "user", "content": "What's the weather in La Paz? Use the tool."}],
        tools=[WEATHER_TOOL],
        options={"temperature": 0, "seed": seed},
        think=False,
    )
    elapsed = time.perf_counter() - start
    calls = response.message.tool_calls or []
    valid = any(c.function.name == "get_weather" and "city" in c.function.arguments for c in calls)
    detail = [f"{c.function.name}({dict(c.function.arguments)})" for c in calls]
    return f"seed={seed} valid_tool_call={valid} calls={detail} latency_s={elapsed:.1f}"


def main() -> None:
    models = sys.argv[1:] or ["qwen3.5:4b", "llama3.2"]
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    print(f"date: {datetime.now(UTC).isoformat(timespec='seconds')}")
    print(f"commit: {commit}")
    client = ollama.Client()
    for model in models:
        print(f"\n## {model}")
        for seed in (1, 2, 3):
            print(check_tool_call(client, model, seed), flush=True)
    start = time.perf_counter()
    vector = client.embed(model="nomic-embed-text", input="search_query: ronda cerrada").embeddings[0]
    print(f"\n## nomic-embed-text\nembedding_dim={len(vector)} latency_s={time.perf_counter() - start:.1f}")


if __name__ == "__main__":
    main()
