export const esc = (v) =>
  String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

export const ESTADOS = {
  vencido: { texto: "Vencido", clase: "danger", icono: "x-octagon-fill" },
  proximo: { texto: "Por vencer", clase: "warning text-dark", icono: "exclamation-triangle-fill" },
  vigente: { texto: "Vigente", clase: "success", icono: "check-circle-fill" },
  sin_fecha: { texto: "Sin fecha", clase: "secondary", icono: "dash-circle" },
};
export const COLORES = { vencido: "#dc2626", proximo: "#f59e0b", vigente: "#059669", sin_fecha: "#9ca3af" };

export const badgeEstado = (estado) => {
  const e = ESTADOS[estado] || ESTADOS.sin_fecha;
  return `<span class="badge badge-estado text-bg-${e.clase}"><i class="bi bi-${e.icono} me-1"></i>${e.texto}</span>`;
};

export function fmtFecha(iso) {
  if (!iso) return "—";
  const [a, m, d] = String(iso).slice(0, 10).split("-");
  return `${d}/${m}/${a}`;
}
export function fmtFechaHora(iso) {
  if (!iso) return "—";
  const f = new Date(String(iso).replace(" ", "T"));
  return isNaN(f) ? "—" : f.toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" });
}
export const fmtMoneda = (n) => "S/ " + Number(n || 0).toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function diasTexto(dias) {
  if (dias === null || dias === undefined) return "—";
  if (dias < 0) return `Venció hace ${-dias} d`;
  if (dias === 0) return "Vence hoy";
  return `${dias} d`;
}

export const spinner = (texto = "Cargando…") =>
  `<div class="empty"><div class="spinner-border text-success mb-3" role="status"></div><div>${esc(texto)}</div></div>`;
export const vacio = (texto, icono = "inbox") => `<div class="empty"><i class="bi bi-${icono}"></i>${esc(texto)}</div>`;
export const errorBox = (e) =>
  `<div class="alert alert-danger d-flex align-items-center gap-2"><i class="bi bi-exclamation-octagon-fill"></i><div>${esc(e.message || e)}</div></div>`;

export function toast(mensaje, tipo = "success") {
  const el = document.createElement("div");
  el.className = `toast align-items-center text-bg-${tipo === "error" ? "danger" : tipo} border-0`;
  el.setAttribute("role", "alert");
  el.innerHTML = `<div class="d-flex"><div class="toast-body">${esc(mensaje)}</div>
    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Cerrar"></button></div>`;
  document.getElementById("toasts").appendChild(el);
  const t = new bootstrap.Toast(el, { delay: tipo === "error" ? 6000 : 3500 });
  el.addEventListener("hidden.bs.toast", () => el.remove());
  t.show();
}

/** Muestra un modal Bootstrap con el HTML dado. Devuelve { el, close }. */
export function modal({ titulo, cuerpo, pie = "", grande = false }) {
  const el = document.createElement("div");
  el.className = "modal fade";
  el.tabIndex = -1;
  el.innerHTML = `<div class="modal-dialog modal-dialog-centered ${grande ? "modal-lg" : ""}"><div class="modal-content">
    <div class="modal-header"><h2 class="modal-title h5">${esc(titulo)}</h2>
      <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button></div>
    <div class="modal-body">${cuerpo}</div>${pie ? `<div class="modal-footer">${pie}</div>` : ""}</div></div>`;
  document.getElementById("modal-root").appendChild(el);
  const m = new bootstrap.Modal(el);
  el.addEventListener("hidden.bs.modal", () => { m.dispose(); el.remove(); });
  m.show();
  return { el, close: () => m.hide() };
}

export function confirmar(titulo, mensaje, { textoOk = "Confirmar", peligro = false } = {}) {
  return new Promise((resolve) => {
    let resuelto = false;
    const fin = (v) => { if (!resuelto) { resuelto = true; resolve(v); } };
    const m = modal({
      titulo, cuerpo: `<p class="mb-0">${esc(mensaje)}</p>`,
      pie: `<button class="btn btn-light" data-bs-dismiss="modal">Cancelar</button>
            <button class="btn btn-${peligro ? "danger" : "primary"}" id="ok-btn">${esc(textoOk)}</button>`,
    });
    m.el.querySelector("#ok-btn").onclick = () => { fin(true); m.close(); };
    m.el.addEventListener("hidden.bs.modal", () => fin(false));
  });
}

export function paginacion({ page, page_size, total }, onPage) {
  const paginas = Math.max(1, Math.ceil(total / page_size));
  const div = document.createElement("div");
  div.className = "d-flex justify-content-between align-items-center flex-wrap gap-2 p-3 border-top";
  const desde = total ? (page - 1) * page_size + 1 : 0;
  div.innerHTML = `<small class="text-muted">Mostrando ${desde}–${Math.min(page * page_size, total)} de ${total}</small>
    <div class="btn-group"><button class="btn btn-sm btn-outline-secondary" data-p="${page - 1}" ${page <= 1 ? "disabled" : ""}><i class="bi bi-chevron-left"></i></button>
    <span class="btn btn-sm btn-light disabled">${page} / ${paginas}</span>
    <button class="btn btn-sm btn-outline-secondary" data-p="${page + 1}" ${page >= paginas ? "disabled" : ""}><i class="bi bi-chevron-right"></i></button></div>`;
  div.querySelectorAll("button[data-p]").forEach((b) => (b.onclick = () => onPage(Number(b.dataset.p))));
  return div;
}

export function debounce(fn, ms = 300) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

/** Marca campos inválidos con estilos de Bootstrap; devuelve true si el formulario es válido. */
export function validar(form) {
  form.classList.add("was-validated");
  return form.checkValidity();
}

export const kpi = (icono, clase, valor, etiqueta) =>
  `<div class="card h-100"><div class="kpi"><div class="icon ${clase}"><i class="bi bi-${icono}"></i></div>
   <div><div class="value">${esc(valor)}</div><div class="label">${esc(etiqueta)}</div></div></div></div>`;
