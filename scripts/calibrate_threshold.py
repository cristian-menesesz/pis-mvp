"""Choose the retrieval sufficiency threshold from labeled questions.

For every question in docs/evidence/assistant/calibration-questions.md, the real corpus
is searched with the real embedding model and the best cosine similarity is recorded.
The threshold is the value that misclassifies the fewest questions; among equally good
values, the midpoint of the widest gap. The output is the evidence for the chosen value.

Usage: uv run python scripts/calibrate_threshold.py
"""

import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from evidence_anchor.config import load_settings
from evidence_anchor.rag.embeddings import OllamaEmbedder
from evidence_anchor.rag.index import HybridIndex
from evidence_anchor.rag.search import search
from evidence_anchor.rag.sources import load_sources

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "docs" / "evidence" / "assistant" / "calibration-questions.md"


def labeled_questions() -> list[tuple[str, str, bool]]:
    rows = []
    for line in QUESTIONS.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0].startswith("Q-"):
            rows.append((cells[0], cells[1], cells[2] == "con respaldo"))
    return rows


def choose_threshold(scored: list[tuple[float, bool]]) -> tuple[float, int]:
    values = sorted({s for s, _ in scored})
    candidates = [values[0] - 1e-6] + [(a + b) / 2 for a, b in zip(values, values[1:])] + [values[-1] + 1e-6]

    def errors(t: float) -> int:
        return sum((s >= t) != supported for s, supported in scored)

    best = min(errors(t) for t in candidates)
    tied = [t for t in candidates if errors(t) == best]
    # Prefer the candidate in the widest gap between neighboring scores.
    def gap(t: float) -> float:
        below = max((s for s in values if s < t), default=t)
        above = min((s for s in values if s >= t), default=t)
        return above - below

    return max(tied, key=gap), best


def main() -> None:
    settings = load_settings()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    with tempfile.TemporaryDirectory() as tmp:
        index = HybridIndex(Path(tmp) / "index.db", OllamaEmbedder(settings.embed_model, settings.ollama_host))
        stats = index.ingest(load_sources(settings.repo_root))
        scored = []
        print(f"date: {datetime.now(UTC).isoformat(timespec='seconds')}")
        print(f"commit: {commit}")
        print(f"embedding model: {settings.embed_model}; chunks indexed: {stats.added}\n")
        print("| ID | Etiqueta | Coseno máximo | Mejor fragmento |")
        print("|---|---|---|---|")
        for qid, question, supported in labeled_questions():
            result = search(index, question, threshold=0.0)
            best = max(result.hits, key=lambda h: h.cosine or -1).chunk_id if result.hits else "-"
            scored.append((result.max_cosine, supported))
            label = "con respaldo" if supported else "sin respaldo"
            print(f"| {qid} | {label} | {result.max_cosine:.4f} | {best} |")
    threshold, errors = choose_threshold(scored)
    low_supported = min(s for s, sup in scored if sup)
    high_unsupported = max(s for s, sup in scored if not sup)
    print(f"\nmenor coseno con respaldo: {low_supported:.4f}")
    print(f"mayor coseno sin respaldo: {high_unsupported:.4f}")
    print(f"separación: {'sí' if low_supported > high_unsupported else 'no (las distribuciones se solapan)'}")
    print(f"umbral elegido τ = {threshold:.4f}; errores de clasificación: {errors} de {len(scored)}")


if __name__ == "__main__":
    main()
