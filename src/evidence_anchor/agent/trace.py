"""Ordered JSONL record of everything the agent did and decided."""

import dataclasses
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _default(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    return str(value)


class TraceWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    def write(self, kind: str, step: int, **data: Any) -> None:
        entry = {"t": datetime.now(UTC).isoformat(timespec="milliseconds"), "step": step, "kind": kind, **data}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False, default=_default) + "\n")
