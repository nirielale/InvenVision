import { api } from "../api.js";
import { esc, fmtFecha, toast } from "../ui.js";

const TIPO = {
  vencimiento: ["success", "Vencimiento"],
  fabricacion: ["secondary", "Fabricación / envasado"],
  desconocido: ["warning text-dark", "Sin etiqueta"],
};

export async function escaner(root, { query, esActual }) {
  const [ocr, prods] = await Promise.all([api("/ocr/estado"), api("/productos", { query: { page_size: 100, ordenar_por: "nombre" } })]);
  if (!esActual()) return;

  let archivo = null, previewUrl = null, stream = null;
  const detenerCamara = () => { stream?.getTracks().forEach((t) => t.stop()); stream = null; };
  const liberar = () => { detenerCamara(); if (previewUrl) URL.revokeObjectURL(previewUrl); previewUrl = null; };

  function paso1() {
    liberar(); archivo = null;
    root.innerHTML = `
      ${ocr.disponible ? "" : `<div class="alert alert-warning"><i class="bi bi-exclamation-triangle-fill me-2"></i>
        El motor OCR (Tesseract) no está instalado en el servidor, por lo que no se pueden analizar imágenes. Consulte el README.</div>`}
      <div class="row g-3">
        <div class="col-lg-6"><div class="card h-100"><div class="card-header">1. Seleccione la imagen de la etiqueta</div><div class="card-body">
          <label class="form-label" for="archivo">Subir fotografía (JPEG, PNG o WEBP, máx. 8 MB)</label>
          <input type="file" id="archivo" class="form-control mb-3" accept="image/jpeg,image/png,image/webp">
          <div class="d-flex gap-2 flex-wrap mb-3" id="cam-barra">
            <button class="btn btn-outline-primary" id="cam-on"><i class="bi bi-camera-video me-1"></i>Usar cámara</button>
            <select id="cam-sel" class="form-select w-auto d-none" aria-label="Cámara"></select>
            <button class="btn btn-primary d-none" id="capturar"><i class="bi bi-record-circle me-1"></i>Capturar</button>
            <button class="btn btn-outline-secondary d-none" id="cam-off"><i class="bi bi-x-lg me-1"></i>Cancelar</button></div>
          <div id="cam-error"></div>
          <video id="video" class="cam d-none" playsinline muted></video>
          <div id="vista"></div></div></div></div>
        <div class="col-lg-6"><div class="card h-100"><div class="card-header">2. Producto asociado (opcional)</div><div class="card-body">
          <label class="form-label" for="producto">Al confirmar, la fecha se guardará en este producto</label>
          <select id="producto" class="form-select mb-2"><option value="">— Solo registrar la detección —</option>
          ${prods.items.map((p) => `<option value="${p.id}" ${String(p.id) === query.producto ? "selected" : ""}>${esc(p.nombre)} ${p.codigo_barras ? `(${esc(p.codigo_barras)})` : ""}</option>`).join("")}</select>
          ${prods.total > prods.items.length ? `<div class="form-text">Se muestran los primeros ${prods.items.length} de ${prods.total} productos.</div>` : ""}
          <div class="alert alert-light border mt-3 mb-3 small">Consejos: buena luz, sin reflejos, etiqueta enfocada y recta. Nada se guarda en el producto hasta que usted confirme la fecha.</div>
          <button class="btn btn-primary w-100" id="analizar" disabled><i class="bi bi-search me-1"></i>Analizar imagen</button></div></div></div>
      </div>`;

    const vista = root.querySelector("#vista"), btn = root.querySelector("#analizar");
    const elegir = (blob) => {
      if (blob.size > 8 * 1024 * 1024) { toast("La imagen supera los 8 MB", "error"); return; }
      archivo = blob;
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      previewUrl = URL.createObjectURL(blob);
      vista.innerHTML = `<img src="${previewUrl}" class="scan-preview" alt="Vista previa"><div class="form-text mt-1">Revise que la fecha se vea nítida; si no, tome otra o suba otra imagen.</div>`;
      btn.disabled = !ocr.disponible;
    };
    const $ = (id) => root.querySelector(id);
    const video = $("#video"), selCam = $("#cam-sel");
    const mostrarCamara = (on) => {
      video.classList.toggle("d-none", !on);
      $("#capturar").classList.toggle("d-none", !on);
      $("#cam-off").classList.toggle("d-none", !on);
      $("#cam-on").classList.toggle("d-none", on);
      if (!on) selCam.classList.add("d-none");
    };
    const errorCamara = (msg) => { $("#cam-error").innerHTML = `<div class="alert alert-warning py-2"><i class="bi bi-camera-video-off me-2"></i>${esc(msg)}</div>`; };
    const cerrarCamara = () => { detenerCamara(); video.srcObject = null; mostrarCamara(false); };

    $("#archivo").onchange = (ev) => {
      const f = ev.target.files[0];
      if (!f) return;
      if (!["image/jpeg", "image/png", "image/webp"].includes(f.type)) { toast("Formato no admitido. Use JPEG, PNG o WEBP.", "error"); ev.target.value = ""; return; }
      cerrarCamara(); $("#cam-error").innerHTML = ""; elegir(f);
    };

    async function abrirCamara(deviceId) {
      $("#cam-error").innerHTML = "";
      if (!navigator.mediaDevices?.getUserMedia) {
        errorCamara("Este navegador no permite usar la cámara (requiere abrir la aplicación desde localhost o HTTPS). Puede subir una imagen en su lugar.");
        return;
      }
      detenerCamara();
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: deviceId ? { deviceId: { exact: deviceId } } : { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1080 } },
          audio: false,
        });
        video.srcObject = stream; await video.play();
        vista.innerHTML = ""; archivo = null; btn.disabled = true;
        mostrarCamara(true);
        // Tras conceder el permiso el navegador ya revela los nombres de las cámaras
        const camaras = (await navigator.mediaDevices.enumerateDevices()).filter((d) => d.kind === "videoinput");
        const actual = stream.getVideoTracks()[0]?.getSettings().deviceId;
        selCam.innerHTML = camaras.map((c, i) => `<option value="${esc(c.deviceId)}" ${c.deviceId === actual ? "selected" : ""}>${esc(c.label || `Cámara ${i + 1}`)}</option>`).join("");
        selCam.classList.toggle("d-none", camaras.length < 2);
      } catch (e) {
        mostrarCamara(false);
        const motivos = {
          NotAllowedError: "Se denegó el permiso de la cámara. Permítalo desde el icono del candado junto a la dirección y vuelva a intentar.",
          SecurityError: "El navegador bloqueó la cámara por seguridad. Use http://127.0.0.1:8000 o HTTPS.",
          NotFoundError: "No se encontró ninguna cámara en este equipo. Puede subir una imagen en su lugar.",
          NotReadableError: "La cámara está siendo usada por otra aplicación. Ciérrela e intente de nuevo.",
          OverconstrainedError: "La cámara seleccionada ya no está disponible. Elija otra o recargue.",
        };
        errorCamara(motivos[e.name] || `No se pudo iniciar la cámara (${e.name || "error desconocido"}).`);
      }
    }
    $("#cam-on").onclick = () => abrirCamara();
    selCam.onchange = () => abrirCamara(selCam.value);
    $("#cam-off").onclick = cerrarCamara;
    $("#capturar").onclick = () => {
      if (!video.videoWidth) { toast("La cámara aún no está lista; espere un segundo.", "error"); return; }
      const c = document.createElement("canvas");
      c.width = video.videoWidth; c.height = video.videoHeight;
      c.getContext("2d").drawImage(video, 0, 0);
      c.toBlob((blob) => {
        if (!blob) { toast("No se pudo tomar la fotografía. Intente de nuevo.", "error"); return; }
        cerrarCamara();  // detiene las pistas de vídeo
        elegir(new File([blob], "captura.jpg", { type: "image/jpeg" }));
      }, "image/jpeg", 0.92);
    };

    btn.onclick = async () => {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Analizando…';
      const fd = new FormData(); fd.append("archivo", archivo, archivo.name || "captura.jpg");
      try {
        const r = await api("/scan", { method: "POST", form: fd });
        if (!esActual()) return;
        paso2(r, root.querySelector("#producto").value);
      } catch (e) {
        toast(e.status === 503 ? "El motor OCR no está disponible en el servidor." : e.message, "error");
        btn.disabled = false; btn.innerHTML = '<i class="bi bi-search me-1"></i>Analizar imagen';
      }
    };
  }

  function paso2(r, productoId) {
    const sug = r.sugerida?.fecha || "";
    root.innerHTML = `<div class="row g-3">
      <div class="col-lg-5"><div class="card"><div class="card-header">Imagen analizada</div><div class="card-body">
        <img src="${previewUrl}" class="scan-preview mb-3" alt="Imagen analizada">
        <div class="small text-muted mb-1">Texto reconocido por el OCR</div><div class="ocr-text">${esc(r.texto || "(no se reconoció texto)")}</div>
        ${r.confianza != null ? `<div class="mt-2 small text-muted">Confianza media del OCR: ${r.confianza} %</div>` : ""}
        ${r.lotes?.length ? `<div class="mt-2 small">Lote(s) detectado(s): ${r.lotes.map((l) => `<span class="badge text-bg-light border">${esc(l)}</span>`).join(" ")}</div>` : ""}</div></div></div>
      <div class="col-lg-7"><div class="card"><div class="card-header">3. Confirme la fecha de vencimiento</div><div class="card-body">
        ${r.advertencias.map((a) => `<div class="alert alert-warning py-2"><i class="bi bi-exclamation-triangle me-2"></i>${esc(a)}</div>`).join("")}
        ${r.candidatas.length ? `<div class="mb-3"><div class="fw-semibold mb-2">Fechas candidatas</div><div class="d-grid gap-2">
          ${r.candidatas.map((c, i) => { const [cl, tx] = TIPO[c.tipo]; return `<label class="cand"><div class="d-flex align-items-center gap-2">
            <input type="radio" name="cand" class="form-check-input mt-0" value="${c.fecha}" ${c.fecha === sug ? "checked" : ""}>
            <div class="flex-grow-1"><strong>${fmtFecha(c.fecha)}</strong> <span class="text-muted small">leído como «${esc(c.texto)}»</span>
              <div class="small">${c.ambigua ? '<span class="text-warning-emphasis"><i class="bi bi-exclamation-triangle"></i> Ambigua (día/mes)</span> ' : ""}${esc(c.nota)}</div></div>
            <span class="badge text-bg-${cl}">${tx}</span></div></label>`; }).join("")}</div></div>` : ""}
        <form id="f" novalidate><label class="form-label fw-semibold" for="fecha">Fecha de vencimiento (puede corregirla)</label>
          <input type="date" class="form-control mb-1" id="fecha" required value="${sug}">
          <div class="invalid-feedback">Indique la fecha antes de confirmar.</div>
          <div class="form-text mb-3">${sug ? "Sugerida por el sistema; verifique contra la imagen." : "El sistema no pudo sugerir una fecha con certeza: elíjala o escríbala manualmente."}</div>
          <div class="d-flex gap-2 flex-wrap"><button class="btn btn-primary" id="confirmar"><i class="bi bi-check2-circle me-1"></i>Confirmar y guardar</button>
          <button type="button" class="btn btn-outline-danger" id="descartar">Descartar</button></div></form>
        ${productoId ? "" : '<div class="form-text mt-2">Sin producto asociado: solo se registrará la detección en el historial.</div>'}
      </div></div></div></div>`;

    const form = root.querySelector("#f");
    root.querySelectorAll("input[name=cand]").forEach((rb) => (rb.onchange = () => { form.fecha.value = rb.value; }));
    form.onsubmit = async (ev) => {
      ev.preventDefault();
      form.classList.add("was-validated");
      if (!form.fecha.value) return;
      const btn = root.querySelector("#confirmar"); btn.disabled = true;
      try {
        await api("/scan/confirmar", { method: "POST", body: { scan_id: r.scan_id, fecha: form.fecha.value, producto_id: productoId ? Number(productoId) : null } });
        toast("Fecha confirmada y registrada");
        location.hash = productoId ? `#/productos/${productoId}` : "#/historial";
      } catch (e) { toast(e.message, "error"); btn.disabled = false; }
    };
    root.querySelector("#descartar").onclick = async () => {
      try { await api(`/scan/${r.scan_id}`, { method: "DELETE" }); toast("Detección descartada", "secondary"); paso1(); }
      catch (e) { toast(e.message, "error"); }
    };
  }

  paso1();
  return liberar;
}
