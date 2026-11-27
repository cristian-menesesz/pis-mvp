# Informe de verificación

**Pregunta:** ¿Qué evidencia muestra que no se guarda un comentario en una ronda cerrada?

**Requisito verificado:** RF-02: Solo se aceptan comentarios en una ronda abierta; en una ronda cerrada se rechaza y no se guarda nada.

**Conclusión:** sustentada

## Fuentes consultadas
- SRC-FUN#reglas
- SRC-README#requisitos/rf-02

## Herramientas usadas
- search_requirements
- get_test_result
- run_test

## Resultados verificados
- U-02
- I-02

## Límites de la conclusión
- La prueba no cubre el caso de cierre entre comprobación y escritura, aunque se menciona en los criterios.
- No se verificó explícitamente que ningún comentario aceptado tenga una hora posterior a la del cierre.

## Observaciones del validador
- herramientas declaradas ['search_requirements', 'run_test'] reemplazadas por las realmente usadas ['search_requirements', 'get_test_result', 'run_test']
