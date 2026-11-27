# Consultas RAG

Fecha (UTC): 2026-11-27T14:59:35+00:00. Commit: `66a21eb125b6b9dc0316656a4c7fc827b83377a8`. Recuperación: herramienta MCP `search_requirements` (híbrida BM25 + `nomic-embed-text`, τ = 0.6869). Respuesta: `qwen3.5:4b`, temperatura 0, solo con los fragmentos recuperados. Fragmentos completos y puntajes en `rag-queries.json`.

La verificación humana la redactó el asistente de IA con su razonamiento; el estudiante la revisó y la confirmó sin cambios el 2026-11-27.

## RAG-1

| Campo | Registro |
|---|---|
| Consulta | ¿Qué ocurre si un revisor intenta comentar en una ronda cerrada y qué pruebas lo verifican? |
| Fuentes recuperadas | `SRC-CA#ca-02-rechazar-comentarios-en-una-ronda-cerrada-rf-02` (coseno 0.721)<br>`SRC-README#requisitos` (coseno 0.695)<br>`SRC-REV#observaciones-y-tratamiento/1` (coseno 0.715)<br>`SRC-FUN#reglas` (coseno 0.695) |
| Suficiencia | coseno máximo 0.7403; suficiente |
| Respuesta del sistema | Si un revisor intenta comentar en una ronda cerrada, el sistema rechaza la acción con el código de estado 409 sin guardar ningún dato ni modificar los comentarios existentes [SRC-FUN#reglas]. Esta verificación se confirma mediante las pruebas U-02, U-02b, U-05 e I-02 que validan el rechazo inmediato antes de cualquier problema de entrada [SRC-CA#ca-02-rechazar-comentarios-en-una-ronda-cerrada-rf-02]. Además, se garantiza mediante la prueba F-04 y C-01 que ningún comentario aceptado tendrá una hora de creación posterior a la del cierre de su ronda [SRC-FUN#reglas]. |
| Citas inválidas (no recuperadas) | ninguna |
| Verificación humana | Confirmada por el estudiante (2026-11-27); detalle abajo |

**Verificación (redactada por el asistente de IA, confirmada por el estudiante).** Respaldo parcial.
- «Se rechaza con 409, sin guardar datos ni modificar comentarios existentes»: el contenido es correcto, pero la cita es imprecisa. `SRC-FUN#reglas` respalda «se rechaza y no se guarda nada»; el 409 y «los comentarios existentes no cambian» están en `SRC-CA#ca-02`, que fue recuperado pero no se cita ahí.
- «U-02, U-02b, U-05 e I-02 lo verifican»: respaldado por `SRC-CA#ca-02`, que además lista F-02, F-04, C-01 y C-04. La frase «rechazo inmediato antes de cualquier problema de entrada» describe solo U-02b.
- «F-04 y C-01 garantizan que ninguna hora es posterior al cierre»: la regla está en `SRC-CA#ca-02`, no en `SRC-FUN#reglas`. Según el catálogo, la coherencia de horas la verifican F-04 y C-04; C-01 verifica que no se guarde nada en una ronda cerrada. Es una mezcla incorrecta, no detectable por el validador de citas (LIM-A02).
- Ninguna afirmación inventada fuera del corpus.

## RAG-2

| Campo | Registro |
|---|---|
| Consulta | ¿Cómo se calcula la caja del comentario cuando el trazo sale de la imagen? |
| Fuentes recuperadas | `SRC-CA#ca-01-registrar-y-recuperar-un-comentario-anclado-rf-01` (coseno 0.717)<br>`SRC-FUN#alcance` (coseno 0.721)<br>`SRC-FUN#reglas` (coseno 0.708)<br>`SRC-README#inicio` (coseno 0.679) |
| Suficiencia | coseno máximo 0.7209; suficiente |
| Respuesta del sistema | La caja delimitadora se calcula como el rectángulo mínimo que contiene los puntos del trazo [SRC-FUN#reglas]. Cuando este cálculo resulta fuera de las dimensiones del ítem, la caja se recorta a sus bordes correspondientes [SRC-CA#ca-01-registrar-y-recuperar-un-comentario-anclado-rf-01]. Si el trazo sale completamente de la imagen o tiene coordenadas no finitas, se rechaza y no se guarda nada [SRC-FUN#reglas]. |
| Citas inválidas (no recuperadas) | ninguna |
| Verificación humana | Confirmada por el estudiante (2026-11-27); detalle abajo |

**Verificación (redactada por el asistente de IA, confirmada por el estudiante).** Respaldo casi total.
- «Rectángulo mínimo que contiene los puntos»: respaldado por `SRC-FUN#reglas`.
- «Fuera de las dimensiones se recorta a sus bordes»: respaldado por `SRC-CA#ca-01`.
- «Totalmente fuera o con coordenadas no finitas se rechaza y no se guarda nada»: correcto, pero el respaldo está en `SRC-CA#ca-01`, no en `SRC-FUN#reglas` (cita imprecisa).

## RAG-3

| Campo | Registro |
|---|---|
| Consulta | ¿Cuál es el tiempo máximo de respuesta exigido para registrar un comentario? |
| Fuentes recuperadas | `SRC-FUN#inicio` (coseno 0.712)<br>`SRC-FUN#datos-del-comentario` (coseno 0.717)<br>`SRC-FUN#alcance` (coseno 0.727)<br>`SRC-FUN#reglas` (coseno 0.719) |
| Suficiencia | coseno máximo 0.7275; suficiente |
| Respuesta del sistema | Los fragmentos proporcionados describen los datos necesarios (texto, revisión de puntos) y las reglas para registrar un comentario anclado a una región [SRC-FUN#datos-del-comentario], pero no especifican ningún tiempo máximo exigido para esta acción. La única restricción temporal mencionada es que el sistema solo acepta comentarios si la ronda está abierta en ese momento [SRC-FUN#reglas]. Por lo tanto, no se puede determinar un límite de tiempo específico desde los datos disponibles. |
| Citas inválidas (no recuperadas) | ninguna |
| Verificación humana | Confirmada por el estudiante (2026-11-27); detalle abajo |

**Verificación (redactada por el asistente de IA, confirmada por el estudiante).** Límite reconocido.
- El corpus no define tiempos de respuesta; la respuesta lo dice explícitamente y no inventa un valor.
- La búsqueda marcó «suficiente» (coseno 0,7275 > τ) aunque no hay respaldo: es el caso LIM-A01 (preguntas con vocabulario del dominio). El límite lo reconoció el modelo, no el umbral.
- La afirmación sobre «la única restricción temporal» es una interpretación: la ronda abierta no es un requisito de tiempo de respuesta.
