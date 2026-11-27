# Funcionalidad: registrar un comentario anclado a una región

Prototipo. Base: blueprint del proyecto (marcado, comentario, rondas, versiones).

## Alcance

El sistema recibe los puntos del trazo del revisor sobre un ítem (imagen), calcula la caja delimitadora y guarda el comentario con su región, su versión y su ronda. El comentario se puede recuperar. El revisor puede cerrar la ronda.

## Reglas

- Solo se aceptan comentarios en una ronda abierta; si está cerrada se rechaza y no se guarda nada.
- La caja se calcula como el rectángulo mínimo que contiene los puntos del trazo y se recorta a las dimensiones del ítem.
- El comentario queda asociado a la versión del ítem y a la ronda.
- El comentario requiere texto.
- Cerrar una ronda ya cerrada no cambia nada.

## Datos del comentario

Ronda, ítem y versión, caja (x, y, ancho, alto), texto, nombre del revisor.

## Fuera de alcance

Canvas e interfaz, cuentas, enlaces de revisión, PDFs, audio y transcripción, notificaciones, descubrimiento de intención con IA, comparación de versiones, aprobación de ítems.

## Sin definir

Lenguaje, framework y base de datos; tratamiento de un trazo de un solo punto.
