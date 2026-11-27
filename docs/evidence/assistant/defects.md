# Defectos y limitaciones del asistente evidence-anchor

Separado del registro de la funcionalidad (`docs/evidence/defects.md`), que forma parte
del corpus del RAG: los defectos del asistente no son requisitos del producto.

## DEF-A01 · El agente agota sus pasos antes de entregar el informe · prioridad alta · corregido

| Campo | Contenido |
|---|---|
| Condiciones de reproducción | Pregunta «¿Qué evidencia muestra que no se guarda un comentario en una ronda cerrada?», `qwen3.5:4b`, temperatura 0, semilla 42, límite de 8 pasos. |
| Esperado | Un informe entregado con `submit_report` dentro del límite de pasos. |
| Observado | El modelo consultó una prueba por turno (U-02, U-02b, I-02, F-02, C-01, U-05) y llegó al paso 8 sin informe; el código lo detuvo con «no concluyente». No inventó nada, pero no concluyó. |
| Causa probable | El prompt no indicaba que los pasos son limitados ni que bastan pocas pruebas representativas; nada avisaba al modelo de que se acercaba al límite. |
| Corrección | El bucle avisa al modelo cuando quedan 2 pasos (prueba `test_model_is_warned_when_two_steps_remain`, roja y luego verde) y el prompt indica que puede pedir varias pruebas por turno y que bastan dos o tres vigentes. El límite sigue en 8 pasos. |
| Reejecución | Antes: `def-a01-before-fix.jsonl` (8 pasos, sin informe). Después: `def-a01-after-fix.jsonl` (5 pasos, conclusión «sustentada» validada, citas SRC-CA, SRC-FUN, SRC-README; pruebas U-02, I-02, F-02 vigentes). |

## Limitaciones conocidas

| ID | Limitación | Impacto | Acción propuesta |
|---|---|---|---|
| LIM-A01 | El umbral de suficiencia (τ = 0,6869) no separa del todo las preguntas sin respaldo que usan el vocabulario del dominio: 3 de 20 preguntas de calibración mal clasificadas (`calibration.txt`). | En esas preguntas, decidir que no hay respaldo depende del juicio del modelo (T-02 lo prueba). | Reranker o verificación de respaldo por afirmación; ampliar el conjunto de calibración. |
| LIM-A02 | El validador comprueba el origen de cada cita, no si el fragmento respalda la afirmación. | Una cita recuperada pero irrelevante no se detecta automáticamente. | Verificación humana registrada (`rag-queries.md`); a futuro, una comprobación automática por afirmación. |
| LIM-A03 | Modelo local de 4,7 B parámetros en una GPU de 4 GB: cada llamada tarda segundos y la calidad de las decisiones es menor que la de un modelo grande. | Ejecuciones lentas y variables entre semillas; se mide en los escenarios. | Probar con un modelo mayor cuando haya hardware o presupuesto. |
