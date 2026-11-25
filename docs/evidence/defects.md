# Registro de defectos y limitaciones

Cada defecto conserva la evidencia previa y posterior a la corrección. «Corregido»
solo se afirma cuando la **misma** prueba se reejecutó y su salida está guardada.

## DEF-01 · Contrato de error 422 inconsistente · prioridad media · corregido

| Campo | Contenido |
|---|---|
| Condiciones de reproducción | Base sembrada (`seed_demo_data`). `POST /rounds/round-open/comments` con `"text": null` (rechazo del esquema de la petición) frente a `"text": "   "` (rechazo del dominio). |
| Esperado | Todo 422 con el mismo cuerpo `{"error": "invalid_comment", "detail": <texto>}`. |
| Observado | El rechazo del esquema devolvía `{"detail": [ ... ]}` de FastAPI, sin `error`; un cliente debía manejar dos formatos para el mismo código. |
| Causa probable | Solo los errores de dominio pasaban por el manejador propio; la validación de la petición usaba el manejador por defecto del framework. |
| Corrección | Manejador de `RequestValidationError` que responde con el mismo contrato (`src/review_comments/api/app.py`). Commit `6543bad`. |
| Detección | Sonda exploratoria del contrato HTTP ejecutada durante el desarrollo con Claude Code; se fijó como prueba **I-03**, escrita y ejecutada (fallida) antes de la corrección. |
| Reejecución | Antes: `def-01-before-fix.txt` (1 fallida, commit `44bf165`). Después: `def-01-after-fix.txt` (2 aprobadas, commit `6543bad`). |

## DEF-02 · El historial puede mostrar comentarios posteriores al cierre · prioridad alta · corregido

| Campo | Contenido |
|---|---|
| Condiciones de reproducción | Ronda abierta; un comentario se acepta con reloj T0+1 s mientras el cierre leyó su reloj en T0 (lectura del reloj antes de que SQLite serialice las escrituras). Determinista en **F-04**; bajo carga real en `scripts/concurrency_probe.py` (40 hilos, 20 corridas). |
| Esperado | Todo comentario aceptado tiene `created_at <= closed_at` de su ronda (coherente con RF-02). |
| Observado | `closed_at` = T0 < `created_at` = T0+1 s. En la sonda, 10 de 20 corridas tenían comentarios aceptados con marca posterior al cierre (hasta 0,37 s en una exploración de 30 corridas). El orden real de confirmación sí era correcto: ningún comentario se confirmó después del cierre (verificado con un trigger de la sonda). |
| Causa probable | Ambas marcas de tiempo provienen del reloj de la aplicación y se leen **antes** de la escritura; el orden del reloj no coincide con el orden de confirmación. |
| Corrección | El cierre fija `closed_at = max(reloj, max(created_at) de la ronda)` en la misma sentencia `UPDATE`; marcas de tiempo en formato UTC de ancho fijo para que la comparación de texto en SQL respete el orden temporal (`sqlite_repository.py`). Commit `ff48ec9`. |
| Reejecución | Antes: `def-02-before-fix.txt` (F-04 fallida, commit `057b222`), `concurrency-probe-2-before-def02-fix.txt` (10/20). Después: `def-02-after-fix.txt` (F-04 aprobada), `concurrency-probe-3-after-def02-fix.txt` (20/20), `mutation-check-3-after-def02.txt` (M8 la protege). |

## Defectos de las herramientas de verificación

Se registran porque afectaron la validez de la evidencia, no el producto.

- **TOOL-01 · Métrica engañosa en la sonda de concurrencia.** La primera versión
  comparaba solo marcas de tiempo y reportó «comentarios guardados después del
  cierre»; no podía distinguir orden de reloj de orden de confirmación. Se agregó
  un trigger exclusivo de la sonda que registra el mayor id al cerrar. La salida
  original se conserva en `concurrency-probe-1-timestamp-metric.txt`. Este hallazgo
  llevó a identificar DEF-02 con precisión.
- **TOOL-02 · Restauración no exacta en la verificación de mutaciones.** La primera
  ejecución de `scripts/mutation_check.py` restauraba los archivos con fines de
  línea CRLF (Windows). Se detectó con `git status`, se restauró con `git checkout`
  y se corrigió leyendo y escribiendo con `newline=""`.

## Limitaciones conocidas (no corregidas, dentro del alcance aceptado)

| ID | Limitación | Impacto | Prioridad | Acción propuesta |
|---|---|---|---|---|
| LIM-01 | Un `item_id` inexistente con una versión válida responde 422 («la versión no pertenece al ítem») en lugar de 404. | Mensaje menos preciso; no se guarda nada. | Baja | Consultar el ítem en el repositorio y responder 404. |
| LIM-02 | No se verifica que el ítem pertenezca a la ronda (no existe la relación ronda–ítem en este prototipo). | Un comentario podría anclarse a un ítem que no se compartió en esa ronda. | Media | Modelar ítems por ronda cuando se implementen los enlaces de revisión. |
| LIM-03 | Sin límite en la cantidad de puntos del trazo. | Peticiones muy grandes consumen memoria y CPU. | Baja | Límite de puntos en el contrato (422). |
| LIM-04 | SQLite serializa escrituras con un bloqueo de archivo; la garantía se demostró con 40 hilos en un solo proceso. | No se verificó con varias instancias de la aplicación ni con otro motor. | Media | Repetir I-02/F-02/F-04 y la sonda contra el motor de producción cuando se elija. |
| LIM-05 | El formato fijo de marcas de tiempo lo garantiza la aplicación, no una restricción del esquema. | Una escritura que eluda el repositorio con otro formato rompería la comparación de `max(created_at)`. | Baja | `CHECK` de formato en el esquema o columna numérica (epoch µs). |
