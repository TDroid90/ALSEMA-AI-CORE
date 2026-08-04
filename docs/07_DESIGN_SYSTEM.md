# 07 — Design System

## Objetivo

Definir una identidad visual consistente para ALSEMA AI CORE. La interfaz debe sentirse como una herramienta profesional de infraestructura, no como un panel genérico, una consola gamer ni una demo de inteligencia artificial.

## Personalidad

- Sobria.
- Precisa.
- Técnica.
- Silenciosa.
- Confiable.
- Moderna sin exageración.

Referencias de tono visual: Linear, Vercel, Raycast, Cursor y OpenAI. No deben copiarse literalmente.

## Paleta

### Fondos

- `--bg-canvas: #0B0B0B`
- `--bg-surface: #141414`
- `--bg-elevated: #1A1A1A`
- `--bg-hover: #202020`
- `--bg-selected: #10242A`

### Bordes

- `--border-subtle: #232323`
- `--border-default: #2D2D2D`
- `--border-strong: #3A3A3A`

### Texto

- `--text-primary: #F2F2F2`
- `--text-secondary: #A7A7A7`
- `--text-muted: #737373`
- `--text-disabled: #505050`

### Acento

- `--accent-primary: #00B8D9`
- `--accent-hover: #14C4E3`
- `--accent-soft: rgba(0, 184, 217, 0.12)`
- `--accent-border: rgba(0, 184, 217, 0.35)`

El cian se usa con moderación para foco, selección, enlaces, progreso y estados activos. No usarlo como fondo dominante.

### Estados

Los estados deben ser apagados y accesibles:

- éxito: `#5FAF7B`
- advertencia: `#C3A45D`
- error: `#C76868`
- información: `#6F9FC7`

No utilizar verde, amarillo o rojo fluorescente.

## Tipografía

### Interfaz

Preferencia:

```text
Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
```

### Código y datos técnicos

```text
"JetBrains Mono", "SFMono-Regular", Consolas, monospace
```

Si las fuentes no están instaladas, el sistema debe funcionar correctamente con fallbacks.

### Escala

- Display: 32/40, peso 600.
- H1: 24/32, peso 600.
- H2: 20/28, peso 600.
- H3: 16/24, peso 600.
- Body: 14/21, peso 400.
- Small: 12/18, peso 400.
- Micro: 11/16, peso 500.

Evitar titulares gigantes. La densidad debe ser adecuada para una herramienta operativa.

## Espaciado

Base de 4 px:

- 4, 8, 12, 16, 20, 24, 32, 40, 48.

Reglas:

- Separación interna estándar: 16 px.
- Paneles principales: 20–24 px.
- Filas de tablas: 40–48 px.
- Barra lateral: 240 px expandida y 64 px colapsada.
- Header: 56–64 px.

## Radios

- pequeño: 4 px.
- control: 6 px.
- panel: 8 px.
- modal: 10 px.

No utilizar tarjetas excesivamente redondeadas.

## Sombras

Mínimas. Priorizar contraste de superficies y bordes.

```css
box-shadow: 0 8px 24px rgba(0, 0, 0, 0.28);
```

Solo para modales, menús flotantes y elementos elevados.

## Layout principal

```text
┌────────────────────────────────────────────────────────────┐
│ Sidebar │ Header / Context / Actions                       │
│         ├──────────────────────────────────────────────────┤
│         │ Main content                                     │
│         │                                                  │
│         │                                                  │
└────────────────────────────────────────────────────────────┘
```

### Navegación inicial

- Inicio
- Chat
- Agentes
- Workflows
- Modelos
- Proveedores
- Herramientas
- Plugins
- Tareas
- Memoria
- Logs
- Sistema
- Configuración

La navegación debe agruparse por función y no convertirse en una lista interminable.

## Pantalla de inicio

Debe responder rápidamente:

- ¿Está sano el sistema?
- ¿Está conectado Ollama?
- ¿Qué modelo está activo?
- ¿Hay tareas en ejecución o fallidas?
- ¿Cuánta actividad hubo recientemente?

Widgets iniciales:

- Estado del Core.
- Estado de PostgreSQL, Redis, worker y Ollama.
- Modelo predeterminado.
- Tareas activas.
- Errores recientes.
- Actividad reciente.

No llenar el dashboard con gráficos decorativos.

## Chat

### Estructura

- Lista de conversaciones a la izquierda o integrada en sidebar secundaria.
- Conversación central.
- Inspector opcional a la derecha para agente, modelo, tokens y ejecuciones.
- Composer fijo abajo.

### Mensajes

- Diferenciar roles por alineación y superficie, no por colores fuertes.
- Markdown legible.
- Código con encabezado de lenguaje y botón copiar.
- Tool calls colapsables.
- Metadatos discretos: modelo, duración, tokens, estado.

### Composer

Incluye:

- entrada multilinea;
- adjuntos;
- selector de agente;
- selector de modelo;
- botón enviar/detener;
- acceso a parámetros avanzados.

No exponer todos los parámetros técnicos por defecto.

## Tablas

- Cabecera fija cuando sea útil.
- Orden y filtros visibles.
- Densidad cómoda.
- Estados mediante badge discreto.
- Acciones secundarias en menú contextual.
- Filas clicables cuando abren detalle.
- Skeleton durante carga.
- Estado vacío con acción concreta.

## Formularios

- Labels siempre visibles.
- Ayuda debajo del campo.
- Errores junto al campo.
- Validación progresiva sin hostilidad.
- Guardado explícito para configuraciones importantes.
- Avisar cambios sin guardar.
- Secretos con estado configurado y acción reemplazar; nunca mostrar el valor actual.

## Botones

### Primary

Fondo cian, texto oscuro. Reservado para una acción principal por contexto.

### Secondary

Fondo gris elevado y borde.

### Ghost

Sin fondo, para acciones menores.

### Destructive

Rojo apagado y confirmación cuando el efecto sea irreversible.

No usar más de un botón primario visual por bloque.

## Estados y feedback

Toda operación debe mostrar:

- inicio;
- progreso cuando dura más de unos segundos;
- resultado;
- error recuperable;
- enlace a detalles o logs cuando corresponda.

Los toast son complementarios. Las tareas largas deben permanecer visibles en el centro de tareas.

## Accesibilidad

- Contraste WCAG AA como mínimo.
- Navegación completa por teclado.
- Focus ring cian visible.
- Etiquetas ARIA.
- No depender únicamente del color.
- Respetar `prefers-reduced-motion`.
- Tamaño táctil mínimo de 36 px en escritorio y 44 px cuando corresponda.

## Movimiento

- Transiciones de 120–180 ms.
- Curvas suaves.
- Sin animaciones decorativas persistentes.
- Streaming de texto sin efectos de máquina de escribir exagerados.
- Skeletons discretos.

## Iconografía

Usar una única librería consistente, preferentemente Lucide.

- Trazo fino o regular.
- Tamaño 16–20 px.
- No mezclar estilos.
- Los iconos acompañan texto; no reemplazan labels críticos.

## Componentes base

Foundation Build debe incluir componentes reutilizables:

- AppShell
- Sidebar
- Header
- PageHeader
- Button
- IconButton
- Input
- Textarea
- Select
- Combobox
- Checkbox
- Switch
- Tabs
- Badge
- Tooltip
- Dropdown
- Modal
- Drawer
- Table
- Pagination
- EmptyState
- Skeleton
- Alert
- Toast
- CodeBlock
- MarkdownRenderer
- StatusIndicator
- ProgressBar
- LogViewer
- JsonViewer

## Prohibiciones visuales

- Neón intenso.
- Degradados multicolor.
- Glassmorphism excesivo.
- Fondos animados.
- Tipografía futurista.
- Cards para absolutamente todo.
- Sombras profundas permanentes.
- Colores chillones para estados normales.
- Ilustraciones genéricas de robots.
- Estética gamer.

## Criterio de aceptación visual

La interfaz debe poder permanecer abierta durante horas sin fatiga visual, permitir lectura rápida de estados y transmitir que el sistema es una herramienta seria de operación local de IA.
