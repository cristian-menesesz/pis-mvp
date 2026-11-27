"""Text embeddings: the Ollama model used in practice and a deterministic stand-in."""

import hashlib
import math
import re
import unicodedata
from typing import Protocol

import httpx
import ollama

DOCUMENT_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "


class EmbeddingUnavailable(RuntimeError):
    """The embedding model could not be reached or failed."""


class Embedder(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class OllamaEmbedder:
    """nomic-embed-text through Ollama; the model expects task prefixes."""

    def __init__(self, model: str, host: str) -> None:
        self._model = model
        self._client = ollama.Client(host=host, timeout=120)

    def _embed(self, inputs: list[str]) -> list[list[float]]:
        try:
            return [list(v) for v in self._client.embed(model=self._model, input=inputs).embeddings]
        except (ollama.ResponseError, httpx.HTTPError, ConnectionError) as exc:
            raise EmbeddingUnavailable(f"embedding model {self._model!r} unavailable: {exc}") from exc

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed([DOCUMENT_PREFIX + t for t in texts]) if texts else []

    def embed_query(self, text: str) -> list[float]:
        return self._embed([QUERY_PREFIX + text])[0]


class HashingEmbedder:
    """Deterministic bag-of-words vectors (hashed, normalized). Used where no model may
    run: the assistant's automated tests (ANCHOR_FAKE_EMBEDDER=1). Not for real answers."""

    def __init__(self, dim: int = 64) -> None:
        self._dim = dim

    def _vector(self, text: str) -> list[float]:
        plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
        vector = [0.0] * self._dim
        for token in re.findall(r"[a-z0-9]+", plain):
            vector[int(hashlib.md5(token.encode()).hexdigest(), 16) % self._dim] += 1.0
        norm = math.sqrt(sum(x * x for x in vector)) or 1.0
        return [x / norm for x in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)
