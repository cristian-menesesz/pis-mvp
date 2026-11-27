import pytest

from evidence_anchor.agent.report import Report
from evidence_anchor.agent.validator import RunFacts, validate
from evidence_anchor.testing.results import CaseResult, TestResult

pytestmark = pytest.mark.assistant


def result(test_id: str, status: str = "passed", current: bool = True) -> TestResult:
    return TestResult(test_id=test_id, status=status, cases=[CaseResult("test_x", status, 0.0)],
                      run_commit="c", run_date="d", source="stored", current=current, feature_commit="f")


def report(**overrides) -> Report:
    base = dict(requirement="RF-02", sources=["SRC-CA#ca-02"], tools_used=["search_requirements", "get_test_result"],
                verified_results=["U-02"], conclusion="sustentada", limits=["solo pruebas automatizadas"])
    return Report(**{**base, **overrides})


def facts(**overrides) -> RunFacts:
    base = dict(retrieved_ids={"SRC-CA#ca-02"}, results={"U-02": result("U-02")}, sufficient_searches=1,
                tools_called=["search_requirements", "get_test_result"], errors_by_test={}, searches=1,
                errors=[], failed_ids=set())
    return RunFacts(**{**base, **overrides})


def test_valid_sustentada_report_passes_unchanged():
    checked = validate(report(), facts())

    assert checked.conclusion == "sustentada"
    assert checked.validator_notes == []


def test_citing_a_fragment_not_retrieved_downgrades():
    checked = validate(report(sources=["SRC-CA#ca-02", "SRC-X#invented"]), facts())

    assert checked.conclusion == "no concluyente"
    assert any("SRC-X#invented" in n for n in checked.validator_notes)


def test_citing_a_test_without_result_in_this_run_downgrades():
    checked = validate(report(verified_results=["U-02", "F-02"]), facts())

    assert checked.conclusion == "no concluyente"
    assert any("F-02" in n for n in checked.validator_notes)


def test_sustentada_needs_a_current_passed_result():
    checked = validate(report(), facts(results={"U-02": result("U-02", current=False)}))

    assert checked.conclusion == "no concluyente"


def test_sustentada_with_a_failed_result_downgrades():
    checked = validate(report(), facts(results={"U-02": result("U-02", status="failed")}))

    assert checked.conclusion == "no concluyente"


def test_sustentada_when_no_search_was_sufficient_downgrades():
    checked = validate(report(), facts(sufficient_searches=0))

    assert checked.conclusion == "no concluyente"


def test_sustentada_without_sources_downgrades():
    checked = validate(report(sources=[]), facts())

    assert checked.conclusion == "no concluyente"


def test_tool_error_on_a_cited_test_blocks_sustentada():
    checked = validate(report(), facts(errors_by_test={"U-02": "not_found"}))

    assert checked.conclusion == "no concluyente"


def test_tools_used_is_replaced_by_the_tools_actually_called():
    checked = validate(report(tools_used=["run_test"]), facts())

    assert checked.tools_used == ["search_requirements", "get_test_result"]
    assert any("run_test" in n for n in checked.validator_notes)


def test_negative_conclusions_are_never_upgraded():
    checked = validate(report(conclusion="no sustentada"), facts())

    assert checked.conclusion != "sustentada"  # unbacked "no sustentada" becomes "no concluyente" (I-2)


def test_report_without_limits_gets_a_stated_limit():
    checked = validate(report(limits=[]), facts())

    assert checked.limits and "no declaró límites" in checked.limits[0]
    assert checked.conclusion == "sustentada"


def test_no_sustentada_without_any_evidence_becomes_no_concluyente():
    # Review I-2: with the server down the model said "no sustentada" with no evidence at all.
    checked = validate(report(conclusion="no sustentada", sources=[], verified_results=[]),
                       facts(retrieved_ids=set(), results={}, sufficient_searches=0, tools_called=["search_requirements"],
                             searches=0))

    assert checked.conclusion == "no concluyente"


def test_no_sustentada_with_invented_citation_becomes_no_concluyente():
    checked = validate(report(conclusion="no sustentada", sources=["SRC-X#invented"]), facts())

    assert checked.conclusion == "no concluyente"


def test_no_sustentada_backed_by_a_failed_current_test_stands():
    checked = validate(report(conclusion="no sustentada"), facts(results={"U-02": result("U-02", status="failed")}))

    assert checked.conclusion == "no sustentada"


def test_no_sustentada_backed_by_insufficient_searches_stands():
    checked = validate(report(conclusion="no sustentada", sources=[], verified_results=[]),
                       facts(retrieved_ids=set(), results={}, sufficient_searches=0, searches=2))

    assert checked.conclusion == "no sustentada"


def test_tool_errors_are_named_in_the_limits():
    checked = validate(report(conclusion="no concluyente", verified_results=[]),
                       facts(results={}, errors=[("get_test_result", "not_found")]))

    assert any("get_test_result" in l and "not_found" in l for l in checked.limits)


def test_an_earlier_failed_result_blocks_sustentada():
    # Review M-1: a failure seen in this run must not be hidden by a later pass.
    checked = validate(report(), facts(failed_ids={"U-02"}))

    assert checked.conclusion == "no concluyente"
