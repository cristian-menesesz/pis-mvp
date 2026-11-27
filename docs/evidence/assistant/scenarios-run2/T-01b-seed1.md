# Informe de verificación

**Pregunta:** ¿Qué evidencia muestra que no se guarda un comentario en una ronda cerrada?

**Requisito verificado:** RF-02: Solo se aceptan comentarios en una ronda abierta; en una ronda cerrada se rechaza y no se guarda nada.

**Conclusión:** sustentada

## Fuentes consultadas
- SRC-CA#ca-02-rechazar-comentarios-en-una-ronda-cerrada-rf-02
- SRC-FUN#reglas
- SRC-README#requisitos/rf-02

## Herramientas usadas
- search_requirements
- get_test_result
- run_test

## Resultados verificados
- U-02

## Límites de la conclusión
- Faltan verificar las otras pruebas mencionadas en CA-02 (U-05, I-02, F-02, F-04, C-01, C-04) para una cobertura completa
- No se verificó el caso específico de cuando la ronda se cierra entre la comprobación del servicio y la escritura

## Observaciones del validador
- (ninguno)
