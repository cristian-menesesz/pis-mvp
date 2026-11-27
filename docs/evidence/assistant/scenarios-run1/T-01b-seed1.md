# Informe de verificación

**Pregunta:** ¿Qué evidencia muestra que no se guarda un comentario en una ronda cerrada?

**Requisito verificado:** RF-02: Solo se aceptan comentarios en una ronda abierta; en una ronda cerrada se rechaza y no se guarda nada.

**Conclusión:** sustentada

## Fuentes consultadas
- SRC-CA#ca-02-rechazar-comentarios-en-una-ronda-cerrada-rf-02

## Herramientas usadas
- search_requirements
- get_test_result
- run_test

## Resultados verificados
- U-02

## Límites de la conclusión
- Faltan verificar las pruebas I-02, F-02, F-04, C-01 y C-04 mencionadas en los criterios de aceptación para una cobertura completa
- No se verificó el comportamiento cuando la ronda se cierra entre la comprobación del servicio y la escritura

## Observaciones del validador
- herramientas declaradas ['search_requirements', 'run_test'] reemplazadas por las realmente usadas ['search_requirements', 'get_test_result', 'run_test']
