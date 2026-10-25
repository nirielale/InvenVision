import json
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import HistorialDeteccion, Producto, Usuario
from app.routers import common
from app.routers.common import ruta_archivo
from app.services.date_parser import extraer_fechas
from app.schemas import ConfirmarScanIn
from app.security import usuario_actual
from app.services import vision

router = APIRouter(prefix="/api", tags=["Escáner OCR e historial"])


def _fila(h: HistorialDeteccion) -> dict:
    return {
        "id": h.id, "creado_en": h.creado_en, "fecha_detectada": h.fecha_detectada,
        "resultado": "corregida" if h.corregido_manual else "confirmada", "confirmada": True,
        "texto_ocr": h.texto_ocr, "confianza_ocr": float(h.confianza_ocr) if h.confianza_ocr is not None else None,
        "tiene_imagen": bool(h.imagen),
        "producto_id": h.producto_id, "producto": h.producto.nombre if h.producto else None,
    }


def _archivos_scan(scan_id: str, user: Usuario) -> tuple[Path, Path]:
    """Devuelve (json, imagen) de un escaneo pendiente de este usuario o responde 404."""
    if not scan_id.startswith(f"{user.id}_"):
        raise HTTPException(404, "Escaneo no encontrado o ya resuelto")
    carpeta = common.UPLOAD_DIR / "scans"
    meta = carpeta / f"{scan_id}.json"
    imagenes = [f for f in carpeta.glob(f"{scan_id}.*") if f.suffix != ".json"]
    if not meta.is_file() or not imagenes:
        raise HTTPException(404, "Escaneo no encontrado o ya resuelto")
    return meta, imagenes[0]


@router.get("/ocr/estado")
def estado_ocr(_: Usuario = Depends(usuario_actual)):
    return {"disponible": vision.ocr_disponible()}


@router.post("/scan")
def escanear(archivo: UploadFile = File(...), user: Usuario = Depends(usuario_actual)):
    """Analiza la imagen; NO escribe en la base de datos. Devuelve un `scan_id` para confirmar o descartar."""
    datos = archivo.file.read(vision.MAX_BYTES + 1)
    try:
        resultado = vision.escanear(datos)
    except vision.ImagenInvalida as e:
        raise HTTPException(400, str(e))
    except vision.OcrNoDisponible as e:
        raise HTTPException(503, str(e))

    scan_id = f"{user.id}_{uuid.uuid4().hex}"
    common.guardar_archivo("scans", f"{scan_id}.{vision.extension(datos)}", datos)
    common.guardar_archivo(
        "scans", f"{scan_id}.json",
        json.dumps({"texto": resultado["texto"], "confianza": resultado.get("confianza")}).encode("utf-8"),
    )
    return {"scan_id": scan_id, **resultado}


@router.post("/scan/confirmar")
def confirmar(
    datos: ConfirmarScanIn, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db),
):
    """El usuario confirma o corrige la fecha. Solo aquí se escribe en historial y producto."""
    meta, imagen = _archivos_scan(datos.scan_id, user)
    info = json.loads(meta.read_text(encoding="utf-8"))
    producto = None
    if datos.producto_id is not None:
        producto = db.get(Producto, datos.producto_id)
        if producto is None:
            raise HTTPException(404, "Producto no encontrado")
    # 'confirmada' si coincide con una fecha leída por el OCR, 'corregida' si la escribió el usuario
    leidas = {c.fecha for c in extraer_fechas(info["texto"] or "")}
    h = HistorialDeteccion(
        producto_id=producto.id if producto else None,
        imagen=f"scans/{imagen.name}", texto_ocr=info["texto"], fecha_detectada=datos.fecha,
        confianza_ocr=info.get("confianza"), corregido_manual=datos.fecha.isoformat() not in leidas,
    )
    db.add(h)
    if producto:
        producto.fecha_vencimiento = datos.fecha
    db.commit()
    meta.unlink(missing_ok=True)  # el escaneo queda resuelto
    return _fila(h)


@router.delete("/scan/{scan_id}", status_code=204)
def descartar(scan_id: str, user: Usuario = Depends(usuario_actual)):
    meta, imagen = _archivos_scan(scan_id, user)
    meta.unlink(missing_ok=True)
    imagen.unlink(missing_ok=True)


@router.get("/historial")
def historial(
    resultado: Literal["confirmada", "corregida"] | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    q = db.query(HistorialDeteccion)
    if resultado:
        q = q.filter(HistorialDeteccion.corregido_manual.is_(resultado == "corregida"))
    total = q.with_entities(func.count(HistorialDeteccion.id)).scalar()
    filas = (
        q.options(joinedload(HistorialDeteccion.producto))
        .order_by(HistorialDeteccion.creado_en.desc(), HistorialDeteccion.id.desc())
        .offset((page - 1) * page_size).limit(page_size).all()
    )
    return {"items": [_fila(h) for h in filas], "total": total, "page": page, "page_size": page_size}


@router.get("/historial/{hid}/imagen")
def imagen(hid: int, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    h = db.get(HistorialDeteccion, hid)
    ruta = ruta_archivo(h.imagen if h else None)
    if ruta is None:
        raise HTTPException(404, "Imagen no disponible")
    return FileResponse(ruta)
