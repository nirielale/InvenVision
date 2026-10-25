import { api, session } from "../api.js";
import { esc, toast, validar } from "../ui.js";

function campoPassword(id, etiqueta, extra = "") {
  return `<label class="form-label" for="${id}">${etiqueta}</label>
    <div class="input-group has-validation mb-3">
      <input type="password" class="form-control" id="${id}" required ${extra} autocomplete="${id === "password" ? "current-password" : "new-password"}">
      <button class="btn btn-outline-secondary" type="button" data-ver="${id}" aria-label="Mostrar u ocultar contraseña"><i class="bi bi-eye"></i></button>
      <div class="invalid-feedback">${id === "password" && extra ? "Mínimo 8 caracteres." : "Ingrese la contraseña."}</div>
    </div>`;
}

function activarOjos(root) {
  root.querySelectorAll("[data-ver]").forEach((b) => {
    b.onclick = () => {
      const input = root.querySelector("#" + b.dataset.ver);
      const oculto = input.type === "password";
      input.type = oculto ? "text" : "password";
      b.innerHTML = `<i class="bi bi-eye${oculto ? "-slash" : ""}"></i>`;
    };
  });
}

function tarjeta(titulo, subtitulo, formHtml, pie) {
  return `<div class="card auth-card"><div class="card-body p-4 p-sm-5">
    <div class="text-center mb-4"><span class="auth-logo"><i class="bi bi-box-seam-fill"></i></span>
      <h1 class="h4 mt-3 mb-1">${titulo}</h1><p class="text-muted mb-0">${subtitulo}</p></div>
    <div id="auth-error" class="alert alert-danger d-none" role="alert"></div>
    ${formHtml}<hr class="my-4"><p class="text-center text-muted mb-0">${pie}</p></div></div>`;
}

function errorAuth(root, msg) {
  const box = root.querySelector("#auth-error");
  box.textContent = msg;
  box.classList.remove("d-none");
}

export function renderLogin(root) {
  root.innerHTML = tarjeta("InvenVision", "Inicie sesión para continuar", `
    <form id="f" novalidate>
      <label class="form-label" for="email">Correo electrónico</label>
      <div class="mb-3"><input type="email" class="form-control" id="email" required autocomplete="username" autofocus>
        <div class="invalid-feedback">Ingrese un correo válido.</div></div>
      ${campoPassword("password", "Contraseña")}
      <button class="btn btn-primary w-100" id="submit"><span class="spinner-border spinner-border-sm d-none me-2"></span>Iniciar sesión</button>
    </form>`, `¿No tiene cuenta? <a href="#/registro">Regístrese</a>`);
  activarOjos(root);
  const f = root.querySelector("#f");
  f.onsubmit = async (ev) => {
    ev.preventDefault();
    root.querySelector("#auth-error").classList.add("d-none");
    if (!validar(f)) return;
    const btn = root.querySelector("#submit");
    btn.disabled = true; btn.querySelector(".spinner-border").classList.remove("d-none");
    try {
      const r = await api("/auth/login", { method: "POST", body: { email: f.email.value.trim(), password: f.password.value } });
      session.set(r.access_token, r.usuario);
      location.hash = "#/dashboard";
    } catch (e) {
      errorAuth(root, e.message);
      btn.disabled = false; btn.querySelector(".spinner-border").classList.add("d-none");
    }
  };
}

export function renderRegistro(root) {
  root.innerHTML = tarjeta("Crear cuenta", "Regístrese como operador", `
    <form id="f" novalidate>
      <div class="mb-3"><label class="form-label" for="nombre">Nombre completo</label>
        <input class="form-control" id="nombre" required minlength="2" maxlength="100" autocomplete="name">
        <div class="invalid-feedback">Ingrese su nombre (mínimo 2 caracteres).</div></div>
      <div class="mb-3"><label class="form-label" for="email">Correo electrónico</label>
        <input type="email" class="form-control" id="email" required autocomplete="username">
        <div class="invalid-feedback">Ingrese un correo válido.</div></div>
      ${campoPassword("password", "Contraseña", 'minlength="8" maxlength="72"')}
      <div class="mb-3"><label class="form-label" for="password2">Repetir contraseña</label>
        <input type="password" class="form-control" id="password2" required autocomplete="new-password">
        <div class="invalid-feedback">Las contraseñas no coinciden.</div></div>
      <button class="btn btn-primary w-100" id="submit">Crear cuenta</button>
    </form>`, `¿Ya tiene cuenta? <a href="#/login">Inicie sesión</a>`);
  activarOjos(root);
  const f = root.querySelector("#f");
  const coinciden = () => f.password2.setCustomValidity(f.password.value === f.password2.value ? "" : "no coinciden");
  f.password.oninput = f.password2.oninput = coinciden;
  f.onsubmit = async (ev) => {
    ev.preventDefault();
    coinciden();
    if (!validar(f)) return;
    const btn = root.querySelector("#submit");
    btn.disabled = true;
    try {
      await api("/auth/register", { method: "POST", body: { nombre: f.nombre.value.trim(), email: f.email.value.trim(), password: f.password.value } });
      toast("Cuenta creada. Ya puede iniciar sesión.");
      location.hash = "#/login";
    } catch (e) {
      errorAuth(root, e.message);
      btn.disabled = false;
    }
  };
}
