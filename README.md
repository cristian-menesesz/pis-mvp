# Comentarios anclados a una región

Prototipo de una funcionalidad del MVP *Visual Review Tool for Freelancers*: el
revisor traza sobre un ítem (imagen), el sistema calcula la caja delimitadora del
trazo, la recorta al ítem y guarda el comentario con su ronda, ítem y versión. El
revisor puede cerrar la ronda.

El repositorio contiene la funcionalidad y su verificación: pruebas unitarias, de
integración y de fallo, más los registros de evidencia en `docs/evidence/`.

## Requisitos

| ID | Requisito |
|---|---|
| RF-01 | Registrar un comentario anclado: caja = rectángulo mínimo que contiene los puntos del trazo, recortado a las dimensiones de la versión del ítem; se guarda con ronda, ítem, versión, caja, texto y nombre del revisor; se puede recuperar. |
| RF-02 | Solo se aceptan comentarios en una ronda abierta; en una ronda cerrada se rechaza y no se guarda nada. |
| RF-03 | Cerrar una ronda ya cerrada no cambia nada. |

Reglas decididas para el prototipo (la especificación las dejaba abiertas):

- Un trazo de un solo punto (o de puntos idénticos) produce una caja de tamaño cero.
- Se rechazan (422): trazo vacío, coordenadas no finitas, trazo totalmente fuera del
  ítem, texto o nombre en blanco, versión que no pertenece al ítem.
- El texto del revisor se guarda tal como lo escribió (nunca se reescribe).
- Si la ronda está cerrada, se informa eso (409) antes que cualquier problema de la entrada.
- Ningún comentario aceptado tiene `created_at` posterior al `closed_at` de su ronda.

## Componentes y dónde se cumple cada regla

```
api/app.py  ──►  application/service.py  ──►  application/ports.py (CommentRepository)
 contrato HTTP     casos de uso y reglas            ▲
 404/409/422                                        │ implementa
                                         infrastructure/sqlite_repository.py ──► SQLite
domain/geometry.py: caja delimitadora y recorte     (inserción condicional atómica,
domain/models.py, domain/errors.py                   restricciones del esquema)
```

| Componente | Responsabilidad | Depende de |
|---|---|---|
| `domain/geometry.py` | Caja mínima del trazo y recorte al ítem (RF-01). | Nada. |
| `application/service.py` | Orquesta el registro: existencia, ronda abierta, pertenencia de la versión, campos obligatorios, geometría (RF-01, RF-02, RF-03). | Puerto `CommentRepository`, reloj inyectado. |
| `infrastructure/sqlite_repository.py` | Persistencia. **Garantiza RF-02 de forma atómica**: `INSERT … SELECT … WHERE` la ronda sigue abierta, en una sola sentencia; el cierre es condicional e idempotente (RF-03). | SQLite, esquema en `schema.py`. |
| `api/app.py` | Contrato HTTP; traduce errores de dominio a 404/409/422 con un solo formato de cuerpo. | Servicio. |

La regla de ronda abierta se verifica dos veces: el servicio la comprueba para dar un
error claro y el repositorio la impone atómicamente, porque entre la comprobación y la
escritura otra petición puede cerrar la ronda.

## Reproducir

Requisito: [uv](https://docs.astral.sh/uv/) (instala Python 3.13 y las dependencias
fijadas en `uv.lock`).

```powershell
uv sync
uv run pytest -v
```

| Objetivo | Comando |
|---|---|
| Pruebas con cobertura | `uv run pytest -v --cov --cov-report=term-missing` |
| Solo un nivel | `uv run pytest -m unit` · `-m integration` · `-m failure` |
| ¿Las pruebas fallan si se rompe la regla? | `uv run python scripts/mutation_check.py` |
| Concurrencia real (hilos, corridas) | `uv run python scripts/concurrency_probe.py 40 20` |
| Base de demostración | `uv run python scripts/seed.py review.db` |
| Levantar la API | `$env:REVIEW_DB_PATH="review.db"; uv run uvicorn review_comments.api.app:create_app --factory` |

**Datos controlados.** Cada prueba de integración y de fallo crea su propia base SQLite
en un directorio temporal de pytest, la siembra con `seed_demo_data` (datos ficticios:
una ronda abierta, una cerrada con un comentario previo, dos ítems con su versión) y
pytest la elimina al terminar. No hay estado compartido entre pruebas ni datos reales.
La API usa `http://127.0.0.1:8000/docs` para explorar el contrato.

## Pruebas

| ID | Nivel | Qué comprueba | Requisito |
|---|---|---|---|
| U-01 | Unitaria | Trazo válido → caja mínima correcta y comentario guardado | RF-01 |
| U-02 | Unitaria | Ronda cerrada → rechazo, nada guardado, ronda intacta | RF-02 |
| U-02b | Unitaria | Ronda cerrada se informa antes que errores de entrada | RF-02 |
| U-03a–d | Unitaria | Fronteras: un punto, recorte en bordes, borde exacto, entradas inválidas | RF-01 |
| U-04 | Unitaria | El texto se guarda sin reescribir | RF-01 |
| U-05 | Unitaria | Escritura rechazada por cierre concurrente → `RoundClosedError`, nunca éxito ficticio | RF-02 |
| U-06, U-07 | Unitaria | Cierre repetido conserva el primer `closed_at`; entidades inexistentes → no encontrado | RF-03 |
| I-01 | Integración | API → servicio → SQLite: comentario persistido y recuperable con otra conexión | RF-01 |
| I-02 | Integración | Ronda cerrada con datos previos: 409 y datos existentes idénticos | RF-02 |
| I-03 | Integración | Todo 422 usa el mismo contrato de error (DEF-01) | RF-01 |
| F-01 | Fallo | Cierre repetido por la API no cambia la ronda ni los comentarios | RF-03 |
| F-02 | Fallo | La ronda se cierra entre la comprobación y la escritura: no se guarda nada | RF-02 |
| F-03 | Fallo | El esquema rechaza filas inválidas escritas sin pasar por el servicio | RF-01 |
| F-04 | Fallo | `closed_at` nunca es anterior a un comentario aceptado (DEF-02) | RF-02 |

**Si cambia una regla, revisar:** geometría o recorte → U-01, U-03a–c, I-01;
campos obligatorios → U-03d, I-03, F-03; ronda abierta → U-02, U-02b, U-05, I-02,
F-02, F-04; cierre → U-06, F-01, F-04. Después, `scripts/mutation_check.py` indica si
alguna regla quedó sin prueba que la proteja.

## Evidencia (`docs/evidence/`)

| Archivo | Contenido |
|---|---|
| `test-run.txt` | Ejecución completa con cobertura, commit y fecha. |
| `defects.md` | Defectos (DEF-01, DEF-02), defectos de herramientas y limitaciones. |
| `def-0X-before-fix.txt` / `def-0X-after-fix.txt` | Misma prueba antes y después de cada corrección. |
| `mutation-check-*.txt` | Mutaciones detectadas por las pruebas, en orden cronológico. |
| `concurrency-probe-*.txt` | Sonda de concurrencia, en orden cronológico. |
| `peer-review.md` | Revisión independiente de las pruebas y su tratamiento. |
| `ai-usage.md` | Registro del uso de IA en el desarrollo. |
