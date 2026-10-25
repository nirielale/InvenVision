const TOKEN_KEY = "iv_token";
const USER_KEY = "iv_user";

function leer(clave) {
  try { return localStorage.getItem(clave); } catch { return null; }
}
function escribir(clave, valor) {
  try { valor === null ? localStorage.removeItem(clave) : localStorage.setItem(clave, valor); } catch { /* sin almacenamiento */ }
}

export const session = {
  get token() { return leer(TOKEN_KEY); },
  get user() { try { return JSON.parse(leer(USER_KEY)); } catch { return null; } },
  set(token, user) { escribir(TOKEN_KEY, token); escribir(USER_KEY, JSON.stringify(user)); },
  setUser(user) { escribir(USER_KEY, JSON.stringify(user)); },
  clear() { escribir(TOKEN_KEY, null); escribir(USER_KEY, null); },
  get isAdmin() { return this.user?.rol === "admin"; },
};

export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

function mensajeDe(detail, status) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => `${(d.loc || []).filter((x) => x !== "body").join(".")}: ${d.msg}`).join("; ");
  }
  return `Error inesperado (${status})`;
}

async function request(path, { method = "GET", body, form, query } = {}) {
  const url = new URL("/api" + path, location.origin);
  Object.entries(query || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
  });
  const headers = {};
  if (session.token) headers.Authorization = `Bearer ${session.token}`;
  const init = { method, headers };
  if (form) init.body = form;
  else if (body !== undefined) { headers["Content-Type"] = "application/json"; init.body = JSON.stringify(body); }

  let resp;
  try { resp = await fetch(url, init); }
  catch { throw new ApiError("No se pudo conectar con el servidor", 0); }

  if (resp.status === 401 && session.token) {
    session.clear();
    location.hash = "#/login";
    throw new ApiError("Su sesión expiró. Inicie sesión nuevamente.", 401);
  }
  if (!resp.ok) {
    let detail = null;
    try { detail = (await resp.json()).detail; } catch { /* sin cuerpo */ }
    throw new ApiError(mensajeDe(detail, resp.status), resp.status);
  }
  return resp;
}

export async function api(path, opciones) {
  const resp = await request(path, opciones);
  return resp.status === 204 ? null : resp.json();
}

/** Descarga un recurso protegido (imagen) y devuelve una URL local para <img>. */
export async function blobUrl(path) {
  const resp = await request(path);
  return URL.createObjectURL(await resp.blob());
}
