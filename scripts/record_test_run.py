"""Run the feature's full test suite and store the JUnit report the MCP tools read.

Writes docs/evidence/assistant/junit-latest.xml and junit-latest.json (commit, feature
commit, UTC date, command). The machine's hostname is removed from the report.

Usage: uv run python scripts/record_test_run.py
"""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

from evidence_anchor.testing.results import (
    FEATURE_TEST_DIRS,
    JUNIT_NAME,
    META_NAME,
    RESULTS_DIR,
    feature_commit,
    feature_has_uncommitted_changes,
)

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    if feature_has_uncommitted_changes(ROOT):
        sys.exit("feature code or tests have uncommitted changes; commit them before recording a run")
    out = ROOT / RESULTS_DIR
    junit = out / JUNIT_NAME
    command = [sys.executable, "-m", "pytest", *FEATURE_TEST_DIRS, "-q", "-p", "no:cacheprovider", f"--junitxml={junit}"]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    print(completed.stdout.strip().splitlines()[-1])

    tree = ET.parse(junit)
    for suite in tree.getroot().iter("testsuite"):
        suite.attrib.pop("hostname", None)
    tree.write(junit, encoding="utf-8", xml_declaration=True)

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    meta = {
        "commit": commit,
        "feature_commit": feature_commit(ROOT),
        "date": datetime.now(UTC).isoformat(timespec="seconds"),
        "command": "uv run pytest " + " ".join(FEATURE_TEST_DIRS) + f" --junitxml={RESULTS_DIR.as_posix()}/{JUNIT_NAME}",
        "exit_code": completed.returncode,
    }
    (out / META_NAME).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
