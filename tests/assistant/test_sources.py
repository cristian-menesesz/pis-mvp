import re
from pathlib import Path

import pytest

from evidence_anchor.rag.sources import load_sources

pytestmark = pytest.mark.assistant

REPO = Path(__file__).resolve().parents[2]


def test_all_configured_sources_load_with_version():
    sources = load_sources(REPO)

    assert [s.id for s in sources] == ["SRC-FUN", "SRC-CA", "SRC-README", "SRC-DEF", "SRC-REV"]
    for source in sources:
        assert source.text.strip()
        assert len(source.sha256) == 64
        assert re.fullmatch(r"[0-9a-f]{40}", source.commit) or source.commit == "uncommitted"


def test_config_root_makes_paths_relative_to_the_config(tmp_path: Path):
    (tmp_path / "doc.md").write_text("# T\nx\n", encoding="utf-8")
    config = tmp_path / "sources.toml"
    config.write_text('root = "."\n[[source]]\nid = "SRC-T"\npath = "doc.md"\n', encoding="utf-8")

    [source] = load_sources(REPO, config)

    assert source.id == "SRC-T"
    assert source.path == tmp_path / "doc.md"
    assert source.commit == "uncommitted"
