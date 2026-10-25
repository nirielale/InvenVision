"""Modelos ORM.

IMPORTANTE: las columnas son una PROPUESTA basada en los nombres de tablas del
proyecto. Aún no se contrastaron con el esquema real de MySQL (`invenvision`);
deben conciliarse antes de usar la aplicación sobre esos datos.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

ROL_ADMIN = "admin"
ROL_OPERADOR = "operador"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(20), default=ROL_OPERADOR)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), index=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"), index=True)
    marca: Mapped[str | None] = mapped_column(String(100))
    lote: Mapped[str | None] = mapped_column(String(60))
    cantidad: Mapped[int] = mapped_column(Integer, default=0)
    precio_costo: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    proveedor: Mapped[str | None] = mapped_column(String(150))
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, index=True)
    imagen: Mapped[str | None] = mapped_column(String(255))
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    categoria: Mapped[Categoria] = relationship()


class HistorialDeteccion(Base):
    __tablename__ = "historial_deteccion"

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int | None] = mapped_column(ForeignKey("productos.id", ondelete="SET NULL"), index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    imagen: Mapped[str | None] = mapped_column(String(255))
    texto_ocr: Mapped[str | None] = mapped_column(Text)
    fecha_detectada: Mapped[date | None] = mapped_column(Date)
    resultado: Mapped[str] = mapped_column(String(20), default="pendiente")
    confirmada: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    producto: Mapped[Producto | None] = relationship()
    usuario: Mapped[Usuario | None] = relationship()


class ConfiguracionAlertas(Base):
    __tablename__ = "configuracion_alertas"

    id: Mapped[int] = mapped_column(primary_key=True)
    dias_alerta: Mapped[int] = mapped_column(Integer, default=30)
