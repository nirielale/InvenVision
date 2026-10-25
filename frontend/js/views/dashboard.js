import { api } from "../api.js";
import { COLORES, badgeEstado, diasTexto, esc, fmtFecha, fmtFechaHora, fmtMoneda, kpi, vacio } from "../ui.js";

const ETIQUETA_RESULTADO = { pendiente: "Pendiente", confirmada: "Confirmada", corregida: "Corregida", descartada: "Descartada", ilegible: "Ilegible" };

export async function dashboard(root, { esActual }) {
  const [d, est] = await Promise.all([api("/dashboard"), api("/estadisticas", { query: { meses: 6 } })]);
  if (!esActual()) return;
  const e = d.por_estado;

  root.innerHTML = `
    ${e.vencido ? `<div class="alert alert-danger d-flex align-items-center gap-2"><i class="bi bi-x-octagon-fill fs-5"></i>
      <div><strong>${e.vencido}</strong> producto(s) vencido(s). <a href="#/alertas" class="alert-link">Revisar alertas</a></div></div>` : ""}
    <div class="row g-3 mb-3">
      <div class="col-6 col-xl-3">${kpi("box-seam", "i-gray", d.total_productos, "Productos registrados")}</div>
      <div class="col-6 col-xl-3">${kpi("check-circle", "i-green", e.vigente, "Vigentes")}</div>
      <div class="col-6 col-xl-3">${kpi("exclamation-triangle", "i-amber", e.proximo, `Por vencer (≤ ${d.umbral_dias} d)`)}</div>
      <div class="col-6 col-xl-3">${kpi("x-octagon", "i-red", e.vencido, "Vencidos")}</div>
    </div>
    <div class="row g-3 mb-3">
      <div class="col-md-6 col-xl-3">${kpi("stack", "i-green", d.unidades_en_stock.toLocaleString("es-PE"), "Unidades en stock")}</div>
      <div class="col-md-6 col-xl-3">${kpi("currency-dollar", "i-green", fmtMoneda(d.valor_inventario), "Valor del inventario (costo)")}</div>
    </div>
    <div class="row g-3 mb-3">
      <div class="col-lg-4"><div class="card h-100"><div class="card-header">Estado del inventario</div>
        <div class="card-body"><div class="chart-box"><canvas id="c-estado"></canvas></div></div></div></div>
      <div class="col-lg-8"><div class="card h-100"><div class="card-header">Productos por categoría</div>
        <div class="card-body"><div class="chart-box"><canvas id="c-cat"></canvas></div></div></div></div>
    </div>
    <div class="row g-3">
      <div class="col-xl-7"><div class="card h-100"><div class="card-header d-flex justify-content-between">Próximos a vencer
        <a href="#/alertas" class="small fw-normal">Ver todos</a></div>
        ${d.proximos.length ? `<div class="table-responsive"><table class="table mb-0"><thead><tr><th>Producto</th><th>Vence</th><th>Restan</th><th>Stock</th></tr></thead><tbody>
          ${d.proximos.map((p) => `<tr><td><a href="#/productos/${p.id}" class="fw-semibold text-decoration-none">${esc(p.nombre)}</a>
            <div class="small text-muted">${esc(p.categoria)}</div></td><td>${fmtFecha(p.fecha_vencimiento)}</td>
            <td>${badgeEstado(p.estado)} <span class="small">${diasTexto(p.dias_restantes)}</span></td><td>${p.cantidad}</td></tr>`).join("")}
          </tbody></table></div>` : vacio("No hay productos próximos a vencer", "check2-circle")}</div></div>
      <div class="col-xl-5"><div class="card h-100"><div class="card-header">Actividad reciente (escaneos)</div>
        ${d.actividad.length ? `<ul class="list-group list-group-flush">${d.actividad.map((a) => `
          <li class="list-group-item d-flex justify-content-between align-items-start">
            <div><div class="fw-semibold">${ETIQUETA_RESULTADO[a.resultado] || esc(a.resultado)}${a.fecha_detectada ? ` · ${fmtFecha(a.fecha_detectada)}` : ""}</div>
              <div class="small text-muted">${esc(a.usuario || "—")}${a.producto ? ` · ${esc(a.producto)}` : ""}</div></div>
            <small class="text-muted text-nowrap">${fmtFechaHora(a.creado_en)}</small></li>`).join("")}</ul>`
          : vacio("Aún no hay escaneos", "camera")}</div></div>
    </div>`;

  const charts = [
    new Chart(root.querySelector("#c-estado"), {
      type: "doughnut",
      data: {
        labels: ["Vigentes", "Por vencer", "Vencidos", "Sin fecha"],
        datasets: [{ data: [e.vigente, e.proximo, e.vencido, e.sin_fecha], backgroundColor: [COLORES.vigente, COLORES.proximo, COLORES.vencido, COLORES.sin_fecha] }],
      },
      options: { maintainAspectRatio: false, plugins: { legend: { position: "bottom" } }, cutout: "62%" },
    }),
    new Chart(root.querySelector("#c-cat"), {
      type: "bar",
      data: { labels: est.por_categoria.map((c) => c.categoria), datasets: [{ label: "Productos", data: est.por_categoria.map((c) => c.productos), backgroundColor: "#10b981", borderRadius: 6 }] },
      options: { maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
    }),
  ];
  return () => charts.forEach((c) => c.destroy());
}
