import { api, blobUrl } from "../api.js";
import { errorBox, esc, fmtFecha, fmtFechaHora, modal, paginacion, spinner, toast, vacio } from "../ui.js";

const RESULTADOS = {
  confirmada: ["success", "Confirmada"], corregida: ["info", "Corregida a mano"],
};

export async function historial(root, { esActual }) {
  let resultado = "", page = 1;
  const urls = [];

  async function cargar() {
    const zona = root.querySelector("#zona");
    zona.innerHTML = spinner();
    let r;
    try { r = await api("/historial", { query: { resultado, page, page_size: 10 } }); } catch (e) { zona.innerHTML = errorBox(e); return; }
    if (!esActual()) return;
    if (!r.items.length) { zona.innerHTML = vacio("No hay detecciones registradas", "camera"); return; }
    zona.innerHTML = `<div class="table-responsive"><table class="table table-hover mb-0"><thead><tr>
      <th>Fecha</th><th>Imagen</th><th>Texto OCR</th><th>Fecha detectada</th><th>Resultado</th><th>Producto</th><th>Confianza OCR</th><th></th></tr></thead><tbody>
      ${r.items.map((h) => { const [c, t] = RESULTADOS[h.resultado] || ["secondary", h.resultado];
        return `<tr><td class="text-nowrap">${fmtFechaHora(h.creado_en)}</td>
        <td>${h.tiene_imagen ? `<button class="btn btn-sm btn-outline-secondary" data-img="${h.id}"><i class="bi bi-image"></i></button>` : "—"}</td>
        <td style="max-width:280px" class="text-truncate" title="${esc(h.texto_ocr || "")}">${esc((h.texto_ocr || "—").replace(/\s+/g, " "))}</td>
        <td>${fmtFecha(h.fecha_detectada)}</td>
        <td><span class="badge text-bg-${c}">${t}</span></td>
        <td>${h.producto_id ? `<a href="#/productos/${h.producto_id}">${esc(h.producto)}</a>` : "—"}</td><td>${h.confianza_ocr == null ? "—" : h.confianza_ocr + " %"}</td>
        <td><button class="btn btn-sm btn-light" data-det="${h.id}">Detalle</button></td></tr>`; }).join("")}</tbody></table></div>`;
    zona.appendChild(paginacion(r, (p) => { page = p; cargar(); }));
    const porId = Object.fromEntries(r.items.map((h) => [h.id, h]));
    zona.querySelectorAll("[data-img],[data-det]").forEach((b) => (b.onclick = () => verDetalle(porId[b.dataset.img || b.dataset.det])));
  }

  async function verDetalle(h) {
    const m = modal({ titulo: `Detección #${h.id}`, grande: true, cuerpo: `<div class="row g-3"><div class="col-md-6" id="img-zona">${spinner("Cargando imagen…")}</div>
      <div class="col-md-6"><div class="small text-muted mb-1">Texto reconocido</div><div class="ocr-text">${esc(h.texto_ocr || "(sin texto)")}</div>
      <div class="mt-3"><strong>Fecha confirmada:</strong> ${fmtFecha(h.fecha_detectada)}</div></div></div>` });
    try {
      const url = await blobUrl(`/historial/${h.id}/imagen`);
      urls.push(url);
      m.el.querySelector("#img-zona").innerHTML = `<img class="scan-preview" src="${url}" alt="Imagen escaneada">`;
    } catch (e) { m.el.querySelector("#img-zona").innerHTML = errorBox(e); toast(e.message, "error"); }
  }

  root.innerHTML = `<div class="card"><div class="card-header d-flex justify-content-between align-items-center flex-wrap gap-2">Escaneos y detecciones
      <select id="filtro" class="form-select form-select-sm w-auto"><option value="">Todos los resultados</option>
      ${Object.entries(RESULTADOS).map(([k, [, t]]) => `<option value="${k}">${t}</option>`).join("")}</select></div><div id="zona"></div></div>`;
  root.querySelector("#filtro").onchange = (ev) => { resultado = ev.target.value; page = 1; cargar(); };
  await cargar();
  return () => urls.forEach((u) => URL.revokeObjectURL(u));
}
