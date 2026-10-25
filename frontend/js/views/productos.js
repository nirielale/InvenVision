import { api, blobUrl, session } from "../api.js";
import {
  badgeEstado, confirmar, debounce, diasTexto, errorBox, esc, fmtFecha, fmtFechaHora, fmtMoneda,
  modal, paginacion, spinner, toast, validar, vacio,
} from "../ui.js";

const COLUMNAS = [
  ["nombre", "Producto"], ["sku", "SKU"], [null, "Categoría"], ["cantidad", "Stock"],
  ["fecha_vencimiento", "Vence"], [null, "Estado"],
];

/* ---------------------------- Lista ---------------------------- */
export async function listaProductos(root, { esActual }) {
  const f = { q: "", categoria_id: "", estado: "", ordenar_por: "nombre", orden: "asc", page: 1 };
  const cats = await api("/categorias");
  if (!esActual()) return;

  root.innerHTML = `
    <div class="card">
      <div class="card-body">
        <div class="row g-2 align-items-center">
          <div class="col-12 col-md-4"><div class="input-group"><span class="input-group-text"><i class="bi bi-search"></i></span>
            <input id="q" class="form-control" placeholder="Buscar por nombre, SKU, marca o lote" maxlength="100"></div></div>
          <div class="col-6 col-md-3"><select id="cat" class="form-select"><option value="">Todas las categorías</option>
            ${cats.map((c) => `<option value="${c.id}">${esc(c.nombre)}${c.activa ? "" : " (inactiva)"}</option>`).join("")}</select></div>
          <div class="col-6 col-md-3"><select id="est" class="form-select"><option value="">Todos los estados</option>
            <option value="vigente">Vigentes</option><option value="proximo">Por vencer</option>
            <option value="vencido">Vencidos</option><option value="sin_fecha">Sin fecha</option></select></div>
          <div class="col-12 col-md-2 text-md-end"><a href="#/productos/nuevo" class="btn btn-primary w-100"><i class="bi bi-plus-lg me-1"></i>Nuevo</a></div>
        </div>
      </div>
      <div id="zona"></div>
    </div>`;

  async function cargar() {
    const zona = root.querySelector("#zona");
    zona.innerHTML = spinner();
    let r;
    try { r = await api("/productos", { query: { ...f, page_size: 10 } }); } catch (e) { zona.innerHTML = errorBox(e); return; }
    if (!esActual()) return;
    if (!r.items.length) {
      zona.innerHTML = vacio(f.q || f.categoria_id || f.estado ? "Ningún producto coincide con los filtros" : "Aún no hay productos registrados. Cree el primero con «Nuevo».", "box-seam");
      return;
    }
    const flecha = (k) => (f.ordenar_por === k ? `<i class="bi bi-caret-${f.orden === "asc" ? "up" : "down"}-fill ms-1"></i>` : "");
    zona.innerHTML = `<div class="table-responsive"><table class="table table-hover mb-0"><thead><tr>
      ${COLUMNAS.map(([k, t]) => `<th ${k ? `class="sortable" data-sort="${k}"` : ""}>${t}${k ? flecha(k) : ""}</th>`).join("")}<th class="text-end">Acciones</th></tr></thead><tbody>
      ${r.items.map((p) => `<tr><td class="fw-semibold">${esc(p.nombre)}<div class="small text-muted fw-normal">${esc(p.marca || "")}</div></td>
        <td>${esc(p.sku)}</td><td>${esc(p.categoria)}</td><td>${p.cantidad}</td>
        <td>${fmtFecha(p.fecha_vencimiento)}<div class="small text-muted">${p.dias_restantes === null ? "" : diasTexto(p.dias_restantes)}</div></td>
        <td>${badgeEstado(p.estado)}</td>
        <td class="text-end text-nowrap">
          <a class="btn btn-sm btn-light" href="#/productos/${p.id}" title="Ver detalle"><i class="bi bi-eye"></i></a>
          <button class="btn btn-sm btn-light" data-stock="${p.id}" title="Ajustar stock"><i class="bi bi-plus-slash-minus"></i></button>
          <a class="btn btn-sm btn-light" href="#/productos/${p.id}/editar" title="Editar"><i class="bi bi-pencil"></i></a>
          ${session.isAdmin ? `<button class="btn btn-sm btn-light text-danger" data-del="${p.id}" title="Eliminar"><i class="bi bi-trash"></i></button>` : ""}
        </td></tr>`).join("")}</tbody></table></div>`;
    zona.appendChild(paginacion(r, (p) => { f.page = p; cargar(); }));
    const porId = Object.fromEntries(r.items.map((p) => [p.id, p]));
    zona.querySelectorAll("[data-sort]").forEach((th) => (th.onclick = () => {
      const k = th.dataset.sort;
      f.orden = f.ordenar_por === k && f.orden === "asc" ? "desc" : "asc";
      f.ordenar_por = k; f.page = 1; cargar();
    }));
    zona.querySelectorAll("[data-stock]").forEach((b) => (b.onclick = () => ajustarStock(porId[b.dataset.stock], cargar)));
    zona.querySelectorAll("[data-del]").forEach((b) => (b.onclick = () => eliminar(porId[b.dataset.del], cargar)));
  }

  root.querySelector("#q").oninput = debounce((ev) => { f.q = ev.target.value.trim(); f.page = 1; cargar(); });
  root.querySelector("#cat").onchange = (ev) => { f.categoria_id = ev.target.value; f.page = 1; cargar(); };
  root.querySelector("#est").onchange = (ev) => { f.estado = ev.target.value; f.page = 1; cargar(); };
  await cargar();
}

export function ajustarStock(p, despues) {
  const m = modal({
    titulo: `Ajustar stock · ${p.nombre}`,
    cuerpo: `<p class="text-muted">Stock actual: <strong>${p.cantidad}</strong></p>
      <form id="f" novalidate><label class="form-label" for="delta">Cantidad a sumar (positivo) o restar (negativo)</label>
      <input type="number" class="form-control" id="delta" required step="1" min="${-p.cantidad}" value="1">
      <div class="invalid-feedback">Ingrese un entero; no puede dejar el stock negativo (mínimo ${-p.cantidad}).</div></form>`,
    pie: `<button class="btn btn-light" data-bs-dismiss="modal">Cancelar</button><button class="btn btn-primary" id="ok">Aplicar</button>`,
  });
  const form = m.el.querySelector("#f");
  m.el.querySelector("#ok").onclick = async () => {
    if (!validar(form)) return;
    try {
      await api(`/productos/${p.id}/stock`, { method: "PATCH", body: { delta: Number(form.delta.value) } });
      toast("Stock actualizado");
      m.close();
      despues();
    } catch (e) { toast(e.message, "error"); }
  };
  form.onsubmit = (ev) => { ev.preventDefault(); m.el.querySelector("#ok").click(); };
}

async function eliminar(p, despues) {
  if (!(await confirmar("Eliminar producto", `¿Eliminar «${p.nombre}»? Su historial de detecciones se conservará sin producto asociado.`, { textoOk: "Eliminar", peligro: true }))) return;
  try {
    await api(`/productos/${p.id}`, { method: "DELETE" });
    toast("Producto eliminado");
    despues();
  } catch (e) { toast(e.message, "error"); }
}

/* ------------------------- Crear / editar ------------------------- */
export async function formProducto(root, { params, esActual }) {
  const id = params[0];
  const [cats, existente] = await Promise.all([
    api("/categorias", { query: { solo_activas: true } }),
    id ? api(`/productos/${id}`) : null,
  ]);
  if (!esActual()) return;
  const p = existente || {};
  // Al editar, si la categoría actual está inactiva, se conserva visible
  const opciones = [...cats];
  if (p.categoria_id && !cats.some((c) => c.id === p.categoria_id)) opciones.push({ id: p.categoria_id, nombre: `${p.categoria} (inactiva)` });

  root.innerHTML = `<div class="card"><div class="card-body">
    <form id="f" novalidate class="row g-3">
      <div class="col-md-6"><label class="form-label" for="nombre">Nombre *</label>
        <input class="form-control" id="nombre" required minlength="2" maxlength="150" value="${esc(p.nombre)}"><div class="invalid-feedback">Mínimo 2 caracteres.</div></div>
      <div class="col-md-3"><label class="form-label" for="sku">SKU *</label>
        <input class="form-control" id="sku" required maxlength="50" value="${esc(p.sku)}"><div class="invalid-feedback">El SKU es obligatorio.</div></div>
      <div class="col-md-3"><label class="form-label" for="categoria_id">Categoría *</label>
        <select class="form-select" id="categoria_id" required><option value="">Seleccione…</option>
        ${opciones.map((c) => `<option value="${c.id}" ${c.id === p.categoria_id ? "selected" : ""}>${esc(c.nombre)}</option>`).join("")}</select>
        <div class="invalid-feedback">Seleccione una categoría.</div></div>
      <div class="col-md-4"><label class="form-label" for="marca">Marca</label><input class="form-control" id="marca" maxlength="100" value="${esc(p.marca)}"></div>
      <div class="col-md-4"><label class="form-label" for="lote">Lote</label><input class="form-control" id="lote" maxlength="60" value="${esc(p.lote)}"></div>
      <div class="col-md-4"><label class="form-label" for="proveedor">Proveedor</label><input class="form-control" id="proveedor" maxlength="150" value="${esc(p.proveedor)}"></div>
      <div class="col-md-4"><label class="form-label" for="cantidad">Cantidad *</label>
        <input type="number" class="form-control" id="cantidad" required min="0" step="1" value="${p.cantidad ?? 0}"><div class="invalid-feedback">Entero mayor o igual a 0.</div></div>
      <div class="col-md-4"><label class="form-label" for="precio_costo">Precio de costo (S/) *</label>
        <input type="number" class="form-control" id="precio_costo" required min="0" step="0.01" value="${p.precio_costo ?? ""}"><div class="invalid-feedback">Ingrese un precio válido (≥ 0).</div></div>
      <div class="col-md-4"><label class="form-label" for="fecha_vencimiento">Fecha de vencimiento</label>
        <input type="date" class="form-control" id="fecha_vencimiento" value="${esc(p.fecha_vencimiento)}">
        <div class="form-text">Déjela vacía si no tiene o use el <a href="#/escaner${id ? "?producto=" + id : ""}">escáner</a>.</div></div>
      <div class="col-12"><label class="form-label" for="foto">Fotografía (JPEG, PNG o WEBP, máx. 8 MB)</label>
        <input type="file" class="form-control" id="foto" accept="image/jpeg,image/png,image/webp"></div>
      <div class="col-12 d-flex gap-2 justify-content-end">
        <a class="btn btn-light" href="#/productos">Cancelar</a>
        <button class="btn btn-primary" id="guardar"><i class="bi bi-save me-1"></i>${id ? "Guardar cambios" : "Registrar producto"}</button></div>
    </form></div></div>`;

  const form = root.querySelector("#f");
  form.onsubmit = async (ev) => {
    ev.preventDefault();
    if (!validar(form)) return;
    const archivo = form.foto.files[0];
    if (archivo && archivo.size > 8 * 1024 * 1024) { toast("La fotografía supera los 8 MB", "error"); return; }
    const body = {
      nombre: form.nombre.value.trim(), sku: form.sku.value.trim(), categoria_id: Number(form.categoria_id.value),
      marca: form.marca.value.trim() || null, lote: form.lote.value.trim() || null, proveedor: form.proveedor.value.trim() || null,
      cantidad: Number(form.cantidad.value), precio_costo: form.precio_costo.value,
      fecha_vencimiento: form.fecha_vencimiento.value || null,
    };
    const btn = root.querySelector("#guardar");
    btn.disabled = true;
    try {
      const guardado = await api(id ? `/productos/${id}` : "/productos", { method: id ? "PUT" : "POST", body });
      if (archivo) {
        const fd = new FormData(); fd.append("archivo", archivo);
        try { await api(`/productos/${guardado.id}/foto`, { method: "POST", form: fd }); }
        catch (e) { toast(`Producto guardado, pero la foto falló: ${e.message}`, "warning"); }
      }
      toast(id ? "Producto actualizado" : "Producto registrado");
      location.hash = `#/productos/${guardado.id}`;
    } catch (e) {
      toast(e.message, "error");
      btn.disabled = false;
    }
  };
}

/* ---------------------------- Detalle ---------------------------- */
export async function detalleProducto(root, { params, esActual }) {
  const id = params[0];
  const [p, dets] = await Promise.all([api(`/productos/${id}`), api(`/productos/${id}/detecciones`)]);
  if (!esActual()) return;
  const dato = (t, v) => `<div class="col-6 col-md-4"><div class="small text-muted">${t}</div><div class="fw-semibold">${v}</div></div>`;

  root.innerHTML = `<div class="row g-3">
    <div class="col-lg-8"><div class="card"><div class="card-body">
      <div class="d-flex justify-content-between flex-wrap gap-2 mb-3">
        <div><h2 class="h4 mb-1">${esc(p.nombre)}</h2><div class="text-muted">SKU ${esc(p.sku)} · ${esc(p.categoria)}</div></div>
        <div>${badgeEstado(p.estado)}</div></div>
      <div class="row g-3">
        ${dato("Fecha de vencimiento", fmtFecha(p.fecha_vencimiento))}${dato("Días restantes", diasTexto(p.dias_restantes))}${dato("Stock", p.cantidad + " u.")}
        ${dato("Lote", esc(p.lote || "—"))}${dato("Marca", esc(p.marca || "—"))}${dato("Proveedor", esc(p.proveedor || "—"))}
        ${dato("Precio de costo", fmtMoneda(p.precio_costo))}${dato("Valor en stock", fmtMoneda(p.precio_costo * p.cantidad))}${dato("Última actualización", fmtFechaHora(p.actualizado_en))}
      </div>
      <hr><div class="d-flex flex-wrap gap-2">
        <a class="btn btn-primary" href="#/productos/${p.id}/editar"><i class="bi bi-pencil me-1"></i>Editar</a>
        <button class="btn btn-outline-primary" id="stock"><i class="bi bi-plus-slash-minus me-1"></i>Ajustar stock</button>
        <a class="btn btn-outline-primary" href="#/escaner?producto=${p.id}"><i class="bi bi-camera me-1"></i>Escanear vencimiento</a>
        <a class="btn btn-light ms-auto" href="#/productos">Volver</a></div>
    </div></div></div>
    <div class="col-lg-4"><div class="card h-100"><div class="card-header">Fotografía</div><div class="card-body text-center" id="foto">
      ${p.tiene_foto ? spinner("Cargando…") : vacio("Sin fotografía", "image")}</div></div></div>
    <div class="col-12"><div class="card"><div class="card-header">Historial de detecciones</div>
      ${dets.length ? `<div class="table-responsive"><table class="table mb-0"><thead><tr><th>Fecha</th><th>Fecha detectada</th><th>Resultado</th><th>Confirmada</th></tr></thead><tbody>
        ${dets.map((d) => `<tr><td>${fmtFechaHora(d.creado_en)}</td><td>${fmtFecha(d.fecha_detectada)}</td><td>${esc(d.resultado)}</td>
        <td>${d.confirmada ? '<i class="bi bi-check-circle-fill text-success"></i>' : "—"}</td></tr>`).join("")}</tbody></table></div>`
        : vacio("Este producto no tiene detecciones", "camera")}</div></div></div>`;

  root.querySelector("#stock").onclick = () => ajustarStock(p, () => navegarMismo());
  const navegarMismo = () => window.dispatchEvent(new HashChangeEvent("hashchange"));
  let url = null;
  if (p.tiene_foto) {
    try {
      url = await blobUrl(`/productos/${p.id}/foto`);
      if (esActual()) root.querySelector("#foto").innerHTML = `<img class="img-fluid rounded" src="${url}" alt="Fotografía de ${esc(p.nombre)}">`;
    } catch (e) { root.querySelector("#foto").innerHTML = errorBox(e); }
  }
  return () => url && URL.revokeObjectURL(url);
}
