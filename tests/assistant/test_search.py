from pathlib import Path

import pytest

from evidence_anchor.rag.embeddings import HashingEmbedder
from evidence_anchor.rag.index import HybridIndex
from evidence_anchor.rag.search import rrf, search
from evidence_anchor.rag.sources import load_sources

pytestmark = pytest.mark.assistant

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def index(tmp_path_factory: pytest.TempPathFactory) -> HybridIndex:
    idx = HybridIndex(tmp_path_factory.mktemp("idx") / "index.db", HashingEmbedder())
    idx.ingest(load_sources(REPO))
    return idx


def test_rrf_merges_rankings():
    merged = rrf([["a", "b"], ["b", "c"]])

    assert [cid for cid, _ in merged] == ["b", "a", "c"]
    assert merged[0][1] == pytest.approx(1 / 62 + 1 / 61)


def test_search_finds_requirement_by_identifier(index: HybridIndex):
    result = search(index, "¿Qué dice RF-02 sobre una ronda cerrada?", threshold=0.0)

    assert any("RF-02" in hit.text for hit in result.hits)
    assert len(result.hits) == 4


def test_search_marks_insufficient_below_threshold(index: HybridIndex):
    result = search(index, "ronda cerrada", threshold=0.99)

    assert result.sufficient is False
    assert result.threshold == 0.99
    assert result.hits


def test_search_is_sufficient_when_best_match_reaches_threshold(index: HybridIndex):
    result = search(index, "ronda cerrada", threshold=0.0)

    assert result.sufficient is True
    assert result.max_cosine >= 0.0


@pytest.mark.parametrize("query, k", [("", 4), ("   ", 4), ("ronda", 0), ("ronda", 9)])
def test_search_rejects_blank_query_and_bad_k(index: HybridIndex, query: str, k: int):
    with pytest.raises(ValueError):
        search(index, query, k=k, threshold=0.5)


def test_hits_carry_citation_fields(index: HybridIndex):
    result = search(index, "caja delimitadora recortada", threshold=0.0)

    for hit in result.hits:
        assert hit.chunk_id.startswith(hit.source_id + "#")
        assert hit.source_path.endswith(".md")
        assert not Path(hit.source_path).is_absolute()
        assert hit.source_commit
        assert hit.cosine is not None or hit.bm25 is not None
