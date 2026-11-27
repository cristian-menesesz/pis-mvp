"""Persistent hybrid index in one SQLite file: FTS5 (BM25) plus float32 vectors.

Ingestion is incremental: a chunk whose content hash is unchanged is not re-embedded,
and chunks of removed sections or sources are deleted, so the index never cites text
that no longer exists.
"""

import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from evidence_anchor.rag.chunking import PATH_SEP, Chunk, chunk_markdown
from evidence_anchor.rag.embeddings import Embedder
from evidence_anchor.rag.sources import Source

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY, path TEXT NOT NULL, commit_id TEXT NOT NULL, sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    heading_path TEXT NOT NULL,
    text TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    ordinal INTEGER NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    chunk_id UNINDEXED, text, tokenize = 'unicode61 remove_diacritics 2'
);
CREATE TABLE IF NOT EXISTS vectors (
    chunk_id TEXT PRIMARY KEY REFERENCES chunks(id), dim INTEGER NOT NULL, data BLOB NOT NULL
);
"""


@dataclass(frozen=True)
class IngestStats:
    added: int
    unchanged: int
    removed: int


@dataclass(frozen=True)
class StoredChunk:
    chunk: Chunk
    source_path: str
    source_commit: str


def fts_query(query: str) -> str:
    """Quote every word so user text can never be read as FTS5 syntax."""
    tokens = re.findall(r"\w+", query)
    return " OR ".join(f'"{t}"' for t in tokens)


class HybridIndex:
    def __init__(self, path: Path, embedder: Embedder) -> None:
        self._path = path
        self._embedder = embedder
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def ingest(self, sources: list[Source]) -> IngestStats:
        wanted: dict[str, tuple[Source, Chunk]] = {}
        for source in sources:
            for chunk in chunk_markdown(source.id, source.text):
                wanted[chunk.id] = (source, chunk)

        with self._connect() as conn:
            existing = {r["id"]: r["sha256"] for r in conn.execute("SELECT id, sha256 FROM chunks")}
        stale = [cid for cid, sha in existing.items() if cid not in wanted or wanted[cid][1].sha256 != sha]
        new = [pair for cid, pair in wanted.items() if existing.get(cid) != pair[1].sha256]
        vectors = self._embedder.embed_documents([chunk.text for _, chunk in new])

        with self._connect() as conn:
            for cid in stale:
                conn.execute("DELETE FROM vectors WHERE chunk_id = ?", (cid,))
                conn.execute("DELETE FROM chunks_fts WHERE chunk_id = ?", (cid,))
                conn.execute("DELETE FROM chunks WHERE id = ?", (cid,))
            for source in sources:
                conn.execute(
                    "INSERT INTO sources (id, path, commit_id, sha256) VALUES (?, ?, ?, ?) "
                    "ON CONFLICT(id) DO UPDATE SET path = excluded.path, "
                    "commit_id = excluded.commit_id, sha256 = excluded.sha256",
                    (source.id, source.display_path or source.path.as_posix(), source.commit, source.sha256),
                )
            for (_, chunk), vector in zip(new, vectors, strict=True):
                conn.execute(
                    "INSERT INTO chunks (id, source_id, heading_path, text, sha256, ordinal) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (chunk.id, chunk.source_id, PATH_SEP.join(chunk.heading_path),
                     chunk.text, chunk.sha256, chunk.ordinal),
                )
                conn.execute("INSERT INTO chunks_fts (chunk_id, text) VALUES (?, ?)", (chunk.id, chunk.text))
                data = np.asarray(vector, dtype=np.float32)
                data /= np.linalg.norm(data) or 1.0
                conn.execute(
                    "INSERT INTO vectors (chunk_id, dim, data) VALUES (?, ?, ?)",
                    (chunk.id, data.size, data.tobytes()),
                )
            live = {s.id for s in sources}
            conn.execute(
                f"DELETE FROM sources WHERE id NOT IN ({','.join('?' * len(live))})", tuple(live)
            ) if live else conn.execute("DELETE FROM sources")
        return IngestStats(added=len(new), unchanged=len(wanted) - len(new), removed=len(stale))

    def chunk_count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]

    def lexical(self, query: str, limit: int) -> list[tuple[str, float]]:
        match = fts_query(query)
        if not match:
            return []
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT chunk_id, bm25(chunks_fts) AS score FROM chunks_fts "
                "WHERE chunks_fts MATCH ? ORDER BY score LIMIT ?",
                (match, limit),
            ).fetchall()
        # SQLite's bm25() is lower-is-better; negate so higher means more relevant.
        return [(r["chunk_id"], -r["score"]) for r in rows]

    def vector(self, query: str, limit: int) -> list[tuple[str, float]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT chunk_id, data FROM vectors").fetchall()
        if not rows:
            return []
        matrix = np.vstack([np.frombuffer(r["data"], dtype=np.float32) for r in rows])
        q = np.asarray(self._embedder.embed_query(query), dtype=np.float32)
        q /= np.linalg.norm(q) or 1.0
        scores = np.clip(matrix @ q, -1.0, 1.0)
        order = np.argsort(-scores)[:limit]
        return [(rows[i]["chunk_id"], float(scores[i])) for i in order]

    def get_chunk(self, chunk_id: str) -> StoredChunk | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT c.*, s.path AS source_path, s.commit_id FROM chunks c "
                "JOIN sources s ON s.id = c.source_id WHERE c.id = ?",
                (chunk_id,),
            ).fetchone()
        if row is None:
            return None
        chunk = Chunk(
            id=row["id"],
            source_id=row["source_id"],
            heading_path=tuple(row["heading_path"].split(PATH_SEP)) if row["heading_path"] else (),
            text=row["text"],
            sha256=row["sha256"],
            ordinal=row["ordinal"],
        )
        return StoredChunk(chunk=chunk, source_path=row["source_path"], source_commit=row["commit_id"])
