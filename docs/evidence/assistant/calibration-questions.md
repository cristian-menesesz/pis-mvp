# Preguntas de calibración del umbral de suficiencia

Conjunto etiquetado para elegir el umbral τ con el que la búsqueda decide si hay evidencia
documental. «Con respaldo»: el corpus (SRC-FUN, SRC-CA, SRC-README, SRC-DEF, SRC-REV)
contiene la respuesta. «Sin respaldo»: no la contiene, aunque la pregunta use palabras del
dominio.

Las etiquetas y su justificación fueron redactadas por el asistente de IA. La columna
«Verificación del estudiante» queda pendiente hasta que el estudiante las revise.

| ID | Pregunta | Etiqueta | Justificación | Verificación del estudiante |
|---|---|---|---|---|
| Q-01 | ¿Qué pasa si se intenta comentar en una ronda cerrada? | con respaldo | RF-02 y CA-02: se rechaza y no se guarda nada | pendiente |
| Q-02 | ¿Cómo se calcula la caja delimitadora del trazo? | con respaldo | SRC-FUN, reglas: rectángulo mínimo recortado al ítem | pendiente |
| Q-03 | ¿Qué ocurre al cerrar una ronda que ya estaba cerrada? | con respaldo | RF-03 y CA-03 | pendiente |
| Q-04 | ¿Qué produce un trazo de un solo punto? | con respaldo | README, reglas adoptadas: caja de tamaño cero | pendiente |
| Q-05 | ¿Qué prueba verifica que el texto del revisor se guarda sin cambios? | con respaldo | Catálogo de pruebas: U-04 e I-04 | pendiente |
| Q-06 | ¿Cuál fue la causa del defecto DEF-02? | con respaldo | SRC-DEF, DEF-02 | pendiente |
| Q-07 | ¿Qué código de error se devuelve cuando la entrada es inválida? | con respaldo | README: 422 | pendiente |
| Q-08 | ¿Qué datos se guardan con cada comentario? | con respaldo | SRC-FUN, datos del comentario | pendiente |
| Q-09 | ¿Quién revisó las pruebas y qué limitación tiene esa revisión? | con respaldo | SRC-REV | pendiente |
| Q-10 | ¿Qué pruebas verifican el criterio de aceptación CA-02? | con respaldo | SRC-CA, CA-02 | pendiente |
| Q-11 | ¿Qué sucede si la ronda se cierra entre la comprobación y la escritura? | con respaldo | CA-02 y F-02 | pendiente |
| Q-12 | ¿Qué queda fuera del alcance de la funcionalidad? | con respaldo | SRC-FUN, fuera de alcance | pendiente |
| Q-13 | ¿Cuál es el tiempo máximo de respuesta exigido para registrar un comentario? | sin respaldo | Ningún documento fija requisitos de rendimiento | pendiente |
| Q-14 | ¿Cómo se autentica a un revisor con usuario y contraseña? | sin respaldo | No hay autenticación; las cuentas están fuera de alcance, pero no se describe ningún mecanismo | pendiente |
| Q-15 | ¿Cuántos comentarios por segundo soporta el sistema en producción? | sin respaldo | No hay mediciones de carga | pendiente |
| Q-16 | ¿Qué servidor de nube aloja la aplicación? | sin respaldo | No se describe despliegue | pendiente |
| Q-17 | ¿Cómo se envían notificaciones por correo al diseñador? | sin respaldo | Notificaciones fuera de alcance; ningún mecanismo descrito | pendiente |
| Q-18 | ¿Qué precio tiene la suscripción mensual? | sin respaldo | No hay información comercial | pendiente |
| Q-19 | ¿En qué idiomas se traduce automáticamente la interfaz? | sin respaldo | No hay interfaz ni traducción | pendiente |
| Q-20 | ¿Qué base de datos guarda el registro de auditoría de pagos? | sin respaldo | No existen pagos ni auditoría | pendiente |
