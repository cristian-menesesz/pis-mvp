"""Ask the agent a question.

Usage: uv run python -m evidence_anchor.agent "<pregunta>" [--seed N] [--temperature T]
       [--trace PATH] [--max-steps N]
Writes the JSONL trace and a Markdown report next to it, and prints the report.
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

from evidence_anchor.agent.llm import OllamaChatModel
from evidence_anchor.agent.loop import run_agent
from evidence_anchor.agent.report import Report, render_markdown
from evidence_anchor.agent.tools import McpToolGateway
from evidence_anchor.agent.trace import TraceWriter
from evidence_anchor.config import load_settings


async def ask(question: str, *, seed: int, temperature: float, trace_path: Path, max_steps: int) -> Report:
    settings = load_settings()
    model = OllamaChatModel(settings.llm_model, settings.ollama_host, temperature=temperature, seed=seed)
    trace = TraceWriter(trace_path)
    trace.write("config", 0, model=settings.llm_model, temperature=temperature, seed=seed,
                embed_model=settings.embed_model, threshold=settings.sufficiency_threshold)
    async with McpToolGateway() as tools:
        report = await run_agent(question, model, tools, max_steps=max_steps, trace=trace)
    trace_path.with_suffix(".md").write_text(render_markdown(report, question), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-steps", type=int, default=8)
    parser.add_argument("--trace", type=Path)
    args = parser.parse_args()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    trace_path = args.trace or Path(".anchor") / "runs" / f"{stamp}.jsonl"
    report = asyncio.run(ask(args.question, seed=args.seed, temperature=args.temperature,
                             trace_path=trace_path, max_steps=args.max_steps))
    sys.stdout.reconfigure(encoding="utf-8")
    print(render_markdown(report, args.question))
    print(f"traza: {trace_path}")


if __name__ == "__main__":
    main()
