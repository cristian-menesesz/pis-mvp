# Asistente evidence-anchor (RAG, MCP y agente)

Responde preguntas de calidad sobre esta funcionalidad con evidencia real: recupera
fragmentos de los requisitos (RAG híbrido), consulta o ejecuta las pruebas del catálogo
mediante un servidor MCP y un agente con un LLM local decide los pasos. El informe solo
afirma lo que un validador en código puede respaldar con lo obtenido en esa ejecución.
Diseño: `docs/design/evidence-anchor.md`.

```
Pregunta ─► agente (Ollama qwen3.5:4b) ─cliente MCP stdio─► servidor evidence-anchor
             decide cada paso                                ├ search_requirements ─► índice SQLite (FTS5 + vectores)
             ▲                                               ├ get_test_result ────► informe JUnit guardado
             └────────── resultados ◄────────────────────────└ run_test ───────────► pytest (una prueba)
                 │
                 ▼ validador en código ─► informe + traza JSONL
```

| Componente | Responsabilidad |
|---|---|
| `src/evidence_anchor/rag/` | Fuentes versionadas (`sources.toml`), fragmentación por estructura, índice híbrido incremental, búsqueda con fusión RRF y umbral de suficiencia calibrado. |
| `src/evidence_anchor/testing/results.py` | Resultado guardado de una prueba (vigente o no) y ejecución de una sola prueba por su id del catálogo. |
| `src/evidence_anchor/mcp_server.py` | Servidor MCP (SDK oficial, stdio) con tres herramientas de solo lectura o verificación. |
| `src/evidence_anchor/agent/` | Bucle del agente, lista blanca de herramientas, fragmentos tratados como datos, validador del informe, trazas. |

Fuentes del RAG: `docs/requirements/funcionalidad.md` (SRC-FUN), `docs/requirements/criterios-aceptacion.md`
(SRC-CA), `README.md` (SRC-README), `docs/evidence/defects.md` (SRC-DEF) y
`docs/evidence/peer-review.md` (SRC-REV); cada fragmento se cita con su id, ruta y commit.

## Reproducir

Requisitos: uv y [Ollama](https://ollama.com) en ejecución local, sin cuentas ni claves.

```powershell
ollama pull qwen3.5:4b
ollama pull nomic-embed-text
uv sync --all-groups
uv run pytest -m assistant -q
uv run python -m evidence_anchor.agent "¿Qué evidencia muestra que no se guarda un comentario en una ronda cerrada?"
```

| Objetivo | Comando |
|---|---|
| Registrar una ejecución de la suite para `get_test_result` | `uv run python scripts/record_test_run.py` |
| Calibrar el umbral de suficiencia | `uv run python scripts/calibrate_threshold.py` |
| Consultas RAG registradas | `uv run python scripts/rag_queries.py` |
| Escenarios T-01 a T-04 (3 semillas) | `uv run python scripts/run_scenarios.py` |
| Comprobar los modelos locales | `uv run python scripts/model_smoke.py` |
| Usar el servidor desde Claude Code | `.mcp.json` lo registra; Claude Code pide aprobarlo |

Variables de entorno (todas opcionales): `ANCHOR_LLM_MODEL` (por defecto `qwen3.5:4b`),
`ANCHOR_EMBED_MODEL` (`nomic-embed-text`), `OLLAMA_HOST` (`http://127.0.0.1:11434`),
`ANCHOR_TAU` (umbral, por defecto el calibrado), `ANCHOR_INDEX` (`.anchor/index.db`),
`ANCHOR_CORPUS` (otro `sources.toml`), `ANCHOR_RESULTS_DIR` (otro informe JUnit guardado),
`ANCHOR_SERVER_CMD` (otro comando para lanzar el servidor MCP).

**Datos y permisos.** Todo es local: los documentos del repositorio, las pruebas con sus
bases temporales y datos ficticios, y modelos de Ollama. Ninguna herramienta escribe,
borra ni publica; `run_test` acepta solo ids del catálogo (`U-02`, `F-02`…), nunca
expresiones de pytest. **Limpieza:** borrar `.anchor/` (índice y trazas locales; se
regenera solo).

## Evidencia (`docs/evidence/assistant/`)

| Archivo | Contenido |
|---|---|
| `model-smoke.txt` | Prueba de llamadas a herramientas de los modelos locales. |
| `calibration-questions.md`, `assistant/calibration.txt` | Preguntas etiquetadas y elección del umbral τ. |
| `junit-latest.xml` / `.json` | Ejecución registrada de la suite que lee `get_test_result`. |
| `rag-queries.md` / `.json` | Consultas RAG con fragmentos, respuesta y verificación. |
| `scenarios.md`, `scenarios/` | Escenarios T-01 a T-04: tabla, trazas e informes por semilla. |
| `defects.md` | Defectos y limitaciones del asistente (DEF-A01, LIM-A01 a LIM-A03). |
| `def-a01-*.jsonl` | Traza antes y después de corregir DEF-A01. |
| `test-run.txt` | Ejecución completa de las pruebas (funcionalidad y asistente). |
