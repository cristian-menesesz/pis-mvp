# Criterios de aceptación: comentario anclado a una región

Un criterio por requisito funcional (RF). Cada uno indica qué pruebas lo verifican; el
catálogo de pruebas está en el README.

## CA-01 · Registrar y recuperar un comentario anclado (RF-01)

- **Dado** una ronda abierta y la versión 1 del ítem «póster», de 1200 × 800 píxeles,
- **cuando** un revisor envía un trazo con los puntos (100, 50), (300, 200) y (150, 120),
  el texto «Mover el logo» y su nombre,
- **entonces** se guarda un comentario con la caja x = 100, y = 50, ancho = 200,
  alto = 150, asociado a esa ronda, ítem y versión, con el texto y el nombre tal como se
  escribieron, y el comentario se puede recuperar por su identificador.
- Si el trazo sale de la imagen, la caja se recorta a sus bordes; un trazo de un solo
  punto produce una caja de tamaño cero; un trazo vacío, totalmente fuera de la imagen,
  con coordenadas no finitas, o un texto o nombre en blanco se rechazan (422) y no se
  guarda nada.
- Verificado por: U-01, U-03a a U-03d, U-04, I-01, I-03, I-04, I-05.

## CA-02 · Rechazar comentarios en una ronda cerrada (RF-02)

- **Dado** una ronda cerrada,
- **cuando** un revisor envía un comentario, aunque sea válido,
- **entonces** se rechaza con 409, no se guarda nada y los comentarios existentes de la
  ronda no cambian.
- Si la ronda se cierra entre la comprobación del servicio y la escritura, tampoco se
  guarda nada.
- Ningún comentario aceptado tiene una hora de creación posterior a la hora de cierre de
  su ronda.
- Verificado por: U-02, U-02b, U-05, I-02, F-02, F-04, C-01, C-04.

## CA-03 · Cerrar una ronda ya cerrada no cambia nada (RF-03)

- **Dado** una ronda cerrada con su hora de cierre,
- **cuando** se pide cerrarla otra vez,
- **entonces** la operación responde con éxito, la hora de cierre original se conserva y
  ningún comentario cambia.
- Verificado por: U-06, F-01, C-03.
