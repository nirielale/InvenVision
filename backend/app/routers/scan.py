import uuid
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import HistorialDeteccion, Producto, Usuario
from app.routers.common import guardar_archivo, ruta_archivo
from app.schemas import ConfirmarScanIn
from app.security import usuario_actual
from app.services import vision

router = APIRouter(prefix="/api", tags=["Escáner OCR e historial"])


def _fila(h: HistorialDeteccion) -> dict:
    return {
        "id": h.id, "creado_en": h.creado_en, "fecha_detectada": h.fecha_detectada,
        "resultado": h.resultado, "confirmada": h.confirmada, "texto_ocr": h.texto_ocr,
        "tiene_imagen": bool(h.imagen),
        "producto_id": h.producto_id, "producto": h.producto.nombre if h.producto else None,
        "usuario": h.usuario.nombre if h.usuario else None,
    }


@router.get("/ocr/estado")
def estado_ocr(_: Usuario = Depends(usuario_actual)):
    return {"disponible": vision.ocr_disponible()}


@router.post("/scan")
def escanear(
    archivo: UploadFile = File(...),
    user: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    """Analiza la imagen y registra una detección PENDIENTE; no modifica productos."""
    datos = archivo.file.read(vision.MAX_BYTES + 1)
    try:
        resultado = vision.escanear(datos)
    except vision.ImagenInvalida as e:
        raise HTTPException(400, str(e))
    except vision.OcrNoDisponible as e:
        raise HTTPException(503, str(e))

    ruta = guardar_archivo("scans", f"{uuid.uuid4().hex}.{vision.extension(datos)}", datos)
    h = HistorialDeteccion(
        usuario_id=user.id, imagen=ruta, texto_ocr=resultado["texto"],
        resultado="ilegible" if not resultado["texto"] else "pendiente", confirmada=False,
    )
    db.add(h)
    db.commit()
    return {"id": h.id, **resultado}


def _pendiente(db: Session, hid: int) -> HistorialDeteccion:
    h = db.get(HistorialDeteccion, hid)
    if h is None:
        raise HTTPException(404, "Detección no encontrada")
    if h.confirmada or h.resultado in ("descartada", "confirmada", "corregida"):
        raise HTTPException(409, "Esta detección ya fue resuelta")
    return h


@router.post("/scan/{hid}/confirmar")
def confirmar(
    hid: int, datos: ConfirmarScanIn,
    _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db),
):
    """El usuario confirma o corrige la fecha. Solo aquí se escribe en el producto."""
    if datos.fecha is None:
        raise HTTPException(422, "Debe indicar la fecha de vencimiento a confirmar")
    h = _pendiente(db, hid)
    # 'confirmada' si coincide con una fecha leída por el OCR, 'corregida' si la escribió el usuario
    from app.services.date_parser import extraer_fechas

    leidas = {c.fecha for c in extraer_fechas(h.texto_ocr or "")}
    h.fecha_detectada = datos.fecha
    h.resultado = "confirmada" if datos.fecha.isoformat() in leidas else "corregida"
    h.confirmada = True
    if datos.producto_id is not None:
        p = db.get(Producto, datos.producto_id)
        if p is None:
            raise HTTPException(404, "Producto no encontrado")
        p.fecha_vencimiento = datos.fecha
        h.producto_id = p.id
    db.commit()
    return _fila(h)


@router.post("/scan/{hid}/descartar")
def descartar(hid: int, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    h = _pendiente(db, hid)
    h.resultado, h.confirmada = "descartada", False
    db.commit()
    return _fila(h)


@router.get("/historial")
def historial(
    resultado: Literal["pendiente", "confirmada", "corregida", "descartada", "ilegible"] | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    q = db.query(HistorialDeteccion)
    if resultado:
        q = q.filter(HistorialDeteccion.resultado == resultado)
    total = q.with_entities(func.count(HistorialDeteccion.id)).scalar()
    filas = (
        q.options(joinedload(HistorialDeteccion.producto), joinedload(HistorialDeteccion.usuario))
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
