"""Modelos ORM, alineados con el esquema REAL de MySQL (`invenvision`).

El esquema se inspeccionó con un usuario de solo lectura/DML; la aplicación nunca crea ni altera tablas.
Los atributos `email`, `cantidad` e `imagen` se mapean a las columnas reales `correo`, `stock` e `imagen_path`.
Verificación contra la base real: `python -m scripts.verificar_esquema`.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

ROL_ADMIN = "administrador"
ROL_OPERADOR = "operador"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column("correo", String(150), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(Enum(ROL_ADMIN, ROL_OPERADOR, name="rol"), default=ROL_OPERADOR)
    negocio: Mapped[str | None] = mapped_column(String(150))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), index=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"), index=True)
    codigo_barras: Mapped[str | None] = mapped_column(String(50))
    lote: Mapped[str | None] = mapped_column(String(50))
    fecha_vencimiento: Mapped[date] = mapped_column(Date, index=True)
    cantidad: Mapped[int] = mapped_column("stock", Integer, default=0)
    imagen: Mapped[str | None] = mapped_column("imagen_path", String(255))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    categoria: Mapped[Categoria] = relationship()


class HistorialDeteccion(Base):
    """Una fila por detección CONFIRMADA por el usuario (la tabla real no guarda estados pendientes)."""

    __tablename__ = "historial_deteccion"

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int | None] = mapped_column(ForeignKey("productos.id", ondelete="SET NULL"), index=True)
    imagen: Mapped[str] = mapped_column("imagen_path", String(255))
    texto_ocr: Mapped[str | None] = mapped_column("texto_detectado_ocr", Text)
    fecha_detectada: Mapped[date | None] = mapped_column(Date)
    confianza_ocr: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    corregido_manual: Mapped[bool] = mapped_column("fue_corregido_manual", Boolean, default=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    producto: Mapped[Producto | None] = relationship()


class ConfiguracionAlertas(Base):
    """Configuración por usuario (columna usuario_id única)."""

    __tablename__ = "configuracion_alertas"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), unique=True)
    dias_alerta: Mapped[int] = mapped_column(Integer, default=30)
