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

## Verificación personal del estudiante (completar)

El enunciado exige que el estudiante pueda explicar todo lo entregado. Estos puntos
quedan para que el estudiante los complete con su propia revisión; no se dan por hechos.

- [ ] Ejecuté `uv sync` y `uv run pytest -v` en mi equipo y obtuve el mismo resultado.
- [ ] Leí y puedo explicar la inserción condicional atómica y por qué la comprobación del servicio no basta.
- [ ] Puedo explicar DEF-02: por qué el orden del reloj no coincide con el orden de confirmación.
- [ ] Revisé al menos una prueba y anoté qué defecto podría quedar sin detectar aunque apruebe.
