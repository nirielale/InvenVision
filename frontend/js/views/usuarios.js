import { api, session } from "../api.js";
import { errorBox, esc, fmtFecha, modal, spinner, toast, validar } from "../ui.js";

export async function usuarios(root, { esActual }) {
  async function cargar() {
    const zona = root.querySelector("#zona");
    zona.innerHTML = spinner();
    let lista;
    try { lista = await api("/usuarios"); } catch (e) { zona.innerHTML = errorBox(e); return; }
    if (!esActual()) return;
    const yo = session.user?.id;
    zona.innerHTML = `<div class="table-responsive"><table class="table table-hover mb-0"><thead><tr>
      <th>Nombre</th><th>Correo</th><th>Rol</th><th>Estado</th><th>Alta</th><th class="text-end">Acciones</th></tr></thead><tbody>
      ${lista.map((u) => `<tr><td class="fw-semibold">${esc(u.nombre)}${u.id === yo ? ' <span class="badge text-bg-light border">Usted</span>' : ""}</td><td>${esc(u.email)}</td>
        <td><select class="form-select form-select-sm w-auto" data-rol="${u.id}" ${u.id === yo ? "disabled" : ""}>
          <option value="operador" ${u.rol === "operador" ? "selected" : ""}>Operador</option><option value="admin" ${u.rol === "admin" ? "selected" : ""}>Administrador</option></select></td>
        <td><span class="badge text-bg-${u.activo ? "success" : "secondary"}">${u.activo ? "Activo" : "Inactivo"}</span></td><td>${fmtFecha(u.creado_en)}</td>
        <td class="text-end">${u.id === yo ? "" : `<button class="btn btn-sm btn-light" data-act="${u.id}" data-valor="${u.activo ? 0 : 1}">${u.activo ? "Desactivar" : "Activar"}</button>`}</td></tr>`).join("")}
      </tbody></table></div>`;
    zona.querySelectorAll("[data-rol]").forEach((s) => (s.onchange = async () => {
      try { await api(`/usuarios/${s.dataset.rol}`, { method: "PUT", body: { rol: s.value } }); toast("Rol actualizado"); }
      catch (e) { toast(e.message, "error"); cargar(); }
    }));
    zona.querySelectorAll("[data-act]").forEach((b) => (b.onclick = async () => {
      try { await api(`/usuarios/${b.dataset.act}`, { method: "PUT", body: { activo: b.dataset.valor === "1" } }); toast("Usuario actualizado"); cargar(); }
      catch (e) { toast(e.message, "error"); }
    }));
  }

  function nuevo() {
    const m = modal({
      titulo: "Nuevo usuario",
      cuerpo: `<form id="f" novalidate>
        <div class="mb-3"><label class="form-label" for="nombre">Nombre</label><input class="form-control" id="nombre" required minlength="2" maxlength="100"><div class="invalid-feedback">Mínimo 2 caracteres.</div></div>
        <div class="mb-3"><label class="form-label" for="email">Correo</label><input type="email" class="form-control" id="email" required><div class="invalid-feedback">Correo no válido.</div></div>
        <div class="mb-3"><label class="form-label" for="password">Contraseña inicial</label><input type="password" class="form-control" id="password" required minlength="8" maxlength="72" autocomplete="new-password"><div class="invalid-feedback">Mínimo 8 caracteres.</div></div>
        <div class="mb-3"><label class="form-label" for="rol">Rol</label><select class="form-select" id="rol"><option value="operador">Operador</option><option value="admin">Administrador</option></select></div></form>`,
      pie: `<button class="btn btn-light" data-bs-dismiss="modal">Cancelar</button><button class="btn btn-primary" id="ok">Crear</button>`,
    });
    const f = m.el.querySelector("#f");
    f.onsubmit = (ev) => { ev.preventDefault(); m.el.querySelector("#ok").click(); };
    m.el.querySelector("#ok").onclick = async () => {
      if (!validar(f)) return;
      try {
        await api("/usuarios", { method: "POST", body: { nombre: f.nombre.value.trim(), email: f.email.value.trim(), password: f.password.value, rol: f.rol.value } });
        toast("Usuario creado"); m.close(); cargar();
      } catch (e) { toast(e.message, "error"); }
    };
  }

  root.innerHTML = `<div class="card"><div class="card-header d-flex justify-content-between align-items-center">Usuarios del sistema
    <button class="btn btn-primary btn-sm" id="nuevo"><i class="bi bi-person-plus me-1"></i>Nuevo usuario</button></div><div id="zona"></div></div>`;
  root.querySelector("#nuevo").onclick = nuevo;
  await cargar();
}
