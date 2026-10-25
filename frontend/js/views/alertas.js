import { api } from "../api.js";
import { badgeEstado, diasTexto, errorBox, esc, fmtFecha, paginacion, spinner, vacio } from "../ui.js";

const PESTANAS = [
  { id: "", texto: "Todos", clave: null },
  { id: "vencido", texto: "Vencidos", clave: "vencido" },
  { id: "proximo", texto: "Por vencer", clave: "proximo" },
  { id: "vigente", texto: "Vigentes", clave: "vigente" },
];

export async function alertas(root, { esActual }) {
  let estado = "", page = 1;

  async function cargar() {
    const zona = root.querySelector("#zona");
    zona.innerHTML = spinner();
    let r;
    try { r = await api("/alertas", { query: { estado, page, page_size: 10 } }); } catch (e) { zona.innerHTML = errorBox(e); return; }
    if (!esActual()) return;
    root.querySelector("#tabs").innerHTML = PESTANAS.map((t) => {
      const n = t.clave ? r.resumen[t.clave] : r.resumen.vencido + r.resumen.proximo + r.resumen.vigente;
      return `<li class="nav-item"><button class="nav-link ${t.id === estado ? "active" : ""}" data-e="${t.id}">${t.texto} <span class="badge text-bg-light">${n}</span></button></li>`;
    }).join("");
    root.querySelectorAll("#tabs [data-e]").forEach((b) => (b.onclick = () => { estado = b.dataset.e; page = 1; cargar(); }));
    if (!r.items.length) { zona.innerHTML = vacio("No hay productos con fecha de vencimiento en esta categoría", "bell-slash"); return; }
    zona.innerHTML = `<div class="table-responsive"><table class="table table-hover mb-0"><thead><tr>
      <th>Producto</th><th>Categoría</th><th>Lote</th><th>Stock</th><th>Vence</th><th>Días restantes</th><th>Estado</th></tr></thead><tbody>
      ${r.items.map((p) => `<tr><td><a class="fw-semibold text-decoration-none" href="#/productos/${p.id}">${esc(p.nombre)}</a><div class="small text-muted">${esc(p.sku)}</div></td>
        <td>${esc(p.categoria)}</td><td>${esc(p.lote || "—")}</td><td>${p.cantidad}</td><td>${fmtFecha(p.fecha_vencimiento)}</td>
        <td>${diasTexto(p.dias_restantes)}</td><td>${badgeEstado(p.estado)}</td></tr>`).join("")}</tbody></table></div>`;
    zona.appendChild(paginacion(r, (p) => { page = p; cargar(); }));
  }

  const cfg = await api("/config-alertas");
  if (!esActual()) return;
  root.innerHTML = `<p class="text-muted">Un producto se considera <strong>por vencer</strong> cuando faltan ${cfg.dias_alerta} días o menos
    (configurable en <a href="#/perfil">Perfil y configuración</a>). Las alertas se muestran dentro de la aplicación; no se envían correos ni mensajes externos.</p>
    <div class="card"><div class="card-header pb-0 border-0"><ul class="nav nav-tabs card-header-tabs" id="tabs"></ul></div><div id="zona"></div></div>`;
  await cargar();
}
