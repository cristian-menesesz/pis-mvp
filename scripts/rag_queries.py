"""Run the RAG queries through the MCP server and record them (practice section B).

Each query is retrieved with the MCP tool `search_requirements` and answered by the local
model from the retrieved fragments only. Writes docs/evidence/assistant/rag-queries.md
(table to verify by hand) and rag-queries.json (raw fragments and scores).

Usage: uv run python scripts/rag_queries.py
"""

import asyncio
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from evidence_anchor.agent.llm import OllamaChatModel
from evidence_anchor.agent.tools import McpToolGateway
from evidence_anchor.config import load_settings
from evidence_anchor.rag.answer import answer_question

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "evidence" / "assistant"
QUERIES = [
    ("RAG-1", "¿Qué ocurre si un revisor intenta comentar en una ronda cerrada y qué pruebas lo verifican?"),
    ("RAG-2", "¿Cómo se calcula la caja del comentario cuando el trazo sale de la imagen?"),
    ("RAG-3", "¿Cuál es el tiempo máximo de respuesta exigido para registrar un comentario?"),
]


async def main() -> None:
    settings = load_settings()
    model = OllamaChatModel(settings.llm_model, settings.ollama_host, temperature=0.0, seed=42)
    async with McpToolGateway() as tools:
        if tools.unavailable:
            sys.exit(f"MCP server unavailable: {tools.unavailable}")
        answers = [(qid, await answer_question(q, model, tools)) for qid, q in QUERIES]

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    date = datetime.now(UTC).isoformat(timespec="seconds")
    (OUT / "rag-queries.json").write_text(
        json.dumps({"date": date, "commit": commit, "model": settings.llm_model,
                    "answers": [{"id": qid, **asdict(a)} for qid, a in answers]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    lines = ["# Consultas RAG", "",
             f"Fecha (UTC): {date}. Commit: `{commit}`. Recuperación: herramienta MCP `search_requirements` "
             f"(híbrida BM25 + `{settings.embed_model}`, τ = {settings.sufficiency_threshold}). Respuesta: "
             f"`{settings.llm_model}`, temperatura 0, solo con los fragmentos recuperados. Fragmentos completos y "
             "puntajes en `rag-queries.json`.", "",
             "La verificación humana la redactó el asistente de IA con su razonamiento y queda pendiente de "
             "confirmación del estudiante.", ""]
    for qid, a in answers:
        lines += [f"## {qid}", "", "| Campo | Registro |", "|---|---|",
                  f"| Consulta | {a.question} |",
                  "| Fuentes recuperadas | " + "<br>".join(
                      f"`{h['chunk_id']}` (coseno {h['cosine']:.3f})" if h.get("cosine") is not None
                      else f"`{h['chunk_id']}`" for h in a.hits) + " |",
                  f"| Suficiencia | coseno máximo {a.max_cosine:.4f}; {'suficiente' if a.sufficient else 'insuficiente'} |",
                  f"| Respuesta del sistema | {a.text.replace(chr(10), ' ')} |",
                  f"| Citas inválidas (no recuperadas) | {', '.join(a.invalid_citations) or 'ninguna'} |",
                  "| Verificación humana | PENDIENTE (borrador del asistente abajo) |", ""]
    (OUT / "rag-queries.md").write_text("\n".join(lines), encoding="utf-8")
    print((OUT / "rag-queries.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
