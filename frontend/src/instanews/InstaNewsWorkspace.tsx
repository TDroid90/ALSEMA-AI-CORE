import { useCallback, useEffect, useState } from "react";

const API = "http://localhost:8000/api/v1";

type SocialTemplate = {
  output: "story" | "feed_4_5";
  key: string;
  name: string;
  version: number;
  status: string;
  width: number;
  height: number;
};

type SocialAccount = {
  label: string;
  enabled: boolean;
  auto_publish: boolean;
  connection?: string;
};

type InstaNewsStatus = {
  template_family: string;
  template_version: string;
  templates: SocialTemplate[];
  instagram: SocialAccount[];
  facebook: SocialAccount[];
};

type Props = {
  token: string;
  onOpenTemplates: () => void;
  onOpenInstagram: () => void;
  onOpenFacebook: () => void;
};

function accountSummary(accounts: SocialAccount[]): string {
  if (!accounts.length) return "Falta configurar la cuenta de INSTANEWS";
  const active = accounts.find((account) => account.enabled);
  if (!active) return "La cuenta de INSTANEWS está deshabilitada";
  return `${active.label} · ${active.auto_publish ? "publicación automática" : "confirmación manual"}`;
}

export function InstaNewsWorkspace({ token, onOpenTemplates, onOpenInstagram, onOpenFacebook }: Props): JSX.Element {
  const [status, setStatus] = useState<InstaNewsStatus | null>(null);
  const [notice, setNotice] = useState("Cargando configuración…");

  const loadStatus = useCallback(async () => {
    setNotice("Actualizando…");
    const response = await fetch(`${API}/instanews/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      setNotice("No se pudo leer el estado de INSTANEWS.");
      return;
    }
    setStatus(await response.json() as InstaNewsStatus);
    setNotice("");
  }, [token]);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  return <section className="instanews-workspace">
    <div className="instanews-heading">
      <div>
        <p>PUBLICACIÓN AUTOMÁTICA</p>
        <h1>INSTANEWS</h1>
      </div>
      <button type="button" onClick={() => void loadStatus()}>Actualizar estado</button>
    </div>

    <div className="instanews-flow" aria-label="Flujo automático de INSTANEWS">
      <strong>Noticia publicada</strong><span>→</span><strong>Placas ALSEMA</strong><span>→</span><strong>Facebook e Instagram</strong>
    </div>

    <h2>Plantillas oficiales</h2>
    <div className="instanews-template-grid">
      {status?.templates.map((template) => <article key={template.key}>
        <div className={`instanews-template-preview preview-${template.output}`}>
          <span>GOBIERNO</span>
          <strong>Título de la noticia</strong>
          <small>Resumen periodístico generado para redes.</small>
        </div>
        <div>
          <strong>{template.name}</strong>
          <span>{template.width} × {template.height} px</span>
          <span>Versión {template.version} · {template.status === "published" ? "publicada" : template.status}</span>
        </div>
      </article>)}
    </div>
    <button type="button" className="secondary" onClick={onOpenTemplates}>Abrir editor de plantillas</button>

    <h2>Publicación social</h2>
    <div className="instanews-connections">
      <article>
        <div><strong>Instagram</strong><span>{accountSummary(status?.instagram ?? [])}</span></div>
        <button type="button" onClick={onOpenInstagram}>Configurar</button>
      </article>
      <article>
        <div><strong>Facebook</strong><span>{accountSummary(status?.facebook ?? [])}</span></div>
        <button type="button" onClick={onOpenFacebook}>Configurar</button>
      </article>
    </div>

    {notice && <span className="error" role="status">{notice}</span>}
  </section>;
}
