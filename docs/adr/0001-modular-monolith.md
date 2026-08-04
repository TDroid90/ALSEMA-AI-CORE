# ADR 0001 — Adoptar un monolito modular para Foundation Build

- Estado: Aceptado
- Fecha: 2026-08-03

## Contexto

ALSEMA AI CORE tendrá múltiples capacidades: identidad, proveedores, conversaciones, agentes, herramientas, plugins, workflows, tareas, memoria y observabilidad. Dividirlas desde el inicio en microservicios aumentaría despliegues, contratos distribuidos, observabilidad, fallos de red y mantenimiento sin una necesidad demostrada.

El sistema debe ser fácil de instalar localmente, operar con recursos limitados y evolucionar mediante límites internos claros.

## Decisión

Implementar el Foundation Build como monolito modular:

- un backend desplegable;
- módulos delimitados por dominio;
- contratos de aplicación explícitos;
- persistencia compartida con ownership de tablas por módulo;
- worker separado para tareas asíncronas, reutilizando la misma base de código;
- frontend separado como aplicación web;
- PostgreSQL y Redis como servicios de infraestructura.

Los módulos no importarán repositorios o modelos ORM privados de otros módulos. La comunicación se realizará mediante servicios públicos, comandos, consultas o eventos internos.

## Consecuencias positivas

- Instalación y debugging simples.
- Transacciones locales cuando sean necesarias.
- Menor consumo operativo.
- Refactor y evolución más rápidos.
- Posibilidad de extraer servicios en el futuro desde límites ya definidos.

## Riesgos

- Acoplamiento accidental entre módulos.
- Crecimiento desordenado del backend.
- Dependencias circulares.

## Mitigaciones

- Reglas de importación.
- Tests arquitectónicos.
- Ownership explícito de tablas.
- Interfaces públicas por módulo.
- Revisión de dependencias en CI.

## Cuándo reconsiderar

Extraer un módulo a servicio independiente solo si existe evidencia concreta:

- necesidad de escalarlo por separado;
- aislamiento de seguridad;
- ciclo de despliegue independiente;
- tecnología incompatible;
- fallos de un módulo afectan de manera inaceptable al resto.
