"""Read stored test results and run single tests of the anchored-comments feature.

A test is named by its catalog id (U-02, I-03, F-02, C-01, U-03b ...). Ids are
validated against a fixed pattern and resolved to pytest functions named
`test_<id>_...`, so no caller-supplied text ever reaches pytest as an expression.
A stored result is current only if the feature and its tests are unchanged since the
run that produced it.
"""

import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

TEST_ID = re.compile(r"^[UIFC]-\d{2}[a-z]?$")
FEATURE_PATHS = (
    "src/review_comments",
    "tests/conftest.py",
    "tests/unit",
    "tests/integration",
    "tests/failure",
    "tests/contract",
)
FEATURE_TEST_DIRS = ("tests/unit", "tests/integration", "tests/failure", "tests/contract")
RESULTS_DIR = Path("docs") / "evidence" / "assistant"
JUNIT_NAME = "junit-latest.xml"
META_NAME = "junit-latest.json"

Status = Literal["passed", "failed", "skipped"]


class ResultError(Exception):
    __test__ = False
    code = "error"


class InvalidTestId(ResultError):
    code = "invalid_test_id"


class TestNotFound(ResultError):
    code = "not_found"


class NoStoredRun(ResultError):
    code = "no_stored_run"


class RunTimeout(ResultError):
    code = "timeout"


@dataclass(frozen=True)
class CaseResult:
    name: str
    status: Status
    duration_s: float


@dataclass(frozen=True)
class TestResult:
    __test__ = False
    test_id: str
    status: Status
    cases: list[CaseResult]
    run_commit: str
    run_date: str
    source: Literal["stored", "live"]
    current: bool
    feature_commit: str


def _git(repo_root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.strip()


def feature_commit(repo_root: Path) -> str:
    """Last commit that changed the feature code or its tests."""
    return _git(repo_root, "log", "-1", "--format=%H", "--", *FEATURE_PATHS)


def feature_has_uncommitted_changes(repo_root: Path) -> bool:
    return bool(_git(repo_root, "status", "--porcelain", "--", *FEATURE_PATHS))


def _prefix(test_id: str) -> str:
    if not isinstance(test_id, str) or not TEST_ID.match(test_id):
        raise InvalidTestId(f"invalid test id {test_id!r}; expected a catalog id such as U-02 or F-02")
    return "test_" + test_id.replace("-", "").lower() + "_"


def _cases(junit: Path, prefix: str) -> list[CaseResult]:
    cases = []
    for case in ET.parse(junit).getroot().iter("testcase"):
        name = case.get("name", "")
        if not name.startswith(prefix):
            continue
        if case.find("failure") is not None or case.find("error") is not None:
            status: Status = "failed"
        elif case.find("skipped") is not None:
            status = "skipped"
        else:
            status = "passed"
        cases.append(CaseResult(name=name, status=status, duration_s=float(case.get("time", 0))))
    return cases


def _aggregate(cases: list[CaseResult]) -> Status:
    if any(c.status == "failed" for c in cases):
        return "failed"
    if all(c.status == "skipped" for c in cases):
        return "skipped"
    return "passed"


def read_stored_result(repo_root: Path, test_id: str, results_dir: Path | None = None) -> TestResult:
    prefix = _prefix(test_id)
    directory = results_dir or repo_root / RESULTS_DIR
    junit, meta_file = directory / JUNIT_NAME, directory / META_NAME
    if not junit.exists() or not meta_file.exists():
        raise NoStoredRun(f"no stored test run in {directory.as_posix()}")
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    cases = _cases(junit, prefix)
    if not cases:
        raise TestNotFound(f"test {test_id} is not in the stored run")
    now = feature_commit(repo_root)
    current = meta.get("feature_commit") == now and not feature_has_uncommitted_changes(repo_root)
    return TestResult(
        test_id=test_id,
        status=_aggregate(cases),
        cases=cases,
        run_commit=meta["commit"],
        run_date=meta["date"],
        source="stored",
        current=current,
        feature_commit=now,
    )


def run_single_test(repo_root: Path, test_id: str, timeout_s: int = 120) -> TestResult:
    prefix = _prefix(test_id)
    with tempfile.TemporaryDirectory() as tmp:
        junit = Path(tmp) / "junit.xml"
        command = [
            sys.executable, "-m", "pytest", *FEATURE_TEST_DIRS,
            "-k", prefix, "-q", "-p", "no:cacheprovider", f"--junitxml={junit}",
        ]
        try:
            completed = subprocess.run(command, cwd=repo_root, capture_output=True, text=True, timeout=timeout_s)
        except subprocess.TimeoutExpired as exc:
            raise RunTimeout(f"test {test_id} did not finish within {timeout_s} s") from exc
        cases = _cases(junit, prefix) if junit.exists() else []
        if completed.returncode == 5 or not cases:
            raise TestNotFound(f"test {test_id} does not exist in the feature's test suite")
    return TestResult(
        test_id=test_id,
        status=_aggregate(cases),
        cases=cases,
        run_commit=_git(repo_root, "rev-parse", "HEAD"),
        run_date=datetime.now(UTC).isoformat(timespec="seconds"),
        source="live",
        current=True,
        feature_commit=feature_commit(repo_root),
    )
