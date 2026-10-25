import { session } from "./api.js";
import { errorBox, spinner } from "./ui.js";
import { renderLogin, renderRegistro } from "./views/auth.js";
import { dashboard } from "./views/dashboard.js";
import { listaProductos, formProducto, detalleProducto } from "./views/productos.js";
import { categorias } from "./views/categorias.js";
import { escaner } from "./views/escaner.js";
import { alertas } from "./views/alertas.js";
import { historial } from "./views/historial.js";
import { reportes } from "./views/reportes.js";
import { perfil } from "./views/perfil.js";
import { usuarios } from "./views/usuarios.js";

const MENU = [
  { seccion: "Principal" },
  { ruta: "/dashboard", icono: "speedometer2", texto: "Dashboard" },
  { ruta: "/productos", icono: "box-seam", texto: "Productos" },
  { ruta: "/categorias", icono: "tags", texto: "Categorías" },
  { seccion: "Visión artificial" },
  { ruta: "/escaner", icono: "camera", texto: "Escáner inteligente" },
  { ruta: "/historial", icono: "clock-history", texto: "Historial" },
  { seccion: "Control" },
  { ruta: "/alertas", icono: "bell", texto: "Alertas" },
  { ruta: "/reportes", icono: "bar-chart-line", texto: "Reportes" },
  { seccion: "Cuenta" },
  { ruta: "/perfil", icono: "gear", texto: "Perfil y configuración" },
  { ruta: "/usuarios", icono: "people", texto: "Usuarios", admin: true },
];

// Orden importa: las rutas más específicas primero
const RUTAS = [
  { re: /^\/dashboard$/, vista: dashboard, titulo: "Dashboard", menu: "/dashboard" },
  { re: /^\/productos$/, vista: listaProductos, titulo: "Productos", menu: "/productos" },
  { re: /^\/productos\/nuevo$/, vista: formProducto, titulo: "Registrar producto", menu: "/productos" },
  { re: /^\/productos\/(\d+)\/editar$/, vista: formProducto, titulo: "Editar producto", menu: "/productos" },
  { re: /^\/productos\/(\d+)$/, vista: detalleProducto, titulo: "Detalle del producto", menu: "/productos" },
  { re: /^\/categorias$/, vista: categorias, titulo: "Categorías", menu: "/categorias" },
  { re: /^\/escaner$/, vista: escaner, titulo: "Escáner inteligente", menu: "/escaner" },
  { re: /^\/historial$/, vista: historial, titulo: "Historial de detecciones", menu: "/historial" },
  { re: /^\/alertas$/, vista: alertas, titulo: "Alertas de vencimiento", menu: "/alertas" },
  { re: /^\/reportes$/, vista: reportes, titulo: "Reportes y estadísticas", menu: "/reportes" },
  { re: /^\/perfil$/, vista: perfil, titulo: "Perfil y configuración", menu: "/perfil" },
  { re: /^\/usuarios$/, vista: usuarios, titulo: "Gestión de usuarios", menu: "/usuarios", admin: true },
];

const $ = (id) => document.getElementById(id);
let limpiar = null;
let token = 0; // evita que una vista lenta pise a una más reciente

function parseHash() {
  const [ruta, qs] = (location.hash.slice(1) || "/").split("?");
  return { ruta: ruta || "/", query: Object.fromEntries(new URLSearchParams(qs || "")) };
}

function pintarMenu(activa) {
  $("nav").innerHTML = MENU.filter((m) => !m.admin || session.isAdmin)
    .map((m) => m.seccion
      ? `<div class="nav-section">${m.seccion}</div>`
      : `<a class="nav-link ${m.ruta === activa ? "active" : ""}" href="#${m.ruta}"><i class="bi bi-${m.icono}"></i>${m.texto}</a>`)
    .join("");
}

function pintarUsuario() {
  const u = session.user;
  $("user-name").textContent = u?.nombre || "";
  $("user-avatar").textContent = (u?.nombre || "?").trim().charAt(0).toUpperCase();
}

async function navegar() {
  const { ruta, query } = parseHash();
  if (limpiar) { try { limpiar(); } catch { /* ignorar */ } limpiar = null; }
  $("sidebar").classList.remove("open");

  const publica = ruta === "/login" || ruta === "/registro";
  if (!session.token) {
    if (!publica) { location.hash = "#/login"; return; }
    $("app-view").classList.add("d-none");
    $("auth-view").classList.remove("d-none");
    (ruta === "/registro" ? renderRegistro : renderLogin)($("auth-view"));
    return;
  }
  if (publica || ruta === "/") { location.hash = "#/dashboard"; return; }

  $("auth-view").classList.add("d-none");
  $("app-view").classList.remove("d-none");
  const def = RUTAS.map((r) => ({ r, m: r.re.exec(ruta) })).find((x) => x.m);
  if (!def) { location.hash = "#/dashboard"; return; }
  if (def.r.admin && !session.isAdmin) { location.hash = "#/dashboard"; return; }

  pintarUsuario();
  pintarMenu(def.r.menu);
  $("page-title").textContent = def.r.titulo;
  document.title = `${def.r.titulo} · InvenVision`;
  const main = $("main");
  main.innerHTML = spinner();
  const mio = ++token;
  try {
    const fin = await def.r.vista(main, { params: def.m.slice(1), query, esActual: () => mio === token });
    if (mio === token) limpiar = typeof fin === "function" ? fin : null;
    else if (typeof fin === "function") fin();
  } catch (e) {
    if (mio === token) main.innerHTML = errorBox(e);
  }
}

$("menu-btn").onclick = () => $("sidebar").classList.toggle("open");
$("backdrop").onclick = () => $("sidebar").classList.remove("open");
$("logout-btn").onclick = () => { session.clear(); location.hash = "#/login"; };
window.addEventListener("hashchange", navegar);
navegar();
