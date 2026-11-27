import json
from pathlib import Path

import pytest

from evidence_anchor.agent.report import Report
from evidence_anchor.agent.trace import TraceWriter

pytestmark = pytest.mark.assistant


def test_dataclasses_are_written_as_json_objects(tmp_path: Path):
    trace = TraceWriter(tmp_path / "t.jsonl")
    report = Report("RF-02", ["SRC-CA#ca-02"], [], ["U-02"], "sustentada", ["x"])

    trace.write("report", 1, report=report)
    entry = json.loads((tmp_path / "t.jsonl").read_text(encoding="utf-8"))

    assert entry["report"]["conclusion"] == "sustentada"
    assert entry["report"]["sources"] == ["SRC-CA#ca-02"]
