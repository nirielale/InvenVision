import { api, session } from "../api.js";
import { esc, fmtFecha, toast, validar } from "../ui.js";

export async function perfil(root, { esActual }) {
  const [yo, cfg] = await Promise.all([api("/auth/me"), api("/config-alertas")]);
  if (!esActual()) return;
  session.setUser(yo);
  const admin = yo.rol === "admin";

  root.innerHTML = `<div class="row g-3">
    <div class="col-lg-6"><div class="card h-100"><div class="card-header">Mi perfil</div><div class="card-body">
      <form id="fp" novalidate>
        <div class="mb-3"><label class="form-label" for="nombre">Nombre</label>
          <input class="form-control" id="nombre" required minlength="2" maxlength="100" value="${esc(yo.nombre)}"><div class="invalid-feedback">Mínimo 2 caracteres.</div></div>
        <div class="mb-3"><label class="form-label">Correo</label><input class="form-control" value="${esc(yo.email)}" disabled></div>
        <div class="mb-3"><label class="form-label">Rol</label><div><span class="badge text-bg-${admin ? "success" : "secondary"}">${admin ? "Administrador" : "Operador"}</span></div></div>
        <button class="btn btn-primary">Guardar perfil</button></form></div></div></div>
    <div class="col-lg-6"><div class="card mb-3"><div class="card-header">Cambiar contraseña</div><div class="card-body">
      <form id="fc" novalidate>
        <div class="mb-3"><label class="form-label" for="actual">Contraseña actual</label><input type="password" class="form-control" id="actual" required autocomplete="current-password"><div class="invalid-feedback">Obligatoria.</div></div>
        <div class="mb-3"><label class="form-label" for="nueva">Nueva contraseña</label><input type="password" class="form-control" id="nueva" required minlength="8" maxlength="72" autocomplete="new-password"><div class="invalid-feedback">Mínimo 8 caracteres.</div></div>
        <button class="btn btn-primary">Cambiar contraseña</button></form></div></div>
      <div class="card"><div class="card-header">Configuración de alertas</div><div class="card-body">
        <form id="fa" novalidate><label class="form-label" for="dias">Días de anticipación para «por vencer»</label>
          <div class="input-group mb-2"><input type="number" class="form-control" id="dias" required min="1" max="730" step="1" value="${cfg.dias_alerta}" ${admin ? "" : "disabled"}>
          <span class="input-group-text">días</span><div class="invalid-feedback">Entre 1 y 730.</div></div>
          ${admin ? '<button class="btn btn-primary">Guardar configuración</button>' : '<div class="form-text">Solo un administrador puede cambiar este valor.</div>'}</form></div></div></div></div>`;

  root.querySelector("#fp").onsubmit = async (ev) => {
    ev.preventDefault();
    const f = ev.target; if (!validar(f)) return;
    try {
      const u = await api("/auth/me", { method: "PUT", body: { nombre: f.nombre.value.trim() } });
      session.setUser(u);
      document.getElementById("user-name").textContent = u.nombre;
      document.getElementById("user-avatar").textContent = u.nombre.trim().charAt(0).toUpperCase();
      toast("Perfil actualizado");
    } catch (e) { toast(e.message, "error"); }
  };
  root.querySelector("#fc").onsubmit = async (ev) => {
    ev.preventDefault();
    const f = ev.target; if (!validar(f)) return;
    try {
      await api("/auth/cambiar-password", { method: "POST", body: { actual: f.actual.value, nueva: f.nueva.value } });
      f.reset(); f.classList.remove("was-validated");
      toast("Contraseña actualizada");
    } catch (e) { toast(e.message, "error"); }
  };
  root.querySelector("#fa").onsubmit = async (ev) => {
    ev.preventDefault();
    if (!admin) return;
    const f = ev.target; if (!validar(f)) return;
    try { await api("/config-alertas", { method: "PUT", body: { dias_alerta: Number(f.dias.value) } }); toast("Configuración guardada"); }
    catch (e) { toast(e.message, "error"); }
  };
}

export { fmtFecha };
