import { api, session } from "../api.js";
import { confirmar, errorBox, esc, modal, spinner, toast, validar, vacio } from "../ui.js";

export async function categorias(root, { esActual }) {
  const admin = session.isAdmin;

  async function cargar() {
    const zona = root.querySelector("#zona");
    zona.innerHTML = spinner();
    let lista;
    try { lista = await api("/categorias"); } catch (e) { zona.innerHTML = errorBox(e); return; }
    if (!esActual()) return;
    if (!lista.length) { zona.innerHTML = vacio("Aún no hay categorías", "tags"); return; }
    zona.innerHTML = `<div class="table-responsive"><table class="table table-hover mb-0"><thead><tr>
      <th>Nombre</th><th>Productos</th>${admin ? '<th class="text-end">Acciones</th>' : ""}</tr></thead><tbody>
      ${lista.map((c) => `<tr><td class="fw-semibold">${esc(c.nombre)}</td><td>${c.total_productos}</td>
        ${admin ? `<td class="text-end text-nowrap"><button class="btn btn-sm btn-light" data-edit="${c.id}"><i class="bi bi-pencil"></i></button>
          <button class="btn btn-sm btn-light text-danger" data-off="${c.id}" title="Eliminar"><i class="bi bi-trash"></i></button></td>` : ""}</tr>`).join("")}
      </tbody></table></div>`;
    const porId = Object.fromEntries(lista.map((c) => [c.id, c]));
    zona.querySelectorAll("[data-edit]").forEach((b) => (b.onclick = () => formulario(porId[b.dataset.edit])));
    zona.querySelectorAll("[data-off]").forEach((b) => (b.onclick = async () => {
      const c = porId[b.dataset.off];
      if (c.total_productos) { toast(`«${c.nombre}» tiene ${c.total_productos} producto(s); reasígnelos antes de eliminarla.`, "error"); return; }
      if (!(await confirmar("Eliminar categoría", `Se eliminará «${c.nombre}». Esta acción no se puede deshacer.`, { textoOk: "Eliminar", peligro: true }))) return;
      try { await api(`/categorias/${c.id}`, { method: "DELETE" }); toast("Categoría eliminada"); cargar(); }
      catch (e) { toast(e.message, "error"); }
    }));
  }

  function formulario(c) {
    const m = modal({
      titulo: c ? "Editar categoría" : "Nueva categoría",
      cuerpo: `<form id="f" novalidate>
        <div class="mb-3"><label class="form-label" for="nombre">Nombre *</label>
          <input class="form-control" id="nombre" required minlength="2" maxlength="80" value="${esc(c?.nombre)}"><div class="invalid-feedback">Mínimo 2 caracteres.</div></div>
      </form>`,
      pie: `<button class="btn btn-light" data-bs-dismiss="modal">Cancelar</button><button class="btn btn-primary" id="ok">Guardar</button>`,
    });
    const f = m.el.querySelector("#f");
    f.onsubmit = (ev) => { ev.preventDefault(); m.el.querySelector("#ok").click(); };
    m.el.querySelector("#ok").onclick = async () => {
      if (!validar(f)) return;
      const body = { nombre: f.nombre.value.trim() };
      try {
        await api(c ? `/categorias/${c.id}` : "/categorias", { method: c ? "PUT" : "POST", body });
        toast(c ? "Categoría actualizada" : "Categoría creada");
        m.close(); cargar();
      } catch (e) { toast(e.message, "error"); }
    };
  }

  root.innerHTML = `<div class="card"><div class="card-header d-flex justify-content-between align-items-center">Categorías
    ${admin ? '<button class="btn btn-primary btn-sm" id="nueva"><i class="bi bi-plus-lg me-1"></i>Nueva</button>' : '<small class="text-muted fw-normal">Solo un administrador puede modificarlas</small>'}</div><div id="zona"></div></div>`;
  if (admin) root.querySelector("#nueva").onclick = () => formulario(null);
  await cargar();
}
