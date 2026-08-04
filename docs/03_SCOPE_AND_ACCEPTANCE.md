# ALSEMA AI CORE — Alcance y criterios de aceptación

## 1. Objetivo de este documento

Este archivo define qué debe quedar realmente operativo en el Foundation Build v1.0 y qué capacidades quedan fuera. Ninguna funcionalidad se considerará terminada por existir únicamente en la interfaz o en una clase sin integración de punta a punta.

## 2. Alcance incluido

### 2.1 Instalación y operación local

Debe existir un flujo documentado y comprobado para:

1. clonar el repositorio;
2. copiar `.env.example` a `.env`;
3. configurar el administrador inicial;
4. iniciar servicios con Docker Compose;
5. abrir el frontend;
6. completar o validar la instalación inicial;
7. conectar Ollama ejecutándose en el host Windows o en una URL remota.

### 2.2 Identidad y acceso

Incluye:

- administrador inicial;
- login y logout;
- refresh tokens revocables;
- roles y permisos básicos;
- API keys con scopes;
- auditoría de acciones sensibles.

### 2.3 Proveedores y modelos

Incluye:

- abstracción de proveedor;
- adaptador Ollama;
- healthcheck;
- listado de modelos instalados;
- perfiles de configuración de modelo;
- descarga y eliminación iniciadas explícitamente por administrador;
- errores claros ante proveedor inaccesible o modelo inexistente.

### 2.4 Chat y conversaciones

Incluye:

- conversaciones persistentes;
- respuesta en streaming;
- selector de modelo o agente;
- cancelación;
- regeneración;
- edición con comportamiento documentado;
- Markdown, código y copia desde UI;
- historial recuperable.

### 2.5 Agentes

Incluye:

- creación y edición versionada;
- prompt de sistema;
- perfil de modelo;
- parámetros;
- herramientas asignadas;
- memoria configurable;
- esquema JSON de salida opcional;
- activar, desactivar, duplicar y probar.

### 2.6 Herramientas y plugins básicos

Incluye herramientas funcionales y seguras para:

- HTTP con restricciones;
- filesystem dentro de sandbox;
- ejecución Python controlada;
- utilidades internas.

Incluye registro, permisos, esquemas, timeout, logs y auditoría.

### 2.7 Tareas

Incluye:

- cola ARQ;
- persistencia;
- progreso;
- eventos;
- reintentos;
- cancelación cooperativa;
- resultado;
- historial y filtros.

### 2.8 Workflows básicos

Incluye:

- editor visual básico;
- validación de grafo;
- versionado;
- nodos input, agent/LLM, HTTP, file, Python, condition y output;
- ejecución observable;
- estado y salida por nodo.

### 2.9 Memoria básica

Incluye:

- memoria por ámbito;
- namespaces;
- metadatos;
- búsqueda textual;
- expiración opcional;
- permisos.

### 2.10 Administración y observabilidad

Incluye:

- dashboard real;
- estado de servicios;
- tareas recientes;
- latencias y errores básicos;
- logs estructurados;
- auditoría;
- configuración desde interfaz para opciones no secretas y reemplazo seguro de secretos.

## 3. Fuera de alcance

No implementar en v1:

- lógica de Cometa G, InstaNews u otras empresas;
- Google Sheets;
- Telegram, Facebook, Instagram, WhatsApp o Discord;
- audio/TTS;
- generación de imágenes, video o 3D;
- scraping web general;
- browser automation;
- cluster multi-GPU distribuido;
- marketplace público;
- pagos y suscripciones;
- Kubernetes;
- RAG empresarial avanzado;
- compatibilidad completa con n8n;
- aplicación móvil.

Estos elementos no deben aparecer como botones falsos ni endpoints simulados.

## 4. Criterios globales de aceptación

El Foundation Build se acepta únicamente si:

- todos los servicios requeridos inician;
- migraciones se aplican en una base vacía;
- tests automáticos relevantes pasan;
- no hay secretos en el repositorio;
- no existen errores críticos en consola del navegador;
- no existen endpoints obligatorios que devuelvan datos falsos;
- la documentación permite a una persona no desarrolladora iniciar el sistema siguiendo pasos claros;
- los flujos E2E siguientes funcionan.

## 5. Pruebas de aceptación de punta a punta

### AC-01 — Inicio limpio

**Dado** un equipo con Docker Desktop y Ollama instalado,
**cuando** se configura `.env` y se ejecuta `docker compose up -d --build`,
**entonces** PostgreSQL, Redis, API, worker y frontend quedan saludables, y la UI informa el estado de Ollama sin bloquear el resto del sistema.

### AC-02 — Instalación inicial

**Dado** un sistema sin usuarios,
**cuando** se completa la instalación inicial,
**entonces** se crea un único administrador, el proceso no puede repetirse sin autorización y el evento queda auditado.

### AC-03 — Autenticación

**Dado** un administrador válido,
**cuando** inicia sesión,
**entonces** obtiene una sesión funcional; al cerrar sesión el refresh token queda revocado.

### AC-04 — Detección de Ollama

**Dado** Ollama accesible,
**cuando** se abre Providers,
**entonces** el sistema muestra estado saludable y los modelos realmente instalados.

**Dado** Ollama inaccesible,
**entonces** la UI muestra un error accionable y el dashboard sigue funcionando.

### AC-05 — Chat con streaming

**Dado** un modelo instalado,
**cuando** el usuario envía un mensaje,
**entonces** recibe tokens progresivamente, puede cancelar y la conversación queda persistida.

### AC-06 — Recuperación de conversación

**Dado** una conversación existente,
**cuando** el navegador se recarga,
**entonces** se recuperan mensajes, estados y respuesta final sin duplicados.

### AC-07 — Agente versionado

**Dado** un agente publicado,
**cuando** se modifica su prompt,
**entonces** se crea una nueva versión o un historial inmutable equivalente, y las ejecuciones anteriores conservan referencia a la versión usada.

### AC-08 — Salida estructurada

**Dado** un agente con esquema JSON,
**cuando** se ejecuta con un modelo compatible,
**entonces** la plataforma valida la respuesta; si falla, registra el error y aplica la política de reintento configurada sin inventar campos.

### AC-09 — Herramienta filesystem segura

**Dado** un directorio sandbox autorizado,
**cuando** un agente lee o escribe dentro de él,
**entonces** la operación funciona y queda auditada.

**Cuando** intenta acceder fuera del sandbox,
**entonces** se rechaza y queda registrado el intento.

### AC-10 — Herramienta HTTP segura

**Dado** un destino permitido,
**cuando** se ejecuta una solicitud HTTP,
**entonces** se respetan timeout, tamaño máximo y auditoría.

**Cuando** se intenta acceder a destinos privados o bloqueados según política,
**entonces** la solicitud se rechaza para evitar SSRF.

### AC-11 — Tarea asíncrona

**Dado** un trabajo de duración suficiente,
**cuando** se inicia,
**entonces** la API devuelve `202`, la UI muestra progreso y el resultado queda disponible aunque el navegador se cierre.

### AC-12 — Reintento de tarea

**Dado** un error transitorio,
**cuando** la política permite reintento,
**entonces** el sistema reintenta con backoff y registra cada intento.

### AC-13 — Cancelación

**Dado** una tarea en ejecución,
**cuando** se solicita cancelación,
**entonces** pasa por estado `cancelling`, el worker coopera y finaliza como `cancelled` sin publicarla como exitosa.

### AC-14 — Workflow funcional

**Dado** un workflow `input → agent → output`,
**cuando** se valida y ejecuta,
**entonces** cada nodo registra estado y salida, y el resultado final es consultable.

### AC-15 — Workflow con condición

**Dado** un nodo condition,
**cuando** la expresión se evalúa,
**entonces** solo se ejecuta la rama correspondiente y queda trazabilidad de la decisión.

### AC-16 — Memoria aislada

**Dadas** memorias en namespaces diferentes,
**cuando** un usuario o API key consulta uno de ellos,
**entonces** no puede recuperar entradas del otro sin permiso explícito.

### AC-17 — API key limitada

**Dada** una API key con scope de ejecución de agente,
**cuando** intenta administrar usuarios,
**entonces** recibe rechazo de autorización.

### AC-18 — Auditoría

**Cuando** se crea una API key, se cambia un proveedor, se ejecuta una herramienta sensible o se modifica un agente,
**entonces** se registra actor, acción, fecha, objetivo y resultado sin guardar secretos.

### AC-19 — Backups

**Dado** un entorno con datos,
**cuando** se sigue la guía de backup y restore,
**entonces** se recuperan configuración y entidades persistentes en una instalación limpia.

### AC-20 — Calidad automatizada

**Cuando** se ejecuta el pipeline de CI,
**entonces** lint, tipado, pruebas backend, pruebas frontend y build terminan correctamente.

## 6. Definición de terminado por funcionalidad

Una funcionalidad está terminada cuando:

1. cumple criterios funcionales;
2. posee autorización correcta;
3. maneja errores esperables;
4. registra observabilidad necesaria;
5. tiene pruebas;
6. está documentada;
7. funciona desde UI o API según corresponda;
8. no depende de mocks en producción.

## 7. Condiciones de rechazo

El Foundation Build debe rechazarse si ocurre cualquiera de estas situaciones:

- el chat funciona solo mediante respuestas no persistidas;
- los workflows son únicamente un dibujo sin ejecución;
- las tareas dependen de la conexión del navegador;
- los plugins son carpetas vacías;
- las métricas son valores inventados;
- el sistema requiere editar código para configurar aspectos normales;
- los secretos aparecen en logs o respuestas;
- una API key sin scope puede ejecutar acciones administrativas;
- el sistema afirma soportar integraciones fuera de alcance;
- `docker compose up` no produce un entorno utilizable.

## 8. Evidencia de entrega

El informe final debe incluir:

- versión y commit;
- arquitectura implementada;
- comandos ejecutados;
- resultados de tests;
- capturas o evidencia equivalente de flujos principales;
- limitaciones conocidas;
- riesgos abiertos;
- instrucciones de operación;
- lista explícita de capacidades diferidas.
