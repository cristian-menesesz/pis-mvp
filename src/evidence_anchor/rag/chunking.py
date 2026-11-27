"""Structure-aware chunking of Markdown.

One chunk per heading section; oversized sections are split by paragraph; every table
row becomes its own chunk with the column names repeated, so it can be cited alone.
Each chunk starts with its heading path ("README › Pruebas › U-02").
"""

import hashlib
import re
import unicodedata
from dataclasses import dataclass

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
PATH_SEP = " › "


@dataclass(frozen=True)
class Chunk:
    id: str
    source_id: str
    heading_path: tuple[str, ...]
    text: str
    sha256: str
    ordinal: int


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-") or "x"


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_row(line: str) -> bool:
    return line.lstrip().startswith("|")


def _sections(text: str) -> list[tuple[tuple[str, ...], list[str]]]:
    path: list[str] = []
    sections: list[tuple[tuple[str, ...], list[str]]] = [((), [])]
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        match = None if in_fence else HEADING.match(line)
        if match:
            level = len(match.group(1))
            path = path[: level - 1] + [match.group(2)]
            sections.append((tuple(path), []))
        else:
            sections[-1][1].append(line)
    return sections


def _split_body(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    """Separate prose lines from table rows (each row as its "col: value" cells)."""
    prose: list[str] = []
    rows: list[list[str]] = []
    i = 0
    while i < len(lines):
        if _is_row(lines[i]) and i + 1 < len(lines) and SEPARATOR.match(lines[i + 1]):
            header = _cells(lines[i])
            i += 2
            while i < len(lines) and _is_row(lines[i]):
                values = _cells(lines[i])
                rows.append([f"{h}: {v}" for h, v in zip(header, values, strict=False)])
                i += 1
            continue
        prose.append(lines[i])
        i += 1
    return prose, rows


def _paragraph_groups(prose: list[str], max_chars: int) -> list[str]:
    paragraphs = [p.strip() for p in "\n".join(prose).split("\n\n") if p.strip()]
    groups: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if current and len(candidate) > max_chars:
            groups.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        groups.append(current)
    return groups


def chunk_markdown(source_id: str, text: str, max_chars: int = 1500) -> list[Chunk]:
    sections = _sections(text)
    # A document with a single top-level title: the title stays in the chunk text but
    # not in the id, so ids read like "SRC-README#pruebas/u-02".
    titles = [path for path, _ in sections if len(path) == 1]
    drop = 1 if len(titles) == 1 and all(path[:1] == titles[0] for path, _ in sections if path) else 0
    pieces: list[tuple[tuple[str, ...], str, str]] = []  # (path, slug, body)
    for path, lines in sections:
        base_slug = "/".join(slugify(p) for p in path[drop:]) or "inicio"
        prose, rows = _split_body(lines)
        for body in _paragraph_groups(prose, max_chars):
            pieces.append((path, base_slug, body))
        for cells in rows:
            first_value = cells[0].split(": ", 1)[-1] if cells else ""
            pieces.append((path, f"{base_slug}/{slugify(first_value)}", " | ".join(cells)))

    chunks: list[Chunk] = []
    seen: dict[str, int] = {}
    for ordinal, (path, slug, body) in enumerate(pieces):
        seen[slug] = seen.get(slug, 0) + 1
        suffix = f"-{seen[slug]}" if seen[slug] > 1 else ""
        full = f"{PATH_SEP.join(path)}\n{body}" if path else body
        chunks.append(
            Chunk(
                id=f"{source_id}#{slug}{suffix}",
                source_id=source_id,
                heading_path=path,
                text=full,
                sha256=hashlib.sha256(full.encode("utf-8")).hexdigest(),
                ordinal=ordinal,
            )
        )
    return chunks
