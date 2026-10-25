from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models import ConfiguracionAlertas, Producto, Usuario
from app.schemas import ProductoOut
from app.services.expiry import clasificar

UPLOAD_DIR = settings.upload_path  # configurable con UPLOAD_DIR
DIAS_ALERTA_DEFECTO = 30


def umbral_alertas(db: Session, user: Usuario) -> int:
    cfg = db.query(ConfiguracionAlertas).filter(ConfiguracionAlertas.usuario_id == user.id).first()
    return cfg.dias_alerta if cfg else DIAS_ALERTA_DEFECTO


def guardar_archivo(subcarpeta: str, nombre: str, datos: bytes) -> str:
    carpeta = UPLOAD_DIR / subcarpeta
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / nombre).write_bytes(datos)
    return f"{subcarpeta}/{nombre}"


def ruta_archivo(relativa: str | None) -> Path | None:
    """Resuelve una ruta guardada y garantiza que no salga de UPLOAD_DIR."""
    if not relativa:
        return None
    ruta = (UPLOAD_DIR / relativa).resolve()
    if UPLOAD_DIR.resolve() not in ruta.parents or not ruta.is_file():
        return None
    return ruta


def producto_out(p: Producto, umbral: int, hoy: date | None = None) -> ProductoOut:
    estado, dias = clasificar(p.fecha_vencimiento, umbral, hoy)
    return ProductoOut(
        id=p.id, nombre=p.nombre, categoria_id=p.categoria_id,
        categoria=p.categoria.nombre, codigo_barras=p.codigo_barras, lote=p.lote, cantidad=p.cantidad,
        fecha_vencimiento=p.fecha_vencimiento, estado=estado, dias_restantes=dias,
        tiene_foto=bool(p.imagen), creado_en=p.creado_en, actualizado_en=p.actualizado_en,
    )
