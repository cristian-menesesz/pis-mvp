"""Code-enforced checks on the agent's report.

The model may only claim what this run actually obtained: every cited fragment was
retrieved, every cited test has a result from a tool call, and "sustentada" requires
documentary evidence plus at least one current passing result with no error on it.
A report that breaks a rule is downgraded to "no concluyente", never upgraded.
"""

from dataclasses import dataclass, field, replace

from evidence_anchor.agent.report import Report
from evidence_anchor.testing.results import TestResult


@dataclass(frozen=True)
class RunFacts:
    retrieved_ids: set[str]
    results: dict[str, TestResult]
    sufficient_searches: int
    tools_called: list[str]
    errors_by_test: dict[str, str]
    searches: int = 0
    errors: list[tuple[str, str]] = field(default_factory=list)
    failed_ids: set[str] = field(default_factory=set)


def validate(report: Report, facts: RunFacts) -> Report:
    notes: list[str] = []
    violations: list[str] = []

    for chunk_id in report.sources:
        if chunk_id not in facts.retrieved_ids:
            violations.append(f"cita el fragmento {chunk_id}, que no fue recuperado en esta ejecución")
    for test_id in report.verified_results:
        if test_id not in facts.results:
            violations.append(f"cita la prueba {test_id} sin un resultado obtenido en esta ejecución")

    if report.conclusion == "sustentada":
        cited = [facts.results[t] for t in report.verified_results if t in facts.results]
        if not report.sources:
            violations.append("declara 'sustentada' sin citar fragmentos")
        if facts.sufficient_searches == 0:
            violations.append("declara 'sustentada' pero ninguna búsqueda alcanzó el umbral de evidencia")
        if not any(r.current and r.status == "passed" for r in cited):
            violations.append("declara 'sustentada' sin un resultado de prueba vigente y aprobado")
        for result in cited:
            if result.status != "passed":
                violations.append(f"declara 'sustentada' con la prueba {result.test_id} en estado {result.status}")
        for test_id in report.verified_results:
            if test_id in facts.failed_ids:
                violations.append(f"declara 'sustentada' aunque {test_id} falló en esta ejecución")
            if test_id in facts.errors_by_test:
                violations.append(f"declara 'sustentada' aunque la consulta de {test_id} falló "
                                  f"({facts.errors_by_test[test_id]})")

    if sorted(report.tools_used) != sorted(facts.tools_called):
        notes.append(f"herramientas declaradas {report.tools_used} reemplazadas por las realmente usadas "
                     f"{facts.tools_called}")

    if report.conclusion == "no sustentada" and not violations:
        failed_test = bool(facts.failed_ids) or any(r.status == "failed" and r.current for r in facts.results.values())
        undocumented = facts.searches > 0 and facts.sufficient_searches == 0
        if not (failed_test or undocumented):
            violations.append("declara 'no sustentada' sin una prueba fallida ni búsquedas sin respaldo que lo "
                              "muestren; sin evidencia, la conclusión correcta es 'no concluyente'")

    conclusion = "no concluyente" if violations else report.conclusion
    limits = report.limits or [
        "El modelo no declaró límites; la conclusión se apoya solo en los fragmentos y resultados "
        "citados, obtenidos en el entorno local de pruebas."
    ]
    if facts.errors:
        failures = ", ".join(f"{name} ({code})" for name, code in facts.errors)
        limits = [*limits, f"Fallos de herramientas en esta ejecución: {failures}."]
    return replace(report, tools_used=list(facts.tools_called), conclusion=conclusion, limits=limits,
                   validator_notes=[*report.validator_notes, *violations, *notes])
