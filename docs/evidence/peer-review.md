# Revisión de las pruebas

## Quién revisó y por qué así

El trabajo se realizó de forma individual, así que no hubo un compañero distinto al
autor. Como sustituto declarado, la revisión la hizo un **agente revisor de IA
independiente** (Claude Code, agente `feature-dev:code-reviewer`):

- No tenía el contexto de cómo se construyó el código; recibió solo la ruta del
  repositorio, los requisitos RF-01..RF-03 y la instrucción de revisar **las pruebas**
  en cuanto a aserciones, aislamiento, datos, fidelidad del doble de prueba y
  posibles falsos positivos, sin modificar archivos.
- Revisó el commit `9cfad38` (pruebas idénticas a las de `ff48ec9`).

**Limitación:** no es la revisión de una persona del equipo. Un revisor humano aporta
conocimiento del dominio y transferencia de conocimiento (Bacchelli y Bird, 2013) que
este sustituto no reemplaza. Cada observación se verificó contra el código y con
mutaciones antes de aplicarla; no se aceptó ninguna sin comprobación.

## Observaciones y tratamiento

| # | Observación del revisor | ¿Se aplicó? | Por qué / cómo se comprobó |
|---|---|---|---|
| 1 | «El texto se guarda tal cual» solo se probaba sobre el doble en memoria; un `.strip()` en el repositorio o en el modelo HTTP pasaría inadvertido. El nombre del revisor nunca se probaba. | Sí | Nueva **I-04**: texto y nombre con espacios y salto de línea, verificados en la respuesta, en `GET` y en la fila de SQLite. La mutación **M10** (strip al insertar) sobrevivía a la suite anterior y ahora la detecta I-04. |
| 2 | La mayoría de rechazos y los 404 nunca atravesaban API → SQLite; un mapeo incorrecto de error a código HTTP no se detectaría. | Sí | Nuevas **I-05** (6 casos: trazo vacío, fuera del ítem, versión ajena, nombre en blanco, ronda y versión inexistentes) e **I-06** (comentario y ronda inexistentes). Cubren las líneas 404 que la cobertura marcaba sin ejecutar. |
| 3 | «Totalmente fuera del ítem» solo se probaba por la derecha; los bordes solo por la derecha; ninguna coordenada fraccionaria. | Sí | **U-03c** parametrizada en los 4 bordes + caso fraccionario; **U-03d** con los 4 lados a 0,01 px del borde. La mutación **M9** (quitar la comprobación del lado izquierdo) sobrevivía antes y ahora muere. |
| 4 | El doble en memoria no respeta el contrato: ignora la regla de DEF-02, no aplica integridad referencial, no hace ida y vuelta de `created_at`. U-05 es redundante con F-02. | Parcialmente | Se añadió la regla de DEF-02 al doble y una suite de **contrato** (`tests/contract`, C-01..C-05) que ejecuta las mismas comprobaciones contra el doble y contra SQLite. **No** se replicó la integridad referencial en el doble: es responsabilidad exclusiva del almacenamiento y se verifica en F-03. **Se mantuvo U-05**: aísla la decisión del servicio (convertir `None` en `RoundClosedError`, nunca un éxito ficticio), mientras F-02 verifica la carrera completa; fallan por motivos distintos. |
| 5 | Aserciones débiles o que leen internals: `repo.comments == [comment]` es casi tautológica; I-01 no verificaba que las filas previas quedaran intactas; F-01/F-04 usaban `_db_path` privado; F-03 aceptaba cualquier `IntegrityError`; el cierre repetido nunca se probaba con comentarios. | Sí | U-01 comprueba un único registro recuperable por id; I-01 añade `after[:-1] == before`; F-01/F-04 usan el fixture `db_path`; F-03 exige el mensaje de la restricción concreta (FK compuesta, CHECK); C-03 prueba el cierre repetido sobre una ronda con comentarios. |

## Evidencia

- Revisión aplicada en el commit «Apply independent review: contract tests and stronger assertions».
- `mutation-check-4-pre-review-suite.txt`: suite **anterior** a la revisión frente a las
  mutaciones M9–M11 derivadas de ella → 9/11 detectadas (M9 y M10 sobreviven).
- `mutation-check-5-after-review.txt`: suite **posterior** → 11/11 detectadas.
- `test-run.txt`: 51 pruebas aprobadas, cobertura de ramas 98 %.
