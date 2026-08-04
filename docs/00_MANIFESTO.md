# ALSEMA AI CORE — Manifiesto

## 1. Propósito

ALSEMA AI CORE existe para convertir capacidad de cómputo local en una plataforma de inteligencia artificial útil, gobernable y reutilizable.

El Core será la infraestructura compartida de un ecosistema de aplicaciones. Su valor no estará en una única interfaz ni en un único modelo, sino en ofrecer una base estable para que distintos clientes puedan solicitar tareas, ejecutar agentes, utilizar herramientas, encadenar workflows, conservar memoria y observar resultados sin conocer la complejidad interna.

## 2. Identidad

ALSEMA AI CORE es un producto de infraestructura.

No pertenece a Cometa G, InstaNews, CreativoSur, CanastApp, Peak, MascotApps ni a otro cliente. Tampoco debe incorporar reglas comerciales, prompts, esquemas de datos o credenciales específicas de esas empresas.

Los clientes se conectarán al Core mediante APIs, SDKs, eventos, webhooks o plugins externos. El Core deberá poder evolucionar sin obligar a reescribir esos clientes.

## 3. Visión

La visión es construir una plataforma local que combine cinco capacidades:

1. **Inferencia:** acceso uniforme a modelos locales y remotos.
2. **Ejecución:** agentes capaces de utilizar herramientas autorizadas.
3. **Orquestación:** workflows repetibles, observables y recuperables.
4. **Conocimiento:** memoria y contexto separados por usuario, proyecto y conversación.
5. **Gobierno:** permisos, auditoría, límites y control operativo.

La interfaz web será una consola del sistema. El chat será una de sus funciones, no su definición.

## 4. Principios irrenunciables

### 4.1 El dominio no depende del proveedor

Los conceptos de agente, mensaje, tarea, herramienta, workflow y memoria no deben conocer detalles de Ollama. Ollama será implementado como un adaptador de proveedor.

### 4.2 Las empresas son clientes externos

Ningún módulo del Core se denominará `cometag`, `instanews` o con el nombre de una unidad comercial. Las integraciones empresariales vivirán fuera del núcleo o como paquetes instalables independientes.

### 4.3 Local por defecto, híbrido por diseño

El sistema debe ofrecer una experiencia completa con infraestructura local. Al mismo tiempo, debe admitir proveedores remotos cuando el administrador lo decida.

### 4.4 Toda acción sensible necesita autoridad

Un modelo no obtiene permisos por el solo hecho de solicitar una herramienta. Las políticas del sistema determinan qué usuario, agente o API key puede ejecutar cada acción.

### 4.5 Los trabajos largos son entidades persistentes

Un procesamiento masivo no puede depender de una conexión abierta del navegador. Debe convertirse en una tarea persistente, con estado, progreso, logs, reintentos, cancelación e idempotencia cuando corresponda.

### 4.6 El error debe ser visible y recuperable

Los errores no se ocultan ni se transforman en respuestas genéricas. Cada fallo debe registrar contexto suficiente para diagnosticarlo sin exponer secretos.

### 4.7 La arquitectura se justifica por necesidades reales

No se crearán abstracciones especulativas, microservicios innecesarios ni sistemas distribuidos prematuros. El Foundation Build utilizará un monolito modular con workers separados y contratos internos claros.

### 4.8 La documentación forma parte del producto

Una funcionalidad no está terminada si carece de criterios de aceptación, documentación operativa y pruebas adecuadas.

## 5. Experiencia esperada

Una persona administradora debe poder:

- iniciar el sistema con Docker Compose;
- completar una configuración inicial guiada;
- comprobar si Ollama está disponible;
- ver y administrar los modelos detectados;
- crear un agente con un prompt y parámetros;
- mantener una conversación con streaming;
- ejecutar una herramienta permitida;
- crear un workflow básico;
- iniciar una tarea y observar su progreso;
- revisar logs y auditoría;
- crear API keys con permisos limitados.

Una aplicación cliente debe poder:

- autenticarse mediante una API key;
- invocar un agente o modelo;
- solicitar salida estructurada;
- iniciar tareas asíncronas;
- consultar estado y resultados;
- recibir eventos de progreso;
- cancelar una tarea cuando la política lo permita.

## 6. Límites de la primera versión

La primera versión no intentará resolver todos los futuros casos de uso.

Quedan fuera del Foundation Build:

- conectores completos con Google Sheets, redes sociales o mensajería;
- generación de audio, imagen, video o 3D;
- marketplace de plugins;
- ejecución distribuida entre múltiples nodos GPU;
- colaboración multiempresa avanzada;
- RAG empresarial complejo;
- editor visual equivalente a n8n;
- facturación o monetización externa.

La arquitectura debe permitir estas capacidades más adelante, pero no debe fingir que están implementadas.

## 7. Cultura de construcción

Codex y cualquier colaborador deben trabajar con estas reglas:

- inspeccionar antes de modificar;
- preferir cambios pequeños y verificables;
- no continuar con una fase rota;
- registrar decisiones irreversibles mediante ADR;
- no esconder deuda técnica bajo nombres como `temporary`, `legacy` o `compat`;
- no incluir secretos, datos personales ni credenciales en el repositorio;
- evitar dependencias sin mantenimiento o sin una razón documentada;
- priorizar claridad sobre ingenio.

## 8. Definición de éxito

El Foundation Build será exitoso cuando ALSEMA AI CORE sea una plataforma local coherente y utilizable, no cuando exista una gran cantidad de carpetas.

La métrica principal será que sus capacidades básicas funcionen de punta a punta:

**usuario autenticado → agente → proveedor Ollama → respuesta en streaming → persistencia → logs y métricas visibles.**

También deberá funcionar:

**solicitud asíncrona → cola → worker → progreso → resultado persistido → consulta desde la API y la interfaz.**

## 9. Promesa del proyecto

ALSEMA AI CORE debe permitir que cada nueva empresa o aplicación aproveche la infraestructura de IA ya construida sin copiar código, duplicar credenciales ni inventar nuevamente la forma de ejecutar tareas.

El Core será estable por dentro, flexible en sus bordes y explícito en sus límites.
