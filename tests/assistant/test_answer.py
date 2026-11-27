import asyncio

import pytest

from evidence_anchor.agent.llm import ModelTurn
from evidence_anchor.agent.tools import ToolOutcome
from evidence_anchor.rag.answer import NO_EVIDENCE, answer_question

pytestmark = pytest.mark.assistant

HITS = [{"chunk_id": "SRC-CA#ca-02", "source_path": "docs/requirements/criterios-aceptacion.md",
         "text": "Se rechaza con 409 y no se guarda nada.", "cosine": 0.8},
        {"chunk_id": "SRC-FUN#reglas", "source_path": "docs/requirements/funcionalidad.md",
         "text": "Solo se aceptan comentarios en una ronda abierta.", "cosine": 0.7}]


class OneShot:
    def __init__(self, text: str) -> None:
        self.text = text
        self.prompts: list[list[dict]] = []

    def chat(self, messages, tools):
        self.prompts.append(messages)
        return ModelTurn(content=self.text, thinking=None, tool_calls=[])


class Search:
    def __init__(self, sufficient: bool) -> None:
        self.sufficient = sufficient

    def specs(self):
        return []

    async def call(self, name, arguments):
        return ToolOutcome(True, {"query": arguments["query"], "hits": HITS, "sufficient": self.sufficient,
                                  "max_cosine": 0.8, "threshold": 0.68})


def test_answer_cites_only_retrieved_fragments():
    model = OneShot("Se rechaza con 409 [SRC-CA#ca-02].")

    answer = asyncio.run(answer_question("¿Qué pasa en una ronda cerrada?", model, Search(True)))

    assert answer.cited == ["SRC-CA#ca-02"]
    assert answer.invalid_citations == []
    assert [h["chunk_id"] for h in answer.hits] == ["SRC-CA#ca-02", "SRC-FUN#reglas"]


def test_citation_not_retrieved_is_flagged():
    model = OneShot("Según [SRC-X#inventado] se permite.")

    answer = asyncio.run(answer_question("¿?", model, Search(True)))

    assert answer.invalid_citations == ["SRC-X#inventado"]


def test_insufficient_retrieval_answers_without_calling_the_model():
    model = OneShot("no debería usarse")

    answer = asyncio.run(answer_question("¿Precio?", model, Search(False)))

    assert answer.text == NO_EVIDENCE
    assert model.prompts == []


def test_fragments_reach_the_model_as_delimited_data():
    model = OneShot("ok [SRC-CA#ca-02]")

    asyncio.run(answer_question("¿?", model, Search(True)))
    prompt = model.prompts[0][-1]["content"]

    assert '<fragmento id="SRC-CA#ca-02"' in prompt
