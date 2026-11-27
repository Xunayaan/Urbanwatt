// Couche d'accès à l'API : un seul endroit qui connaît l'URL de base et le format des erreurs.
const BASE = (window.APP_CONFIG?.API_BASE ?? "/api").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(status, body) {
    super(formatDetail(status, body));
    this.status = status;
    this.body = body;
  }
}

// Transforme les erreurs de l'API en message lisible.
//  - 422 de validation FastAPI : detail = [{loc, msg}, ...]
//  - erreurs maison / PostgreSQL : detail = "texte" (+ "info" = détail PostgreSQL)
function formatDetail(status, body) {
  if (status === 0) return "API injoignable (réseau ou conteneur arrêté)";
  const d = body?.detail;
  if (Array.isArray(d)) {
    return d.map((e) => `${(e.loc || []).slice(1).join(".") || "requête"} : ${e.msg}`).join(" · ");
  }
  let msg = typeof d === "string" ? d : `Erreur HTTP ${status}`;
  if (body?.info) msg += ` — ${body.info}`;
  return msg;
}

function buildUrl(path, params) {
  const url = new URL(BASE + path, window.location.origin);
  for (const [k, v] of Object.entries(params || {})) {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
  }
  return url;
}

async function request(method, path, { params, body } = {}) {
  let res;
  try {
    res = await fetch(buildUrl(path, params), {
      method,
      headers: body !== undefined ? { "Content-Type": "application/json" } : {},
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, null);
  }
  if (res.status === 204) return null;
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* corps vide ou non JSON */
  }
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}

export const api = {
  get: (path, params) => request("GET", path, { params }),
  post: (path, opts = {}) => request("POST", path, opts),
  patch: (path, opts = {}) => request("PATCH", path, opts),
  del: (path) => request("DELETE", path),
};

// Requête « brute » pour la console : renvoie statut, durée et texte sans lever d'exception HTTP.
export async function rawFetch(method, path, bodyText) {
  const t0 = performance.now();
  try {
    const res = await fetch(BASE + path, {
      method,
      headers: bodyText ? { "Content-Type": "application/json" } : {},
      body: bodyText || undefined,
    });
    return { status: res.status, ms: Math.round(performance.now() - t0), text: await res.text() };
  } catch {
    return { status: 0, ms: Math.round(performance.now() - t0), text: "API injoignable" };
  }
}

export const API_BASE = BASE;
