# Preguntas de calibración del umbral de suficiencia

Conjunto etiquetado para elegir el umbral τ con el que la búsqueda decide si hay evidencia
documental. «Con respaldo»: el corpus (SRC-FUN, SRC-CA, SRC-README, SRC-DEF, SRC-REV)
contiene la respuesta. «Sin respaldo»: no la contiene, aunque la pregunta use palabras del
dominio.

Las etiquetas y su justificación fueron redactadas por el asistente de IA. El estudiante
las revisó y las confirmó sin cambios el 2026-11-27. Q-14, Q-17 y Q-19 tratan temas que
la especificación declara fuera de alcance; se mantienen como «sin respaldo» porque ningún
documento describe cómo funcionarían.

| ID | Pregunta | Etiqueta | Justificación | Verificación del estudiante |
|---|---|---|---|---|
| Q-01 | ¿Qué pasa si se intenta comentar en una ronda cerrada? | con respaldo | RF-02 y CA-02: se rechaza y no se guarda nada | confirmada |
| Q-02 | ¿Cómo se calcula la caja delimitadora del trazo? | con respaldo | SRC-FUN, reglas: rectángulo mínimo recortado al ítem | confirmada |
| Q-03 | ¿Qué ocurre al cerrar una ronda que ya estaba cerrada? | con respaldo | RF-03 y CA-03 | confirmada |
| Q-04 | ¿Qué produce un trazo de un solo punto? | con respaldo | README, reglas adoptadas: caja de tamaño cero | confirmada |
| Q-05 | ¿Qué prueba verifica que el texto del revisor se guarda sin cambios? | con respaldo | Catálogo de pruebas: U-04 e I-04 | confirmada |
| Q-06 | ¿Cuál fue la causa del defecto DEF-02? | con respaldo | SRC-DEF, DEF-02 | confirmada |
| Q-07 | ¿Qué código de error se devuelve cuando la entrada es inválida? | con respaldo | README: 422 | confirmada |
| Q-08 | ¿Qué datos se guardan con cada comentario? | con respaldo | SRC-FUN, datos del comentario | confirmada |
| Q-09 | ¿Quién revisó las pruebas y qué limitación tiene esa revisión? | con respaldo | SRC-REV | confirmada |
| Q-10 | ¿Qué pruebas verifican el criterio de aceptación CA-02? | con respaldo | SRC-CA, CA-02 | confirmada |
| Q-11 | ¿Qué sucede si la ronda se cierra entre la comprobación y la escritura? | con respaldo | CA-02 y F-02 | confirmada |
| Q-12 | ¿Qué queda fuera del alcance de la funcionalidad? | con respaldo | SRC-FUN, fuera de alcance | confirmada |
| Q-13 | ¿Cuál es el tiempo máximo de respuesta exigido para registrar un comentario? | sin respaldo | Ningún documento fija requisitos de rendimiento | confirmada |
| Q-14 | ¿Cómo se autentica a un revisor con usuario y contraseña? | sin respaldo | No hay autenticación; las cuentas están fuera de alcance, pero no se describe ningún mecanismo | confirmada |
| Q-15 | ¿Cuántos comentarios por segundo soporta el sistema en producción? | sin respaldo | No hay mediciones de carga | confirmada |
| Q-16 | ¿Qué servidor de nube aloja la aplicación? | sin respaldo | No se describe despliegue | confirmada |
| Q-17 | ¿Cómo se envían notificaciones por correo al diseñador? | sin respaldo | Notificaciones fuera de alcance; ningún mecanismo descrito | confirmada |
| Q-18 | ¿Qué precio tiene la suscripción mensual? | sin respaldo | No hay información comercial | confirmada |
| Q-19 | ¿En qué idiomas se traduce automáticamente la interfaz? | sin respaldo | No hay interfaz ni traducción | confirmada |
| Q-20 | ¿Qué base de datos guarda el registro de auditoría de pagos? | sin respaldo | No existen pagos ni auditoría | confirmada |
