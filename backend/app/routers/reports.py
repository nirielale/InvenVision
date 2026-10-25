from datetime import date, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Categoria, ConfiguracionAlertas, HistorialDeteccion, Producto, Usuario
from app.routers.common import producto_out, umbral_alertas
from app.schemas import ConfigAlertasIn
from app.security import requiere_admin, usuario_actual
from app.services.expiry import (
    ESTADO_PROXIMO, ESTADO_SIN_FECHA, ESTADO_VENCIDO, ESTADO_VIGENTE, filtro_estado,
)

router = APIRouter(prefix="/api", tags=["Alertas, dashboard y reportes"])
ESTADOS = (ESTADO_VENCIDO, ESTADO_PROXIMO, ESTADO_VIGENTE, ESTADO_SIN_FECHA)


def _por_estado(db: Session, umbral: int) -> dict:
    return {
        e: db.query(func.count(Producto.id)).filter(filtro_estado(Producto.fecha_vencimiento, e, umbral)).scalar()
        for e in ESTADOS
    }


def _meses_atras(hoy: date, n: int) -> list[date]:
    anio, mes = hoy.year, hoy.month
    salida = []
    for _ in range(n):
        salida.append(date(anio, mes, 1))
        mes -= 1
        if mes == 0:
            anio, mes = anio - 1, 12
    return salida[::-1]


@router.get("/config-alertas")
def ver_config(_: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    return {"dias_alerta": umbral_alertas(db)}


@router.put("/config-alertas")
def guardar_config(datos: ConfigAlertasIn, _: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)):
    cfg = db.query(ConfiguracionAlertas).order_by(ConfiguracionAlertas.id).first()
    if cfg is None:
        cfg = ConfiguracionAlertas(dias_alerta=datos.dias_alerta)
        db.add(cfg)
    cfg.dias_alerta = datos.dias_alerta
    db.commit()
    return {"dias_alerta": cfg.dias_alerta}


@router.get("/alertas")
def alertas(
    estado: Literal["vencido", "proximo", "vigente"] | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    """Productos con fecha, ordenados por urgencia. Las notificaciones son solo dentro de la aplicación."""
    umbral = umbral_alertas(db)
    q = db.query(Producto).options(joinedload(Producto.categoria)).filter(Producto.fecha_vencimiento.isnot(None))
    if estado:
        q = q.filter(filtro_estado(Producto.fecha_vencimiento, estado, umbral))
    total = q.with_entities(func.count(Producto.id)).scalar()
    filas = q.order_by(Producto.fecha_vencimiento, Producto.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "umbral_dias": umbral, "total": total, "page": page, "page_size": page_size,
        "resumen": _por_estado(db, umbral),
        "items": [producto_out(p, umbral).model_dump(mode="json") for p in filas],
    }


@router.get("/dashboard")
def dashboard(_: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    umbral = umbral_alertas(db)
    hoy = date.today()
    por_estado = _por_estado(db, umbral)
    proximos = (
        db.query(Producto).options(joinedload(Producto.categoria))
        .filter(filtro_estado(Producto.fecha_vencimiento, ESTADO_PROXIMO, umbral))
        .order_by(Producto.fecha_vencimiento).limit(8).all()
    )
    actividad = (
        db.query(HistorialDeteccion).options(joinedload(HistorialDeteccion.usuario), joinedload(HistorialDeteccion.producto))
        .order_by(HistorialDeteccion.creado_en.desc()).limit(8).all()
    )
    return {
        "umbral_dias": umbral,
        "total_productos": sum(por_estado.values()),
        "unidades_en_stock": db.query(func.coalesce(func.sum(Producto.cantidad), 0)).scalar(),
        "valor_inventario": float(db.query(func.coalesce(func.sum(Producto.cantidad * Producto.precio_costo), 0)).scalar()),
        "por_estado": por_estado,
        "proximos": [producto_out(p, umbral, hoy).model_dump(mode="json") for p in proximos],
        "actividad": [
            {"id": h.id, "creado_en": h.creado_en.isoformat() if h.creado_en else None, "resultado": h.resultado,
             "fecha_detectada": h.fecha_detectada.isoformat() if h.fecha_detectada else None,
             "usuario": h.usuario.nombre if h.usuario else None,
             "producto": h.producto.nombre if h.producto else None}
            for h in actividad
        ],
    }


@router.get("/estadisticas")
def estadisticas(meses: int = Query(6, ge=1, le=24), _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    umbral = umbral_alertas(db)
    hoy = date.today()
    por_categoria = [
        {"categoria": nombre, "productos": n, "unidades": int(u)}
        for nombre, n, u in db.query(Categoria.nombre, func.count(Producto.id), func.coalesce(func.sum(Producto.cantidad), 0))
        .outerjoin(Producto, Producto.categoria_id == Categoria.id).group_by(Categoria.id).order_by(Categoria.nombre).all()
    ]
    # Evolución: productos acumulados al cierre de cada mes, según fecha de registro
    inicios = _meses_atras(hoy, meses)
    evolucion = []
    for ini in inicios:
        siguiente = date(ini.year + (ini.month == 12), ini.month % 12 + 1, 1)
        n = db.query(func.count(Producto.id)).filter(Producto.creado_en < siguiente).scalar()
        evolucion.append({"mes": ini.strftime("%Y-%m"), "productos": n})
    # Vencimientos de los próximos meses (incluye el actual)
    venc = []
    anio, mes = hoy.year, hoy.month
    for _ in range(meses):
        ini = date(anio, mes, 1)
        sig = date(anio + (mes == 12), mes % 12 + 1, 1)
        n = db.query(func.count(Producto.id)).filter(Producto.fecha_vencimiento >= max(ini, hoy), Producto.fecha_vencimiento < sig).scalar()
        venc.append({"mes": ini.strftime("%Y-%m"), "productos": n})
        anio, mes = sig.year, sig.month
    return {
        "umbral_dias": umbral, "por_estado": _por_estado(db, umbral),
        "por_categoria": por_categoria, "evolucion": evolucion, "vencimientos_proximos": venc,
    }
