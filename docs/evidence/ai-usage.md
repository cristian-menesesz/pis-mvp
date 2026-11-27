# Registro de uso y verificación de IA

**Estudiante:** Cristian Meneses (trabajo individual).
**Asistente:** Claude Code (modelo Claude Opus 5.5, Anthropic), en modo agéntico:
lee archivos, ejecuta comandos y edita el repositorio bajo la dirección del estudiante.
**Fecha:** 2026-11-24.

## Cómo se trabajó

El desarrollo fue **dirigido por el estudiante y ejecutado con programación agéntica**.
El estudiante definió el problema (blueprint del producto), eligió la funcionalidad y
su especificación (`funcionalidad.md`), aportó el enunciado de la práctica y la guía de
conceptos del curso, y tomó las decisiones que la especificación dejaba abiertas. Claude
Code propuso el diseño, escribió el código y las pruebas, las ejecutó y registró la
evidencia; cada propuesta de diseño se presentó al estudiante y se aprobó antes de
implementarla.

Ningún resultado de este repositorio es una sugerencia sin ejecutar: cada estado
«aprobado» o «fallido» proviene de una ejecución real cuya salida está en
`docs/evidence/`, con el commit correspondiente.

## Decisiones tomadas por el estudiante

| Decisión | Opciones planteadas | Elección |
|---|---|---|
| Lenguaje y pruebas | Python/pytest, TypeScript/Vitest, Java/JUnit | Python 3.13 + pytest |
| Persistencia | SQLite, PostgreSQL en Docker | SQLite (reproducible sin instalar servicios) |
| Trazo de un solo punto (regla sin definir) | Rechazar, caja mínima fija, caja de tamaño cero | Caja de tamaño cero |
| Capa HTTP | API delgada, solo biblioteca | API delgada (contrato 404/409/422) |
| Idioma | — | Código y commits en inglés; documentación en español |
| Punto de partida | Suponer funcionalidad previa, partir de cero | Partir de cero: construir la funcionalidad y verificarla |
| Revisión por pares (trabajo individual) | Revisor de IA independiente, compañero, ambos | Revisor de IA independiente, declarado como limitación |
| Aprobación del diseño | — | Aprobado antes de escribir código |

## Registro de usos relevantes

| # | Objetivo | Instrucción o consulta | Aporte de la IA | Qué se modificó, rechazó o adaptó | Cómo se validó | Evidencia |
|---|---|---|---|---|---|---|
| 1 | Aclarar alcance antes de construir | «Haz las preguntas que necesites antes de empezar» | Preguntas sobre stack, persistencia, regla de un punto, entregables, línea base y revisión por pares; detectó que el enunciado supone una funcionalidad ya existente | El estudiante respondió cada punto (tabla anterior) | Decisiones explícitas antes de diseñar | Esta tabla |
| 2 | Diseño | Propuesta de diseño con alternativas | Tres alternativas para imponer RF-02 (comprobar y luego insertar; inserción condicional atómica; solo trigger) con recomendación de la segunda | Aprobada por el estudiante | Pruebas F-02, I-02 y mutación M1 | `sqlite_repository.py`, `mutation-check-*.txt` |
| 3 | Implementación | Construir dominio, servicio, repositorio y API | Código de `src/review_comments` | Ajustes tras ejecutar: formato de error 422 (DEF-01), regla de cierre (DEF-02) | 51 pruebas, cobertura 98 % | `test-run.txt` |
| 4 | Pruebas | Pruebas unitarias, de integración y de fallo | U-, I-, F- y C- | Se reforzaron tras la revisión independiente (ver `peer-review.md`) | Ejecución y mutaciones | `tests/`, `test-run.txt` |
| 5 | Comprobar que las pruebas fallan si la regla se rompe | Verificación por mutaciones | `scripts/mutation_check.py` | M2 sobrevivió en la primera ejecución → se añadió U-02b. La restauración de archivos alteraba fines de línea → se corrigió (TOOL-02) | 11/11 mutaciones detectadas | `mutation-check-1..5` |
| 6 | Concurrencia real | Sonda con hilos concurrentes | `scripts/concurrency_probe.py` | La primera métrica (marcas de tiempo) era engañosa (TOOL-01); se reemplazó por un trigger que registra el orden de confirmación. Al separarlas apareció DEF-02 | 20/20 corridas tras la corrección | `concurrency-probe-1..3` |
| 7 | Revisión independiente | Agente revisor sin contexto de construcción | 5 observaciones sobre las pruebas | 4 aplicadas, 1 parcialmente (justificado) | Mutaciones M9–M11: 9/11 antes, 11/11 después | `peer-review.md` |
| 8 | Dependencias | Advertencia de obsolescencia de `httpx` en el cliente de pruebas | La IA intentó instalar `httpx2`, el reemplazo que sugería el mensaje | **Rechazado** por el control de seguridad del entorno (paquete sugerido solo por un mensaje de advertencia); se mantuvo `httpx` y se filtró esa advertencia | Suite en verde sin la dependencia nueva | `pyproject.toml` |
| 9 | Informe técnico | Redactar el complemento técnico y la entrega individual en LaTeX, en primera persona, a partir de la evidencia del repositorio | Borrador completo del informe (compilado con MiKTeX) | El estudiante revisa y ajusta el texto antes de entregarlo | Cada cifra del informe se tomó de las salidas guardadas en `docs/evidence/` | Informe (fuera del repositorio) |

## Asistente evidence-anchor (2026-11-27)

En este trabajo intervienen **dos IA con papeles distintos**. Claude Code (Claude Opus
5.5) diseñó, programó y verificó el asistente bajo la dirección del estudiante.
`qwen3.5:4b`, ejecutado con Ollama, es el modelo **dentro** del asistente: es parte del
sistema bajo prueba. Sus salidas nunca se tomaron como hallazgos ni como instrucciones;
se registran y se evalúan con criterios calculados por código.

### Decisiones tomadas por el estudiante

| Decisión | Opciones planteadas | Elección |
|---|---|---|
| Modelo del agente | Ollama local, API de Claude, ambos | Ollama local (presupuesto cero) |
| Recuperación | Solo léxica, híbrida en SQLite, base vectorial dedicada | Híbrida en SQLite, fragmentación por estructura |
| Documento completo en el contexto | Comparar como modo alternativo | Descartado: se hace RAG |
| Repositorio | Mismo repositorio, uno nuevo | Mismo repositorio, paquete aparte |
| Aprobación humana de `run_test` | Puerta de aprobación, sin aprobación | Sin aprobación: pruebas controladas y ninguna herramienta escribe |
| Verificaciones humanas | Redacta el asistente y confirma el estudiante, solo el estudiante | Redacta el asistente, confirma el estudiante |
| Nombre | Título de la práctica, otro | `evidence-anchor` |

### Registro de usos relevantes

| # | Objetivo | Instrucción o consulta | Aporte de la IA | Qué se modificó, rechazó o adaptó | Cómo se validó | Evidencia |
|---|---|---|---|---|---|---|
| 10 | Diseño | «Antes de hacer nada, discute qué vas a hacer» | Alternativas de recuperación y de fragmentación, diseño escrito y revisado por un agente sin contexto | El estudiante descartó el modo de documento completo y la aprobación humana; cinco preguntas del revisor resueltas | Diseño aprobado antes de programar | `docs/design/evidence-anchor.md` |
| 11 | Elección del modelo | Comprobar llamadas a herramientas en local | Script de prueba con `qwen3.5:4b` y `llama3.2` | Se mantuvo `qwen3.5:4b` (3/3 llamadas válidas) | Ejecución real | `assistant/model-smoke.txt` |
| 12 | RAG | Índice híbrido persistente y umbral de evidencia | Fragmentación, índice, búsqueda, calibración | El umbral no separa del todo las preguntas: se declaró como LIM-A01 en lugar de ajustarlo a mano | 20 preguntas etiquetadas (etiquetas confirmadas por el estudiante) | `assistant/calibration*.{md,txt}` |
| 13 | MCP | Servidor real con herramientas de verificación | Servidor con el SDK oficial 2.3 y tres herramientas | El SDK antepone texto a los errores; el cliente extrae el JSON | 7 pruebas con el cliente real del SDK | `tests/assistant/test_mcp_server.py` |
| 14 | Agente | Decisiones del modelo, controles en código | Bucle, lista blanca, validador, trazas | La primera ejecución real agotó los pasos (DEF-A01); se corrigió el bucle, no la salida del modelo | Prueba roja y luego verde; traza antes y después | `assistant/defects.md`, `assistant/def-a01-*.jsonl` |
| 15 | Escenarios | T-01 a T-04 contra el modelo real | Script con criterios calculados por código y 3 semillas | Los resultados se registran tal como salen; no se ajustó el prompt para aprobarlos | Ejecución real de 18 corridas | `assistant/scenarios.md`, `assistant/scenarios/` |
| 16 | Error propio | — | Claude Code editó el README (fuente del RAG) mientras corrían los escenarios | Se restauró en menos de dos minutos; la documentación del asistente pasó a `docs/assistant/README.md` | La primera corrida afectada recuperó solo fragmentos de la funcionalidad | Traza `T-01-seed1.jsonl` |
| 17 | Revisión independiente | Agente revisor (Claude Opus) sin contexto de construcción, sobre todo el código del asistente | 3 observaciones importantes y 11 menores | Se corrigieron las 3 importantes y 3 menores reclasificadas por su efecto (fallo oculto, límite de tiempo, commit por fila); 8 menores quedaron como límites (LIM-A05 a LIM-A12) | Cada corrección con una prueba roja y luego verde; 133 pruebas; escenarios repetidos | `assistant/defects.md`, `assistant/scenarios-run2/` |
| 18 | Validez de T-04 | Revisión de las trazas de T-04 | Claude Code detectó que la instrucción maliciosa nunca llegaba al modelo | Se agregó la precondición de entrega y se corrigió el documento de prueba (TOOL-A01); se informan todas las corridas, también las no válidas | Precondición calculada por código sobre la traza | `assistant/scenarios-t04-*` |

## Verificación personal del estudiante (completar)

El enunciado exige que el estudiante pueda explicar todo lo entregado. Estos puntos
quedan para que el estudiante los complete con su propia revisión; no se dan por hechos.

- [ ] Ejecuté `uv sync` y `uv run pytest -v` en mi equipo y obtuve el mismo resultado.
- [ ] Leí y puedo explicar la inserción condicional atómica y por qué la comprobación del servicio no basta.
- [ ] Puedo explicar DEF-02: por qué el orden del reloj no coincide con el orden de confirmación.
- [ ] Revisé al menos una prueba y anoté qué defecto podría quedar sin detectar aunque apruebe.
