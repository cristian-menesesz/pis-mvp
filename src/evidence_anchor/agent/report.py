"""The agent's final report: built from the model's `submit_report` call, then validated."""

from dataclasses import dataclass, field
from typing import Any, Literal

Conclusion = Literal["sustentada", "no sustentada", "no concluyente"]
CONCLUSIONS = ("sustentada", "no sustentada", "no concluyente")

SUBMIT_REPORT_SPEC = {
    "type": "function",
    "function": {
        "name": "submit_report",
        "description": "Entrega el informe final. Úsala una sola vez, al terminar.",
        "parameters": {
            "type": "object",
            "properties": {
                "requirement": {"type": "string", "description": "Requisito verificado, con su id (p. ej. RF-02)."},
                "sources": {"type": "array", "items": {"type": "string"},
                            "description": "Ids de los fragmentos recuperados que respaldan el informe."},
                "tools_used": {"type": "array", "items": {"type": "string"}},
                "verified_results": {"type": "array", "items": {"type": "string"},
                                     "description": "Ids de las pruebas cuyos resultados se obtuvieron (p. ej. U-02)."},
                "conclusion": {"type": "string", "enum": list(CONCLUSIONS)},
                "limits": {"type": "array", "items": {"type": "string"},
                           "description": "Límites de la conclusión y verificaciones que faltan."},
            },
            "required": ["requirement", "sources", "tools_used", "verified_results", "conclusion", "limits"],
        },
    },
}


class ReportFormatError(ValueError):
    pass


@dataclass(frozen=True)
class Report:
    requirement: str
    sources: list[str]
    tools_used: list[str]
    verified_results: list[str]
    conclusion: Conclusion
    limits: list[str]
    validator_notes: list[str] = field(default_factory=list)


def _str_list(value: Any, name: str) -> list[str]:
    if isinstance(value, str):
        value = [value] if value.strip() else []
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ReportFormatError(f"'{name}' debe ser una lista de textos")
    return value


def parse_report(arguments: dict[str, Any]) -> Report:
    conclusion = arguments.get("conclusion")
    if conclusion not in CONCLUSIONS:
        raise ReportFormatError(f"'conclusion' debe ser uno de {list(CONCLUSIONS)}, no {conclusion!r}")
    requirement = arguments.get("requirement")
    if not isinstance(requirement, str) or not requirement.strip():
        raise ReportFormatError("'requirement' es obligatorio")
    return Report(
        requirement=requirement,
        sources=_str_list(arguments.get("sources", []), "sources"),
        tools_used=_str_list(arguments.get("tools_used", []), "tools_used"),
        verified_results=_str_list(arguments.get("verified_results", []), "verified_results"),
        conclusion=conclusion,
        limits=_str_list(arguments.get("limits", []), "limits"),
    )


def render_markdown(report: Report, question: str) -> str:
    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {i}" for i in items) if items else "- (ninguno)"

    return (
        f"# Informe de verificación\n\n**Pregunta:** {question}\n\n"
        f"**Requisito verificado:** {report.requirement}\n\n"
        f"**Conclusión:** {report.conclusion}\n\n"
        f"## Fuentes consultadas\n{bullets(report.sources)}\n\n"
        f"## Herramientas usadas\n{bullets(report.tools_used)}\n\n"
        f"## Resultados verificados\n{bullets(report.verified_results)}\n\n"
        f"## Límites de la conclusión\n{bullets(report.limits)}\n\n"
        f"## Observaciones del validador\n{bullets(report.validator_notes)}\n"
    )
