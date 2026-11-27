from pathlib import Path

import pytest

from evidence_anchor.rag.chunking import chunk_markdown

pytestmark = pytest.mark.assistant

REPO = Path(__file__).resolve().parents[2]

TABLE_DOC = """# Proyecto

## Pruebas

| ID | Nivel | Qué comprueba |
|---|---|---|
| U-02 | Unitaria | Ronda cerrada → rechazo |
| I-01 | Integración | Comentario persistido |
"""


def test_sections_become_chunks_with_heading_path():
    chunks = chunk_markdown("SRC-X", "# A\ntext a\n## B\ntext b\n")

    assert [c.heading_path for c in chunks] == [("A",), ("A", "B")]
    assert chunks[1].text.startswith("A › B\n")
    assert "text b" in chunks[1].text


def test_table_rows_become_self_contained_chunks():
    rows = [c for c in chunk_markdown("SRC-README", TABLE_DOC) if "|" in c.text]

    assert len(rows) == 2
    assert "ID: U-02 | Nivel: Unitaria | Qué comprueba: Ronda cerrada → rechazo" in rows[0].text
    assert rows[0].id == "SRC-README#pruebas/u-02"
    assert rows[1].id == "SRC-README#pruebas/i-01"


def test_oversized_section_splits_by_paragraph():
    body = "\n\n".join(c * 700 for c in "abc")
    chunks = chunk_markdown("SRC-X", f"# Long\n{body}\n", max_chars=1500)

    assert len(chunks) >= 2
    assert all(len(c.text) <= 1500 + len("Long\n") for c in chunks)


def test_ids_are_stable_and_unique():
    doc = "# A\none\n# A\ntwo\n"
    first = chunk_markdown("SRC-X", doc)
    second = chunk_markdown("SRC-X", doc)

    assert [c.id for c in first] == [c.id for c in second]
    assert [c.id for c in first] == ["SRC-X#a", "SRC-X#a-2"]


def test_chunks_carry_content_hash_and_order():
    chunks = chunk_markdown("SRC-X", "# A\none\n# B\ntwo\n")

    assert [c.ordinal for c in chunks] == [0, 1]
    assert all(len(c.sha256) == 64 for c in chunks)
    assert chunks[0].sha256 != chunks[1].sha256


def test_readme_u02_and_u02b_rows_are_distinct():
    chunks = chunk_markdown("SRC-README", (REPO / "README.md").read_text(encoding="utf-8"))
    ids = {c.id for c in chunks}

    assert "SRC-README#pruebas/u-02" in ids
    assert "SRC-README#pruebas/u-02b" in ids
