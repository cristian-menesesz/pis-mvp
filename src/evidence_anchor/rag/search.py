"""Hybrid search: BM25 and cosine candidates merged by reciprocal rank fusion.

Whether retrieval counts as evidence is decided here, by code: the best cosine
similarity must reach a calibrated threshold. BM25 scores have no fixed scale and RRF
keeps only ranks, so neither can carry that decision.
"""

from dataclasses import dataclass

from evidence_anchor.rag.index import HybridIndex

CANDIDATES = 10
RRF_K = 60
MAX_K = 8


@dataclass(frozen=True)
class SearchHit:
    chunk_id: str
    heading_path: str
    source_id: str
    source_path: str
    source_commit: str
    text: str
    rrf_score: float
    bm25: float | None
    cosine: float | None


@dataclass(frozen=True)
class SearchResult:
    query: str
    hits: list[SearchHit]
    max_cosine: float
    sufficient: bool
    threshold: float


def rrf(rankings: list[list[str]], k: int = RRF_K) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def search(index: HybridIndex, query: str, k: int = 4, *, threshold: float) -> SearchResult:
    if not query.strip():
        raise ValueError("query must not be blank")
    if not 1 <= k <= MAX_K:
        raise ValueError(f"k must be between 1 and {MAX_K}")

    lexical = index.lexical(query, CANDIDATES)
    vector = index.vector(query, CANDIDATES)
    bm25 = dict(lexical)
    cosine = dict(vector)
    hits = []
    for chunk_id, score in rrf([[c for c, _ in lexical], [c for c, _ in vector]])[:k]:
        stored = index.get_chunk(chunk_id)
        if stored is None:
            continue
        hits.append(
            SearchHit(
                chunk_id=chunk_id,
                heading_path=" › ".join(stored.chunk.heading_path),
                source_id=stored.chunk.source_id,
                source_path=stored.source_path,
                source_commit=stored.source_commit,
                text=stored.chunk.text,
                rrf_score=score,
                bm25=bm25.get(chunk_id),
                cosine=cosine.get(chunk_id),
            )
        )
    max_cosine = max(cosine.values(), default=-1.0)
    return SearchResult(
        query=query,
        hits=hits,
        max_cosine=max_cosine,
        sufficient=max_cosine >= threshold,
        threshold=threshold,
    )
