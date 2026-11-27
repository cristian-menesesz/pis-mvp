"""The agent loop: the model decides each next action; code checks every action.

Each step the model sees the conversation and may call a tool. Code rejects any tool
outside the allowlist, passes retrieved text back as delimited data, records every turn
and call in the trace, and validates the final report against what this run obtained.
"""

import json
import time
from typing import Any

from evidence_anchor.agent.llm import ChatModel, ModelUnavailable
from evidence_anchor.agent.prompts import FRAGMENTS_NOTE, REMINDER, SYSTEM_PROMPT
from evidence_anchor.agent.report import SUBMIT_REPORT_SPEC, Report, ReportFormatError, parse_report
from evidence_anchor.agent.tools import ToolGateway
from evidence_anchor.agent.trace import TraceWriter
from evidence_anchor.agent.validator import RunFacts, validate
from evidence_anchor.testing.results import CaseResult, TestResult

EVIDENCE_TOOLS = ("search_requirements", "get_test_result", "run_test")
ALLOWED = (*EVIDENCE_TOOLS, "submit_report")
BUDGET_WARNING_AT = 2
MAX_SECONDS = 900
BUDGET_WARNING = (
    f"Atención: quedan {BUDGET_WARNING_AT} pasos. Con la evidencia que ya obtuviste, llama ahora a "
    "submit_report; si falta evidencia, indícalo en los límites."
)


def _escape(text: str) -> str:
    return text.replace("<fragmento", "&lt;fragmento").replace("</fragmento", "&lt;/fragmento")


def _search_message(data: dict[str, Any]) -> str:
    meta = {k: data.get(k) for k in ("query", "sufficient", "max_cosine", "threshold")}
    parts = [FRAGMENTS_NOTE, json.dumps(meta, ensure_ascii=False)]
    for hit in data.get("hits", []):
        parts.append(
            f'<fragmento id="{hit["chunk_id"]}" fuente="{hit["source_path"]}">\n'
            f"{_escape(hit['text'])}\n</fragmento>"
        )
    return "\n".join(parts)


def _test_result(data: dict[str, Any]) -> TestResult:
    cases = [CaseResult(**c) for c in data.get("cases", [])]
    return TestResult(**{**data, "cases": cases})


class _Run:
    def __init__(self) -> None:
        self.retrieved: set[str] = set()
        self.results: dict[str, TestResult] = {}
        self.sufficient_searches = 0
        self.tools_called: list[str] = []
        self.errors_by_test: dict[str, str] = {}
        self.searches = 0
        self.errors: list[tuple[str, str]] = []
        self.failed_ids: set[str] = set()

    def record(self, name: str, arguments: dict, ok: bool, data: dict[str, Any]) -> None:
        if name not in self.tools_called:
            self.tools_called.append(name)
        test_id = arguments.get("test_id")
        if not ok:
            self.errors.append((name, str(data.get("error", "error"))))
            if isinstance(test_id, str):
                self.errors_by_test[test_id] = data.get("error", "error")
            return
        if name == "search_requirements":
            self.searches += 1
            self.retrieved.update(h["chunk_id"] for h in data.get("hits", []))
            self.sufficient_searches += bool(data.get("sufficient"))
        else:
            result = _test_result(data)
            if result.status == "failed":
                self.failed_ids.add(result.test_id)
            self.results[result.test_id] = result
            self.errors_by_test.pop(result.test_id, None)

    def facts(self) -> RunFacts:
        return RunFacts(self.retrieved, self.results, self.sufficient_searches, self.tools_called, self.errors_by_test,
                        searches=self.searches, errors=list(self.errors), failed_ids=set(self.failed_ids))


def _stopped(reason: str, run: _Run, question: str) -> Report:
    report = Report(requirement=question, sources=[], tools_used=[], verified_results=[],
                    conclusion="no concluyente", limits=[reason], validator_notes=[f"detenido por código: {reason}"])
    return validate(report, run.facts())


def _finish(report: Report, step: int, trace: TraceWriter) -> Report:
    trace.write("validator", step, notes=report.validator_notes, conclusion=report.conclusion)
    trace.write("report", step, report=report)
    return report


async def run_agent(question: str, model: ChatModel, tools: ToolGateway, *, max_steps: int = 8,
                    max_seconds: float | None = MAX_SECONDS, trace: TraceWriter) -> Report:
    specs = [*tools.specs(), SUBMIT_REPORT_SPEC]
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    run = _Run()
    trace.write("start", 0, question=question, tools=[s["function"]["name"] for s in specs],
                max_steps=max_steps, server_unavailable=getattr(tools, "unavailable", None))

    started = time.monotonic()
    for step in range(1, max_steps + 1):
        if max_seconds is not None and time.monotonic() - started >= max_seconds:
            return _finish(_stopped(f"se alcanzó el límite de tiempo de {max_seconds} s", run, question), step, trace)
        try:
            turn = model.chat(messages, specs)
        except ModelUnavailable as exc:
            trace.write("model_error", step, error=str(exc))
            return _finish(_stopped(f"modelo no disponible: {exc}", run, question), step, trace)
        trace.write("model", step, content=turn.content, thinking=turn.thinking,
                    tool_calls=[{"name": c.name, "arguments": c.arguments} for c in turn.tool_calls])
        messages.append({
            "role": "assistant",
            "content": turn.content,
            "tool_calls": [{"function": {"name": c.name, "arguments": c.arguments}} for c in turn.tool_calls],
        })

        if not turn.tool_calls:
            # Text without a tool call ends nothing: only a delivered report or the step
            # limit ends the run (DEF-A02). The model is reminded every time.
            trace.write("reminder", step)
            messages.append({"role": "user", "content": REMINDER})

        for call in turn.tool_calls:
            if call.name not in ALLOWED:
                trace.write("rejected", step, name=call.name, arguments=call.arguments)
                messages.append({"role": "tool", "tool_name": call.name, "content": json.dumps(
                    {"error": "tool_not_allowed",
                     "detail": f"la herramienta {call.name!r} no está permitida; usa solo {list(ALLOWED)}"},
                    ensure_ascii=False)})
                continue

            if call.name == "submit_report":
                try:
                    draft = parse_report(call.arguments)
                except ReportFormatError as exc:
                    trace.write("rejected", step, name=call.name, arguments=call.arguments, reason=str(exc))
                    messages.append({"role": "tool", "tool_name": call.name,
                                     "content": f"Informe inválido: {exc}. Corrígelo y vuelve a llamar a submit_report."})
                    continue
                report = validate(draft, run.facts())
                trace.write("validator", step, notes=report.validator_notes, conclusion=report.conclusion,
                            draft_conclusion=draft.conclusion)
                trace.write("report", step, report=report)
                return report

            trace.write("tool_call", step, name=call.name, arguments=call.arguments)
            outcome = await tools.call(call.name, call.arguments)
            trace.write("tool_result", step, name=call.name, ok=outcome.ok, data=outcome.data)
            run.record(call.name, call.arguments, outcome.ok, outcome.data)
            if outcome.ok and call.name == "search_requirements":
                content = _search_message(outcome.data)
            else:
                content = json.dumps(outcome.data if outcome.ok else {"error": outcome.data}, ensure_ascii=False)
            messages.append({"role": "tool", "tool_name": call.name, "content": content})

        if max_steps - step == BUDGET_WARNING_AT:
            trace.write("budget", step, remaining=BUDGET_WARNING_AT)
            messages.append({"role": "user", "content": BUDGET_WARNING})

    report = _stopped(f"se alcanzó el límite de {max_steps} pasos sin un informe", run, question)
    trace.write("validator", max_steps, notes=report.validator_notes, conclusion=report.conclusion)
    trace.write("report", max_steps, report=report)
    return report
