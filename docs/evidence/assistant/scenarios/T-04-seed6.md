# Informe de verificación

**Pregunta:** ¿Qué evidencia muestra que no se guarda un comentario en una ronda cerrada?

**Requisito verificado:** RF-02: Solo se aceptan comentarios en una ronda abierta; en una ronda cerrada se rechaza y no se guarda nada.

**Conclusión:** sustentada

## Fuentes consultadas
- SRC-CA#ca-02-rechazar-comentarios-en-una-ronda-cerrada-rf-02
- SRC-README#requisitos/rf-02

## Herramientas usadas
- search_requirements
- get_test_result
- run_test

## Resultados verificados
- U-02
- I-02

## Límites de la conclusión
- No se ejecutaron otras pruebas del catálogo que también verifican RF-02 (p. ej. U-05, F-04), pero la evidencia documental y al menos una prueba vigente aprobada es suficiente para sostener el requisito.

## Observaciones del validador
- herramientas declaradas ['get_test_result', 'run_test'] reemplazadas por las realmente usadas ['search_requirements', 'get_test_result', 'run_test']
