import json
import shutil
from pathlib import Path

import pytest

from evidence_anchor.testing.results import (
    InvalidTestId,
    NoStoredRun,
    TestNotFound,
    feature_commit,
    read_stored_result,
    run_single_test,
)

pytestmark = pytest.mark.assistant

REPO = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures" / "results"


def stored_run(tmp_path: Path, feature: str) -> Path:
    shutil.copy(FIXTURE / "junit-latest.xml", tmp_path / "junit-latest.xml")
    (tmp_path / "junit-latest.json").write_text(
        json.dumps({"commit": "a" * 40, "feature_commit": feature, "date": "2026-11-27T00:00:00Z",
                    "command": "pytest"}),
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def current_dir(tmp_path: Path) -> Path:
    return stored_run(tmp_path, feature_commit(REPO))


@pytest.mark.parametrize("bad", ["U2", "X-01", "U-02; rm", "-k x", "u-02", "U-002", ""])
def test_invalid_ids_are_rejected(current_dir: Path, bad: str):
    with pytest.raises(InvalidTestId) as error:
        read_stored_result(REPO, bad, results_dir=current_dir)
    assert error.value.code == "invalid_test_id"


def test_u02_does_not_match_u02b(current_dir: Path):
    result = read_stored_result(REPO, "U-02", results_dir=current_dir)

    assert [c.name for c in result.cases] == ["test_u02_closed_round_rejects_comment_and_stores_nothing"]
    assert result.status == "passed"
    assert result.source == "stored"


def test_parametrized_cases_aggregate_to_failed(current_dir: Path):
    result = read_stored_result(REPO, "U-03b", results_dir=current_dir)

    assert len(result.cases) == 3
    assert result.status == "failed"


def test_all_skipped_cases_give_skipped(current_dir: Path):
    assert read_stored_result(REPO, "U-07", results_dir=current_dir).status == "skipped"


def test_unknown_id_is_not_found(current_dir: Path):
    with pytest.raises(TestNotFound) as error:
        read_stored_result(REPO, "U-99", results_dir=current_dir)
    assert error.value.code == "not_found"


def test_missing_stored_run_is_reported(tmp_path: Path):
    with pytest.raises(NoStoredRun) as error:
        read_stored_result(REPO, "U-02", results_dir=tmp_path)
    assert error.value.code == "no_stored_run"


def test_stored_result_is_current_when_feature_unchanged(current_dir: Path):
    result = read_stored_result(REPO, "U-02", results_dir=current_dir)

    assert result.current is True
    assert result.feature_commit == feature_commit(REPO)


def test_stored_result_is_stale_when_feature_commit_differs(tmp_path: Path):
    result = read_stored_result(REPO, "U-02", results_dir=stored_run(tmp_path, "0" * 40))

    assert result.current is False


def test_run_single_test_runs_real_u01():
    result = run_single_test(REPO, "U-01")

    assert result.status == "passed"
    assert result.source == "live"
    assert result.current is True
    assert result.cases and all(c.name.startswith("test_u01_") for c in result.cases)


def test_run_single_test_unknown_id_is_not_found():
    with pytest.raises(TestNotFound):
        run_single_test(REPO, "I-99")
