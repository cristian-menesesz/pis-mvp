import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Minimum best-match cosine similarity for retrieval to count as evidence.
# Calibrated by scripts/calibrate_threshold.py; see docs/evidence/assistant/calibration.txt.
DEFAULT_SUFFICIENCY_THRESHOLD = 0.0


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    index_path: Path
    sources_config: Path
    llm_model: str
    embed_model: str
    ollama_host: str
    sufficiency_threshold: float


def load_settings() -> Settings:
    repo_root = Path(os.environ.get("ANCHOR_REPO_ROOT", REPO_ROOT))
    return Settings(
        repo_root=repo_root,
        index_path=Path(os.environ.get("ANCHOR_INDEX", repo_root / ".anchor" / "index.db")),
        sources_config=Path(
            os.environ.get("ANCHOR_CORPUS", repo_root / "src" / "evidence_anchor" / "sources.toml")
        ),
        llm_model=os.environ.get("ANCHOR_LLM_MODEL", "qwen3.5:4b"),
        embed_model=os.environ.get("ANCHOR_EMBED_MODEL", "nomic-embed-text"),
        ollama_host=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"),
        sufficiency_threshold=float(
            os.environ.get("ANCHOR_TAU", DEFAULT_SUFFICIENCY_THRESHOLD)
        ),
    )
