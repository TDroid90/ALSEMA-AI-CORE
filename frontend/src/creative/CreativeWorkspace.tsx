import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { CreativeTemplateEditor, type EditorTemplateRecord } from "./CreativeTemplateEditor";

const API = "http://localhost:8000/api/v1/creative";

type Brand = { id: string; slug: string; name: string; profile: Record<string, unknown>; enabled: boolean };
type CatalogItem = { id: string; source_key: string; title: string; category: string; subcategory: string; cutout_ready: boolean; prepared_images: number[]; payload: Record<string, unknown> };
type Asset = { id: string; kind: string; variant?: string; media_type: string; sha256: string; size_bytes: number; width?: number; height?: number };
type CreativeJob = { id: string; task_id?: string; status: string; campaign: string; format: string; templates: string[]; content: { title?: string; specs?: string[] }; provider_plan: Record<string, string>; qa: Record<string, unknown>; error?: string; created_at: string; completed_at?: string; assets: Asset[] };
type ProviderStatus = { text: { primary: { provider: string; status: string; model: string; detail: string }; fallback: { provider: string; status: string; detail: string } }; visual: { provider: string; status: string; detail: string }; deterministic_compositor: { provider: string; status: string } };
type Layer = { id: string; type: "text" | "shape"; name: string; x: number; y: number; width: number; height: number; z: number; visible: boolean; text?: string; fontSize?: number; fontWeight?: number; color?: string; fill?: string; borderRadius?: number };
type TemplateDocument = { id: string; name: string; format: string; width: number; height: number; background: string; layers: Layer[] };
type TemplateRecord = { id: string; key: string; name: string; description: string; document: TemplateDocument; version: number; status: string; created_at: string };
type Tab = "generator" | "history" | "catalog" | "templates" | "providers";

const FORMATS = [
  ["instagram_feed", "Instagram · 1080 × 1350"],
  ["story", "Historia · 1080 × 1920"],
  ["square", "Cuadrado · 1080 × 1080"],
  ["x_horizontal", "Horizontal · 1600 × 900"],
] as const;

function jsonHeaders(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json() as { detail?: string | { message?: string; errors?: string[] } };
    if (typeof body.detail === "string") return body.detail;
    if (body.detail?.errors?.length) return body.detail.errors.join(" · ");
    return body.detail?.message ?? `Error ${response.status}`;
  } catch {
    return `Error ${response.status}`;
  }
}

function statusLabel(status: string): string {
  return ({ queued: "En cola", running: "Generando", pending_approval: "Pendiente de aprobación", approved: "Aprobado", rejected: "Rechazado", failed: "Falló" } as Record<string, string>)[status] ?? status;
}

function AssetPreview({ asset, token, title }: { asset: Asset; token: string; title: string }): JSX.Element {
  const [url, setUrl] = useState("");
  useEffect(() => {
    if (!asset.media_type.startsWith("image/")) return;
    let active = true;
    let objectUrl = "";
    void fetch(`${API}/assets/${asset.id}/content`, { headers: { Authorization: `Bearer ${token}` } })
      .then(response => response.ok ? response.blob() : Promise.reject(new Error()))
      .then(blob => { objectUrl = URL.createObjectURL(blob); if (active) setUrl(objectUrl); })
      .catch(() => undefined);
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [asset.id, asset.media_type, token]);
  async function download(): Promise<void> {
    const response = await fetch(`${API}/assets/${asset.id}/content`, { headers: { Authorization: `Bearer ${token}` } });
    if (!response.ok) return;
    const objectUrl = URL.createObjectURL(await response.blob());
    const anchor = document.createElement("a"); anchor.href = objectUrl; anchor.download = `${title}-${asset.variant ?? asset.kind}.${asset.media_type.includes("json") ? "json" : "png"}`; anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  }
  return <article className="creative-asset-card">
    <div className="creative-preview">{url ? <img src={url} alt={`Creativo ${asset.variant ?? asset.kind}`} /> : <span>{asset.media_type.includes("json") ? "MANIFEST" : "CARGANDO"}</span>}</div>
    <div><strong>{asset.variant ?? asset.kind}</strong><small>{asset.width && asset.height ? `${asset.width} × ${asset.height} · ` : ""}{(asset.size_bytes / 1024).toFixed(0)} KB</small></div>
    <button type="button" className="quiet" onClick={() => void download()}>Descargar</button>
  </article>;
}

function TemplateEditor({ token, records, refresh }: { token: string; records: TemplateRecord[]; refresh: () => Promise<void> }): JSX.Element {
  const starter = (): TemplateDocument => ({ id: crypto.randomUUID(), name: "Plantilla sin nombre", format: "Instagram", width: 1080, height: 1350, background: "#07111f", layers: [
    { id: crypto.randomUUID(), type: "shape", name: "Acento superior", x: 72, y: 72, width: 300, height: 18, z: 1, visible: true, fill: "#00C2FF", borderRadius: 12 },
    { id: crypto.randomUUID(), type: "text", name: "Título principal", x: 72, y: 850, width: 760, height: 180, z: 2, visible: true, text: "TÍTULO DEL PRODUCTO", fontSize: 74, fontWeight: 800, color: "#ffffff" },
    { id: crypto.randomUUID(), type: "text", name: "Llamado a la acción", x: 72, y: 1080, width: 330, height: 72, z: 3, visible: true, text: "Ver producto", fontSize: 30, fontWeight: 800, color: "#07111f", fill: "#00C2FF", borderRadius: 16 },
  ] });
  const [document, setDocument] = useState<TemplateDocument>(starter);
  const [selected, setSelected] = useState<string>(document.layers[1].id);
  const [saving, setSaving] = useState(false);
  const active = document.layers.find(layer => layer.id === selected);
  const scale = Math.min(0.48, 560 / document.height);
  function updateLayer(patch: Partial<Layer>): void { setDocument(current => ({ ...current, layers: current.layers.map(layer => layer.id === selected ? { ...layer, ...patch } : layer) })); }
  function add(type: Layer["type"]): void {
    const layer: Layer = type === "text"
      ? { id: crypto.randomUUID(), type, name: "Texto", x: 100, y: 300, width: 700, height: 120, z: document.layers.length + 1, visible: true, text: "Nuevo texto", fontSize: 42, fontWeight: 700, color: "#ffffff" }
      : { id: crypto.randomUUID(), type, name: "Forma", x: 100, y: 200, width: 300, height: 160, z: document.layers.length + 1, visible: true, fill: "#00C2FF", borderRadius: 16 };
    setDocument(current => ({ ...current, layers: [...current.layers, layer] })); setSelected(layer.id);
  }
  async function save(publish: boolean): Promise<void> {
    setSaving(true);
    const key = document.name.toLocaleLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || `template-${Date.now()}`;
    const response = await fetch(`${API}/templates`, { method: "POST", headers: jsonHeaders(token), body: JSON.stringify({ key, name: document.name, description: "Plantilla creada en ALSEMA", document, publish }) });
    setSaving(false); if (response.ok) await refresh();
  }
  function open(record: TemplateRecord): void { setDocument(record.document); setSelected(record.document.layers[0]?.id ?? ""); }
  return <div className="creative-editor">
    <div className="creative-editor-toolbar"><input aria-label="Nombre de plantilla" value={document.name} onChange={event => setDocument(current => ({ ...current, name: event.target.value }))} /><button type="button" onClick={() => add("text")}>+ Texto</button><button type="button" onClick={() => add("shape")}>+ Forma</button><button type="button" className="primary" disabled={saving} onClick={() => void save(true)}>{saving ? "Guardando…" : "Guardar versión"}</button></div>
    <div className="creative-editor-grid">
      <div className="creative-layer-list"><span className="creative-kicker">CAPAS</span>{[...document.layers].reverse().map(layer => <button type="button" className={selected === layer.id ? "selected" : ""} key={layer.id} onClick={() => setSelected(layer.id)}><b>{layer.type === "text" ? "T" : "◇"}</b><span>{layer.name}</span></button>)}</div>
      <div className="creative-stage"><div className="creative-canvas-scale" style={{ width: document.width * scale, height: document.height * scale }}><div className="creative-canvas" style={{ width: document.width, height: document.height, background: document.background, transform: `scale(${scale})` }}>{document.layers.filter(layer => layer.visible).sort((a, b) => a.z - b.z).map(layer => <div key={layer.id} onClick={() => setSelected(layer.id)} className={`creative-canvas-layer ${selected === layer.id ? "selected" : ""}`} style={{ left: layer.x, top: layer.y, width: layer.width, height: layer.height, zIndex: layer.z, color: layer.color, background: layer.fill, borderRadius: layer.borderRadius, fontSize: layer.fontSize, fontWeight: layer.fontWeight }}>{layer.text}</div>)}</div></div></div>
      <div className="creative-properties"><span className="creative-kicker">PROPIEDADES</span>{active ? <><label>Nombre<input value={active.name} onChange={event => updateLayer({ name: event.target.value })} /></label>{active.type === "text" && <><label>Texto<textarea rows={4} value={active.text} onChange={event => updateLayer({ text: event.target.value })} /></label><label>Color<input type="color" value={active.color ?? "#ffffff"} onChange={event => updateLayer({ color: event.target.value })} /></label></>}<div className="creative-number-grid">{(["x", "y", "width", "height"] as const).map(key => <label key={key}>{key.toUpperCase()}<input type="number" value={active[key]} onChange={event => updateLayer({ [key]: Number(event.target.value) })} /></label>)}</div>{active.type === "shape" && <label>Relleno<input type="color" value={active.fill ?? "#00C2FF"} onChange={event => updateLayer({ fill: event.target.value })} /></label>}<button type="button" className="danger" onClick={() => { setDocument(current => ({ ...current, layers: current.layers.filter(layer => layer.id !== selected) })); setSelected(""); }}>Eliminar capa</button></> : <label>Fondo<input type="color" value={document.background} onChange={event => setDocument(current => ({ ...current, background: event.target.value }))} /></label>}</div>
    </div>
    <div className="creative-template-library"><span className="creative-kicker">BIBLIOTECA VERSIONADA</span>{records.map(record => <button type="button" key={record.id} onClick={() => open(record)}><strong>{record.name}</strong><small>v{record.version} · {record.status}</small></button>)}</div>
  </div>;
}

export function CreativeWorkspace({ token }: { token: string }): JSX.Element {
  const [tab, setTab] = useState<Tab>("generator");
  const [brands, setBrands] = useState<Brand[]>([]); const [brand, setBrand] = useState("cometag");
  const [catalog, setCatalog] = useState<CatalogItem[]>([]); const [catalogId, setCatalogId] = useState(""); const [search, setSearch] = useState("");
  const [jobs, setJobs] = useState<CreativeJob[]>([]); const [selectedJob, setSelectedJob] = useState<CreativeJob>();
  const [templates, setTemplates] = useState<TemplateRecord[]>([]); const [providers, setProviders] = useState<ProviderStatus>();
  const [format, setFormat] = useState("instagram_feed"); const [variants, setVariants] = useState(["A", "B", "C"]); const [campaign, setCampaign] = useState("producto");
  const [imageIndex, setImageIndex] = useState(0);
  const [customTemplate, setCustomTemplate] = useState("");
  const [useTextAi, setUseTextAi] = useState(true); const [useVisualAi, setUseVisualAi] = useState(false); const [notice, setNotice] = useState(""); const [submitting, setSubmitting] = useState(false);
  const [sheetId, setSheetId] = useState(""); const [sheetGid, setSheetGid] = useState("0");
  const auth = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token]);
  const loadJobs = useCallback(async () => { const response = await fetch(`${API}/jobs`, { headers: auth }); if (response.ok) { const items = (await response.json() as { items: CreativeJob[] }).items; setJobs(items); setSelectedJob(current => current ? items.find(item => item.id === current.id) ?? current : items[0]); } }, [auth]);
  const loadTemplates = useCallback(async () => { const response = await fetch(`${API}/templates`, { headers: auth }); if (response.ok) setTemplates((await response.json() as { items: TemplateRecord[] }).items); }, [auth]);
  const loadCatalog = useCallback(async () => { const params = new URLSearchParams({ brand, search, limit: "80" }); const response = await fetch(`${API}/catalog?${params}`, { headers: auth }); if (response.ok) { const items = (await response.json() as { items: CatalogItem[] }).items; setCatalog(items); setCatalogId(current => items.some(item => item.id === current) ? current : items[0]?.id ?? ""); } }, [auth, brand, search]);
  useEffect(() => { void Promise.all([
    fetch(`${API}/brands`, { headers: auth }).then(async response => { if (response.ok) setBrands((await response.json() as { items: Brand[] }).items); }),
    fetch(`${API}/providers`, { headers: auth }).then(async response => { if (response.ok) setProviders(await response.json() as ProviderStatus); }),
    loadJobs(), loadTemplates(),
  ]); }, [auth, loadJobs, loadTemplates]);
  useEffect(() => { void loadCatalog(); }, [loadCatalog]);
  useEffect(() => { const pending = jobs.some(job => ["queued", "running"].includes(job.status)); if (!pending) return; const timer = window.setInterval(() => void loadJobs(), 2500); return () => window.clearInterval(timer); }, [jobs, loadJobs]);
  async function generate(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault(); if (!catalogId || variants.length === 0) return;
    setSubmitting(true); setNotice("Preparando el trabajo creativo…");
    const response = await fetch(`${API}/jobs`, { method: "POST", headers: jsonHeaders(token), body: JSON.stringify({ brand, catalog_item_id: catalogId, campaign, template_keys: variants, format, use_text_ai: useTextAi, use_visual_ai: useVisualAi, image_index: imageIndex }) });
    if (!response.ok) { setNotice(await readError(response)); setSubmitting(false); return; }
    const result = await response.json() as { job_id: string }; setNotice("Trabajo en cola. ALSEMA lo procesará en segundo plano."); setSubmitting(false); await loadJobs(); setTab("history"); setSelectedJob(jobs.find(job => job.id === result.job_id));
  }
  async function prepareAsset(): Promise<void> {
    if (!selectedItem) return;
    setNotice("Preparando el recorte en segundo plano…");
    const response = await fetch(`${API}/catalog/${selectedItem.id}/prepare?image_index=${imageIndex}`, { method: "POST", headers: auth });
    if (!response.ok) setNotice(await readError(response));
    else setNotice("Preparación en cola. Consultá Tareas y actualizá el catálogo cuando termine.");
  }
  async function importCatalogFile(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const form = event.currentTarget; const input = form.elements.namedItem("catalog_file") as HTMLInputElement; const file = input.files?.[0]; if (!file) return;
    const body = new FormData(); body.append("brand", brand); body.append("file", file);
    setNotice("Importando catálogo…"); const response = await fetch(`${API}/catalog/import`, { method: "POST", headers: auth, body });
    if (!response.ok) setNotice(await readError(response)); else { const result = await response.json() as { received: number }; setNotice(`${result.received} productos procesados.`); form.reset(); await loadCatalog(); }
  }
  async function syncGoogleSheet(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault(); setNotice("Sincronizando Google Sheets en modo solo lectura…");
    const response = await fetch(`${API}/catalog/google-sheets/sync`, { method: "POST", headers: jsonHeaders(token), body: JSON.stringify({ brand, sheet_id: sheetId, gid: sheetGid }) });
    if (!response.ok) setNotice(await readError(response)); else { const result = await response.json() as { received: number }; setNotice(`${result.received} productos sincronizados.`); await loadCatalog(); }
  }
  async function decide(decision: "approved" | "rejected"): Promise<void> { if (!selectedJob) return; const response = await fetch(`${API}/jobs/${selectedJob.id}/decision`, { method: "POST", headers: jsonHeaders(token), body: JSON.stringify({ decision, comment: decision === "approved" ? "Aprobado desde el espacio creativo" : "Requiere correcciones" }) }); if (!response.ok) setNotice(await readError(response)); else { setNotice(decision === "approved" ? "Creativo aprobado." : "Creativo rechazado."); await loadJobs(); } }
  const selectedItem = catalog.find(item => item.id === catalogId);
  const gallerySize = selectedItem && Array.isArray(selectedItem.payload.gallery) ? Math.min(3, selectedItem.payload.gallery.length) : 1;
  const selectedImageReady = selectedItem?.prepared_images.includes(imageIndex) ?? false;
  return <section className="creative-page">
    <header className="creative-header"><div><p>ESTUDIO CREATIVO</p><h1>Creativo</h1><span>Producción visual integrada, trazable y lista para aprobación.</span></div><div className="creative-header-state"><i /><div><b>Motor disponible</b><small>Pillow + {providers?.text.primary.model ?? "Ollama"}</small></div></div></header>
    <nav className="creative-tabs" aria-label="Secciones de Creativo">{([['generator', 'Generador'], ['history', `Producción ${jobs.length ? `(${jobs.length})` : ''}`], ['catalog', 'Catálogos'], ['templates', 'Editor de plantillas'], ['providers', 'Proveedores']] as [Tab, string][]).map(([key, label]) => <button type="button" key={key} aria-current={tab === key ? "page" : undefined} onClick={() => setTab(key)}>{label}</button>)}</nav>
    {tab === "generator" && <form className="creative-generator" onSubmit={generate}>
      <div className="creative-form-card"><div className="creative-section-title"><span>01</span><div><h2>Contenido</h2><p>Elegí una marca y un producto del catálogo consolidado.</p></div></div><label>Marca<select value={brand} onChange={event => setBrand(event.target.value)}>{brands.map(item => <option key={item.id} value={item.slug}>{item.name}</option>)}</select></label><label>Buscar producto<div className="creative-search"><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Nombre, SKU o categoría" /><button type="button" onClick={() => void loadCatalog()}>Buscar</button></div></label><label>Producto<select size={8} value={catalogId} onChange={event => { setCatalogId(event.target.value); setImageIndex(0); }}>{catalog.map(item => <option key={item.id} value={item.id}>{item.cutout_ready ? "●" : "○"} {item.title}</option>)}</select></label>{selectedItem && <div className="creative-selection"><small>{selectedItem.category || "PRODUCTO"}</small><strong>{selectedItem.title}</strong>{gallerySize > 1 && <label>Foto del producto<select value={imageIndex} onChange={event => setImageIndex(Number(event.target.value))}>{Array.from({ length: gallerySize }, (_, index) => <option key={index} value={index}>Imagen {index + 1}{selectedItem.prepared_images.includes(index) ? " · lista" : " · sin recorte"}</option>)}</select></label>}<span>{selectedImageReady ? "Imagen recortada lista" : "Requiere preparar el recorte"} · {selectedItem.source_key}</span>{!selectedImageReady && <button type="button" onClick={() => void prepareAsset()}>Preparar imagen {imageIndex + 1} con rembg</button>}</div>}</div>
      <div className="creative-form-card"><div className="creative-section-title"><span>02</span><div><h2>Dirección creativa</h2><p>Configurá formato, campaña y variantes.</p></div></div><label>Formato<select value={format} onChange={event => setFormat(event.target.value)}>{FORMATS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>Campaña<select value={campaign} onChange={event => setCampaign(event.target.value)}><option value="producto">Producto</option><option value="preventa">Preventa</option><option value="nuevo_ingreso">Nuevo ingreso</option></select></label><label>Plantilla<select value={customTemplate} onChange={event => { const key = event.target.value; setCustomTemplate(key); setVariants(key ? [`template:${key}`] : ["A", "B", "C"]); }}><option value="">Direcciones A / B / C</option>{[...new Map(templates.filter(item => item.status === "published").map(item => [item.key, item])).values()].map(item => <option key={item.key} value={item.key}>{item.name} · v{item.version}</option>)}</select></label>{!customTemplate && <fieldset><legend>Variantes</legend><div className="creative-variants">{[["A", "Product Hero"], ["B", "Gaming / Performance"], ["C", "Clean Tech"]].map(([key, label]) => <label className={variants.includes(key) ? "selected" : ""} key={key}><input type="checkbox" checked={variants.includes(key)} onChange={event => setVariants(current => event.target.checked ? [...current, key] : current.filter(item => item !== key))} /><b>{key}</b><span>{label}</span></label>)}</div></fieldset>}<div className="creative-toggles"><label><input type="checkbox" checked={useTextAi} onChange={event => setUseTextAi(event.target.checked)} /><span><b>Mejorar copy con Ollama</b><small>Con fallback determinista</small></span></label><label><input type="checkbox" checked={useVisualAi} onChange={event => setUseVisualAi(event.target.checked)} /><span><b>Fondo generativo</b><small>ComfyUI si está disponible</small></span></label></div><button className="primary creative-generate" disabled={submitting || !catalogId || variants.length === 0 || !selectedImageReady}>{submitting ? "Enviando…" : selectedImageReady ? `Generar ${variants.length} creativo${variants.length === 1 ? "" : "s"}` : "Prepará la imagen para continuar"}</button></div>
    </form>}
    {tab === "history" && <div className="creative-production"><aside className="creative-job-list"><div><span className="creative-kicker">PRODUCCIÓN</span><button type="button" className="quiet" onClick={() => void loadJobs()}>Actualizar</button></div>{jobs.map(job => <button type="button" key={job.id} className={selectedJob?.id === job.id ? "selected" : ""} onClick={() => setSelectedJob(job)}><span className={`creative-status status-${job.status}`}><i />{statusLabel(job.status)}</span><strong>{job.content.title ?? "Creativo"}</strong><small>{new Date(job.created_at).toLocaleString()} · {job.templates.join(" / ")}</small></button>)}</aside><div className="creative-job-detail">{selectedJob ? <><header><div><span className={`creative-status status-${selectedJob.status}`}><i />{statusLabel(selectedJob.status)}</span><h2>{selectedJob.content.title ?? "Trabajo creativo"}</h2><p>{selectedJob.format} · {selectedJob.templates.length} variantes · {selectedJob.provider_plan.compositor}</p></div>{selectedJob.status === "pending_approval" && <div className="creative-approval"><button type="button" className="danger" onClick={() => void decide("rejected")}>Rechazar</button><button type="button" className="primary" onClick={() => void decide("approved")}>Aprobar producción</button></div>}</header>{selectedJob.error && <div className="creative-error"><b>No se pudo completar</b><span>{selectedJob.error}</span></div>}<div className="creative-assets">{selectedJob.assets.map(asset => <AssetPreview key={asset.id} asset={asset} token={token} title={selectedJob.content.title ?? "creativo"} />)}</div><div className="creative-trace"><div><span>JOB ID</span><code>{selectedJob.id}</code></div><div><span>RENDERER</span><code>{selectedJob.provider_plan.compositor ?? "pillow"}</code></div><div><span>ESTADO QA</span><code>{selectedJob.status === "pending_approval" ? "válido · pendiente" : selectedJob.status}</code></div></div></> : <div className="creative-empty"><b>Todavía no hay producción</b><span>Generá el primer trabajo desde el catálogo.</span></div>}</div></div>}
    {tab === "catalog" && <div className="creative-catalog-admin"><div className="creative-form-card"><div className="creative-section-title"><span>01</span><div><h2>Importar archivo</h2><p>Adaptador compatible con CSV y JSON de CreativoSur.</p></div></div><label>Marca<select value={brand} onChange={event => setBrand(event.target.value)}>{brands.map(item => <option key={item.id} value={item.slug}>{item.name}</option>)}</select></label><form onSubmit={event => void importCatalogFile(event)}><label>Archivo de catálogo<input name="catalog_file" type="file" accept=".csv,.json,application/json,text/csv" required /></label><button className="primary">Importar catálogo</button></form></div><div className="creative-form-card"><div className="creative-section-title"><span>02</span><div><h2>Google Sheets</h2><p>Exportación CSV pública, estrictamente de solo lectura.</p></div></div><form onSubmit={event => void syncGoogleSheet(event)}><label>Sheet ID<input value={sheetId} onChange={event => setSheetId(event.target.value)} pattern="[a-zA-Z0-9_-]{20,120}" required /></label><label>GID<input value={sheetGid} onChange={event => setSheetGid(event.target.value)} pattern="[0-9]{1,20}" required /></label><button className="primary">Sincronizar</button></form></div><div className="creative-form-card creative-catalog-summary"><div className="creative-section-title"><span>03</span><div><h2>Inventario</h2><p>{catalog.length} productos cargados en esta vista.</p></div></div><div>{catalog.map(item => <article key={item.id}><i className={item.cutout_ready ? "ready" : ""} /><div><strong>{item.title}</strong><small>{item.category || "Sin categoría"} · {item.source_key}</small></div><span>{item.cutout_ready ? "Listo" : "Sin recorte"}</span></article>)}</div></div></div>}
    {tab === "templates" && <CreativeTemplateEditor token={token} records={templates as unknown as EditorTemplateRecord[]} refresh={loadTemplates} />}
    {tab === "providers" && <div className="creative-provider-grid"><ProviderCard name="Texto principal" provider={providers?.text.primary.provider ?? "Ollama"} status={providers?.text.primary.status} detail={providers?.text.primary.model} /><ProviderCard name="Fallback de texto" provider="LM Studio" status={providers?.text.fallback.status} detail={providers?.text.fallback.detail} /><ProviderCard name="Generación visual" provider="ComfyUI" status={providers?.visual.status} detail={providers?.visual.detail} /><ProviderCard name="Compositor determinista" provider="Pillow" status={providers?.deterministic_compositor.status} detail="Render reproducible y auditable" /></div>}
    {notice && <div className="creative-notice" role="status">{notice}<button type="button" onClick={() => setNotice("")}>×</button></div>}
  </section>;
}

function ProviderCard({ name, provider, status = "unavailable", detail = "Sin información" }: { name: string; provider: string; status?: string; detail?: string }): JSX.Element {
  const healthy = ["healthy", "available", "ok"].includes(status);
  return <article className="creative-provider-card"><div className="creative-provider-icon">{provider.slice(0, 2).toUpperCase()}</div><span className={`creative-status ${healthy ? "status-approved" : "status-queued"}`}><i />{healthy ? "Disponible" : "Opcional / no disponible"}</span><h2>{name}</h2><strong>{provider}</strong><p>{detail}</p></article>;
}
