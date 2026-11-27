"""Load the configured RAG sources with their version (git commit and content hash)."""

import hashlib
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "sources.toml"


@dataclass(frozen=True)
class Source:
    id: str
    path: Path
    text: str
    commit: str
    sha256: str
    display_path: str = ""  # path as configured, used in citations


def file_commit(path: Path) -> str:
    """Last commit that touched the file, or "uncommitted" if git has no record of it."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", path.name],
        cwd=path.parent,
        capture_output=True,
        text=True,
    )
    commit = result.stdout.strip()
    return commit if result.returncode == 0 and commit else "uncommitted"


def load_sources(repo_root: Path, config: Path | None = None) -> list[Source]:
    config = config or DEFAULT_CONFIG
    data = tomllib.loads(config.read_text(encoding="utf-8"))
    base = (config.parent / data["root"]).resolve() if "root" in data else repo_root
    sources = []
    for entry in data["source"]:
        path = (base / entry["path"]).resolve()
        raw = path.read_bytes()
        sources.append(
            Source(
                id=entry["id"],
                path=path,
                text=raw.decode("utf-8"),
                commit=file_commit(path),
                sha256=hashlib.sha256(raw).hexdigest(),
                display_path=entry["path"],
            )
        )
    return sources
