# Segundo cliente MCP: Claude Code

Claude Code (aplicación de escritorio) cargó el servidor `evidence-anchor` desde
`.mcp.json` del repositorio, con aprobación del estudiante, y lo invocó como cliente MCP
independiente del agente. Fecha: 2026-11-27. Commit del servidor: `60af791`. Embeddings
reales (`nomic-embed-text` en Ollama local).

## Invocación con éxito: `search_requirements`

Argumentos: `{"query": "¿Qué pasa con un comentario enviado a una ronda cerrada?", "k": 3}`

Resultado (resumen; los textos completos van en la respuesta):

| Fragmento | Fuente | Commit | Coseno | BM25 |
|---|---|---|---|---|
| `SRC-CA#ca-02-rechazar-comentarios-en-una-ronda-cerrada-rf-02` | `docs/requirements/criterios-aceptacion.md` | `b48c41e` | 0,7792 | 5,14 |
| `SRC-CA#ca-03-cerrar-una-ronda-ya-cerrada-no-cambia-nada-rf-03` | `docs/requirements/criterios-aceptacion.md` | `b48c41e` | 0,7553 | 5,21 |
| `SRC-FUN#reglas` | `docs/requirements/funcionalidad.md` | `b48c41e` | 0,7568 | 5,20 |

`max_cosine` = 0,7792; `sufficient` = verdadero; `threshold` = 0,6869.

## Invocación con éxito: `get_test_result`

Argumentos: `{"test_id": "U-02"}`

```json
{"test_id": "U-02", "status": "passed",
 "cases": [{"name": "test_u02_closed_round_rejects_comment_and_stores_nothing", "status": "passed", "duration_s": 0.001}],
 "run_commit": "51c4e56bf30b24a83243a61c578a0709fe8c79a6", "run_date": "2026-11-27T14:12:37+00:00",
 "source": "stored", "current": true, "feature_commit": "cec82ef41d11fe2f21295da02bea1d1885b4d4ff"}
```

## Invocación con error: `get_test_result`

Argumentos: `{"test_id": "U-99"}`

Respuesta de error de MCP (`is_error`):

```
Error executing tool get_test_result: {"error": "not_found", "detail": "test U-99 is not in the stored run"}
```

El prefijo «Error executing tool …» lo agrega el SDK; el cuerpo JSON es el contrato del
servidor.
