from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Categoria, HistorialDeteccion, Producto, Usuario
from app.routers.common import (
    guardar_archivo, producto_out, ruta_archivo, umbral_alertas,
)
from app.schemas import PaginaProductos, ProductoIn, ProductoOut, StockIn
from app.security import requiere_admin, usuario_actual
from app.services import vision
from app.services.expiry import filtro_estado

router = APIRouter(prefix="/api/productos", tags=["Productos"])

Estado = Literal["vencido", "proximo", "vigente", "sin_fecha"]
ORDENABLES = {
    "nombre": Producto.nombre, "sku": Producto.sku, "cantidad": Producto.cantidad,
    "precio_costo": Producto.precio_costo, "fecha_vencimiento": Producto.fecha_vencimiento,
    "creado_en": Producto.creado_en,
}


def _obtener(db: Session, pid: int) -> Producto:
    p = db.get(Producto, pid, options=[joinedload(Producto.categoria)])
    if p is None:
        raise HTTPException(404, "Producto no encontrado")
    return p


def _validar_categoria(db: Session, cat_id: int):
    cat = db.get(Categoria, cat_id)
    if cat is None or not cat.activa:
        raise HTTPException(422, "La categoría no existe o está desactivada")


def _guardar(db: Session, p: Producto):
    db.add(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ya existe un producto con ese SKU")


@router.get("", response_model=PaginaProductos)
def listar(
    q: str | None = Query(None, max_length=100),
    categoria_id: int | None = None,
    estado: Estado | None = None,
    ordenar_por: Literal[tuple(ORDENABLES)] = "nombre",  # type: ignore[valid-type]
    orden: Literal["asc", "desc"] = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    umbral = umbral_alertas(db)
    consulta = db.query(Producto).options(joinedload(Producto.categoria))
    if q:
        patron = f"%{q.strip()}%"
        consulta = consulta.filter(or_(
            Producto.nombre.like(patron), Producto.sku.like(patron),
            Producto.marca.like(patron), Producto.lote.like(patron),
        ))
    if categoria_id:
        consulta = consulta.filter(Producto.categoria_id == categoria_id)
    if estado:
        consulta = consulta.filter(filtro_estado(Producto.fecha_vencimiento, estado, umbral))
    total = consulta.with_entities(func.count(Producto.id)).order_by(None).scalar()

    col = ORDENABLES[ordenar_por]
    col = col.asc() if orden == "asc" else col.desc()
    if ordenar_por == "fecha_vencimiento":  # sin fecha siempre al final
        consulta = consulta.order_by(Producto.fecha_vencimiento.is_(None), col, Producto.id)
    else:
        consulta = consulta.order_by(col, Producto.id)
    filas = consulta.offset((page - 1) * page_size).limit(page_size).all()
    return PaginaProductos(
        items=[producto_out(p, umbral) for p in filas], total=total, page=page, page_size=page_size
    )


@router.post("", response_model=ProductoOut, status_code=201)
def crear(datos: ProductoIn, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    _validar_categoria(db, datos.categoria_id)
    p = Producto(**datos.model_dump())
    _guardar(db, p)
    return producto_out(_obtener(db, p.id), umbral_alertas(db))


@router.get("/{pid}", response_model=ProductoOut)
def detalle(pid: int, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    return producto_out(_obtener(db, pid), umbral_alertas(db))


@router.get("/{pid}/detecciones")
def detecciones(pid: int, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    _obtener(db, pid)
    filas = (
        db.query(HistorialDeteccion).filter(HistorialDeteccion.producto_id == pid)
        .order_by(HistorialDeteccion.creado_en.desc()).limit(50).all()
    )
    return [
        {"id": h.id, "creado_en": h.creado_en, "fecha_detectada": h.fecha_detectada,
         "resultado": h.resultado, "confirmada": h.confirmada}
        for h in filas
    ]


@router.put("/{pid}", response_model=ProductoOut)
def editar(pid: int, datos: ProductoIn, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _obtener(db, pid)
    if datos.categoria_id != p.categoria_id:
        _validar_categoria(db, datos.categoria_id)
    for campo, valor in datos.model_dump().items():
        setattr(p, campo, valor)
    _guardar(db, p)
    return producto_out(_obtener(db, pid), umbral_alertas(db))


@router.patch("/{pid}/stock", response_model=ProductoOut)
def stock(pid: int, datos: StockIn, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    if (datos.cantidad is None) == (datos.delta is None):
        raise HTTPException(422, "Indique 'cantidad' o 'delta' (solo uno)")
    p = _obtener(db, pid)
    nueva = datos.cantidad if datos.cantidad is not None else p.cantidad + datos.delta
    if nueva < 0:
        raise HTTPException(422, "El stock no puede quedar negativo")
    p.cantidad = nueva
    db.commit()
    return producto_out(_obtener(db, pid), umbral_alertas(db))


@router.delete("/{pid}", status_code=204)
def eliminar(pid: int, _: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)):
    p = _obtener(db, pid)
    # El historial se conserva, desvinculado del producto
    db.execute(update(HistorialDeteccion).where(HistorialDeteccion.producto_id == pid).values(producto_id=None))
    db.delete(p)
    db.commit()


@router.post("/{pid}/foto", status_code=204)
def subir_foto(
    pid: int, archivo: UploadFile = File(...),
    _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db),
):
    p = _obtener(db, pid)
    datos = archivo.file.read(vision.MAX_BYTES + 1)
    try:
        vision.validar_imagen(datos)
    except vision.ImagenInvalida as e:
        raise HTTPException(400, str(e))
    p.imagen = guardar_archivo("productos", f"{pid}.{vision.extension(datos)}", datos)
    db.commit()


@router.get("/{pid}/foto")
def ver_foto(pid: int, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    ruta = ruta_archivo(_obtener(db, pid).imagen)
    if ruta is None:
        raise HTTPException(404, "El producto no tiene fotografía")
    return FileResponse(ruta)
