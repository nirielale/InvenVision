import { api } from "../api.js";
import { COLORES, errorBox, esc, spinner } from "../ui.js";

const MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const etiquetaMes = (m) => `${MES[Number(m.slice(5)) - 1]} ${m.slice(2, 4)}`;

export async function reportes(root, { esActual }) {
  let charts = [];
  const destruir = () => { charts.forEach((c) => c.destroy()); charts = []; };

  async function cargar(meses) {
    const zona = root.querySelector("#zona");
    zona.innerHTML = spinner();
    let est;
    try { est = await api("/estadisticas", { query: { meses } }); } catch (e) { zona.innerHTML = errorBox(e); return; }
    if (!esActual()) return;
    destruir();
    const e = est.por_estado;
    zona.innerHTML = `
      <div class="row g-3">
        <div class="col-lg-4"><div class="card h-100"><div class="card-header">Distribución por estado</div><div class="card-body"><div class="chart-box"><canvas id="r-estado"></canvas></div></div></div></div>
        <div class="col-lg-8"><div class="card h-100"><div class="card-header">Productos y unidades por categoría</div><div class="card-body"><div class="chart-box"><canvas id="r-cat"></canvas></div></div></div></div>
        <div class="col-lg-6"><div class="card h-100"><div class="card-header">Evolución del inventario (productos registrados acumulados)</div><div class="card-body"><div class="chart-box"><canvas id="r-evo"></canvas></div></div></div></div>
        <div class="col-lg-6"><div class="card h-100"><div class="card-header">Vencimientos en los próximos meses</div><div class="card-body"><div class="chart-box"><canvas id="r-venc"></canvas></div></div></div></div>
      </div>
      <p class="text-muted small mt-3">Umbral de «por vencer»: ${est.umbral_dias} días. La evolución se calcula con la fecha de registro de cada producto actual (no refleja productos eliminados).</p>`;
    const opciones = { maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } };
    charts = [
      new Chart(root.querySelector("#r-estado"), { type: "doughnut",
        data: { labels: ["Vigentes", "Por vencer", "Vencidos", "Sin fecha"], datasets: [{ data: [e.vigente, e.proximo, e.vencido, e.sin_fecha], backgroundColor: [COLORES.vigente, COLORES.proximo, COLORES.vencido, COLORES.sin_fecha] }] },
        options: { maintainAspectRatio: false, cutout: "62%", plugins: { legend: { position: "bottom" } } } }),
      new Chart(root.querySelector("#r-cat"), { type: "bar",
        data: { labels: est.por_categoria.map((c) => c.categoria), datasets: [
          { label: "Productos", data: est.por_categoria.map((c) => c.productos), backgroundColor: "#10b981", borderRadius: 6 },
          { label: "Unidades", data: est.por_categoria.map((c) => c.unidades), backgroundColor: "#a7f3d0", borderRadius: 6 }] },
        options: opciones }),
      new Chart(root.querySelector("#r-evo"), { type: "line",
        data: { labels: est.evolucion.map((m) => etiquetaMes(m.mes)), datasets: [{ label: "Productos", data: est.evolucion.map((m) => m.productos), borderColor: "#059669", backgroundColor: "rgba(5,150,105,.15)", fill: true, tension: .3 }] },
        options: { ...opciones, plugins: { legend: { display: false } } } }),
      new Chart(root.querySelector("#r-venc"), { type: "bar",
        data: { labels: est.vencimientos_proximos.map((m) => etiquetaMes(m.mes)), datasets: [{ label: "Productos que vencen", data: est.vencimientos_proximos.map((m) => m.productos), backgroundColor: "#f59e0b", borderRadius: 6 }] },
        options: { ...opciones, plugins: { legend: { display: false } } } }),
    ];
  }

  root.innerHTML = `<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
      <p class="text-muted mb-0">Datos reales del inventario.</p>
      <div class="d-flex align-items-center gap-2"><label for="meses" class="small text-muted">Periodo</label>
        <select id="meses" class="form-select form-select-sm w-auto">${[3, 6, 12].map((n) => `<option value="${n}" ${n === 6 ? "selected" : ""}>${n} meses</option>`).join("")}</select></div></div>
    <div id="zona"></div>`;
  root.querySelector("#meses").onchange = (ev) => cargar(Number(ev.target.value));
  await cargar(6);
  return destruir;
}

export { esc };
