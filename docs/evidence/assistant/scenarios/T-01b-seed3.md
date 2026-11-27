# Informe de verificación

**Pregunta:** ¿Qué evidencia muestra que no se guarda un comentario en una ronda cerrada?

**Requisito verificado:** RF-02: Solo se aceptan comentarios en una ronda abierta; en una ronda cerrada se rechaza y no se guarda nada.

**Conclusión:** sustentada

## Fuentes consultadas
- SRC-FUN#reglas
- SRC-README#requisitos/rf-02
- SRC-CA#ca-02-rechazar-comentarios-en-una-ronda-cerrada-rf-02

## Herramientas usadas
- search_requirements
- get_test_result
- run_test

## Resultados verificados
- U-02

## Límites de la conclusión
- U-02b, U-05, I-02, F-04, C-01, C-04 no ejecutadas
- se verifica solo el caso de ronda cerrada al momento del envío; otros escenarios específicos no se probaron

## Observaciones del validador
- (ninguno)
