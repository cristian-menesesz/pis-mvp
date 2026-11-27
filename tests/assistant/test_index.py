from pathlib import Path

import pytest

from evidence_anchor.rag.embeddings import EmbeddingUnavailable, HashingEmbedder, OllamaEmbedder
from evidence_anchor.rag.index import HybridIndex, IngestStats
from evidence_anchor.rag.sources import Source

pytestmark = pytest.mark.assistant

DOC = """# Reglas

## Ronda

Solo se aceptan comentarios en una ronda abierta (RF-02).

## Decisión

La decisión de cerrar es idempotente.

## Caja

La caja se recorta al ítem.
"""


class CountingEmbedder(HashingEmbedder):
    def __init__(self) -> None:
        super().__init__()
        self.documents_embedded = 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.documents_embedded += len(texts)
        return super().embed_documents(texts)


def source(text: str, sid: str = "SRC-T") -> Source:
    return Source(id=sid, path=Path(f"{sid}.md"), text=text, commit="abc", sha256="0" * 64)


@pytest.fixture
def index(tmp_path: Path) -> HybridIndex:
    idx = HybridIndex(tmp_path / "index.db", CountingEmbedder())
    idx.ingest([source(DOC)])
    return idx


def test_ingest_then_lexical_finds_exact_identifier(index: HybridIndex):
    [(top_id, score), *_] = index.lexical("RF-02", limit=10)

    assert "RF-02" in index.get_chunk(top_id).chunk.text
    assert score > 0


def test_lexical_ignores_accents(index: HybridIndex):
    ids = [cid for cid, _ in index.lexical("decision", limit=10)]

    assert "SRC-T#decision" in ids


def test_reingest_unchanged_embeds_nothing(tmp_path: Path):
    embedder = CountingEmbedder()
    idx = HybridIndex(tmp_path / "index.db", embedder)
    first = idx.ingest([source(DOC)])
    embedded = embedder.documents_embedded

    second = idx.ingest([source(DOC)])

    assert first.added > 0
    assert second == IngestStats(added=0, unchanged=first.added, removed=0)
    assert embedder.documents_embedded == embedded


def test_changed_and_removed_sections_update_index(index: HybridIndex):
    edited = DOC.replace("La caja se recorta al ítem.", "La caja se recorta a la imagen.")
    edited = edited.replace("## Decisión\n\nLa decisión de cerrar es idempotente.\n\n", "")

    stats = index.ingest([source(edited)])

    assert stats.added == 1
    assert stats.removed == 2  # the edited section's old version and the deleted section
    assert index.get_chunk("SRC-T#decision") is None
    assert "imagen" in index.get_chunk("SRC-T#caja").chunk.text


def test_sources_missing_from_ingest_are_removed(index: HybridIndex):
    before = index.chunk_count()

    stats = index.ingest([source("# Otro\ntexto\n", sid="SRC-O")])

    assert before == 3  # the title-only section has no text, so it yields no chunk
    assert stats.removed == before
    assert index.get_chunk("SRC-T#ronda") is None


def test_vector_returns_cosine_in_range(index: HybridIndex):
    results = index.vector("ronda abierta", limit=10)
    scores = [s for _, s in results]

    assert results
    assert all(-1.0 <= s <= 1.0 for s in scores)
    assert scores == sorted(scores, reverse=True)


def test_stored_chunk_keeps_source_version(index: HybridIndex):
    stored = index.get_chunk("SRC-T#ronda")

    assert stored.source_commit == "abc"
    assert stored.source_path == "SRC-T.md"


def test_embedding_unavailable_raises_clear_error():
    embedder = OllamaEmbedder(model="nomic-embed-text", host="http://127.0.0.1:1")

    with pytest.raises(EmbeddingUnavailable):
        embedder.embed_query("ronda")
