# ADR 0004 — Aprobación de herramientas basada en riesgo

- Estado: Aceptada
- Fecha: 2026-08-04

## Contexto

Los agentes y workflows podrán ejecutar herramientas que leen archivos, realizan solicitudes HTTP, modifican datos o ejecutan código. Permitir ejecución irrestricta convertiría una instrucción maliciosa o un error del modelo en una acción real dañina.

## Decisión

Clasificar cada herramienta y operación por nivel de riesgo y aplicar políticas obligatorias antes de ejecutar.

## Niveles

### Bajo

Operaciones de solo lectura dentro de límites autorizados.

Ejemplos:

- leer configuración no secreta;
- consultar estado;
- leer archivo dentro de sandbox;
- realizar cálculo puro.

Puede ejecutarse automáticamente si el agente tiene permiso.

### Medio

Operaciones externas o mutaciones reversibles y acotadas.

Ejemplos:

- solicitud HTTP a dominio permitido;
- escribir archivo nuevo dentro de sandbox;
- actualizar memoria;
- ejecutar plugin con efecto limitado.

Requiere permiso explícito y auditoría. La política puede exigir aprobación según contexto.

### Alto

Operaciones destructivas, ejecución de código, acceso amplio o publicación externa.

Ejemplos:

- ejecutar shell;
- ejecutar Python no confiable;
- borrar archivos;
- modificar credenciales;
- instalar plugins;
- publicar contenido;
- acceder fuera del sandbox.

Requiere aprobación humana por ejecución, salvo política administrativa específica y documentada. Algunas operaciones pueden permanecer prohibidas.

## Evaluación

La decisión final considera:

- riesgo declarado por herramienta;
- operación concreta;
- agente;
- usuario;
- ámbito;
- origen del contenido;
- destino;
- permisos;
- política del sistema.

El modelo no puede reducir el riesgo declarado.

## Aprobación

La solicitud debe mostrar:

- herramienta;
- acción;
- argumentos sanitizados;
- recursos afectados;
- motivo generado por el agente;
- riesgo;
- consecuencias;
- vencimiento.

La aprobación se vincula a argumentos exactos. Cambiar argumentos invalida la aprobación.

## Consecuencias

### Positivas

- Reduce impacto de prompt injection.
- Hace auditables los efectos externos.
- Permite habilitar herramientas gradualmente.
- Protege a usuarios no técnicos.

### Negativas

- Agrega fricción.
- Requiere UI y estados de espera.
- Puede interrumpir workflows largos.

## Reglas

- Denegar por defecto.
- Aplicar allowlists de rutas, dominios y comandos.
- Limitar tiempo, tamaño y recursos.
- Capturar salida sanitizada.
- Nunca exponer secretos al modelo sin necesidad.
- Registrar aprobación, rechazo, expiración y ejecución.
- Permitir cancelación mientras espera.

## Criterios de aceptación

- Una herramienta de alto riesgo no se ejecuta sin aprobación válida.
- Los argumentos ejecutados coinciden con los aprobados.
- Rechazo y expiración dejan el workflow en estado coherente.
- La auditoría identifica actor, herramienta, recursos y resultado.
