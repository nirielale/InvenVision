from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Rol = Literal["admin", "operador"]


def _password_valida(v: str) -> str:
    if len(v.encode("utf-8")) > 72:  # límite de bcrypt
        raise ValueError("La contraseña no puede superar 72 bytes")
    return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class RegistroIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def _check_password(cls, v):
        return _password_valida(v)

    @field_validator("nombre")
    @classmethod
    def _strip(cls, v):
        return v.strip()


class UsuarioCrearIn(RegistroIn):
    rol: Rol = "operador"


class UsuarioEditarIn(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    rol: Rol | None = None
    activo: bool | None = None


class PerfilIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)


class CambiarPasswordIn(BaseModel):
    actual: str
    nueva: str = Field(min_length=8, max_length=72)

    @field_validator("nueva")
    @classmethod
    def _check_password(cls, v):
        return _password_valida(v)


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    email: str
    rol: str
    activo: bool
    creado_en: datetime | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


class CategoriaIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    descripcion: str | None = Field(default=None, max_length=255)
    activa: bool = True


class CategoriaOut(CategoriaIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    total_productos: int = 0


class ProductoIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    sku: str = Field(min_length=1, max_length=50)
    categoria_id: int
    marca: str | None = Field(default=None, max_length=100)
    lote: str | None = Field(default=None, max_length=60)
    cantidad: int = Field(ge=0, le=10_000_000)
    precio_costo: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    proveedor: str | None = Field(default=None, max_length=150)
    fecha_vencimiento: date | None = None

    @field_validator("nombre", "sku")
    @classmethod
    def _strip(cls, v):
        return v.strip()


class StockIn(BaseModel):
    cantidad: int | None = Field(default=None, ge=0, le=10_000_000)
    delta: int | None = Field(default=None, ge=-10_000_000, le=10_000_000)


class ProductoOut(BaseModel):
    id: int
    nombre: str
    sku: str
    categoria_id: int
    categoria: str
    marca: str | None
    lote: str | None
    cantidad: int
    precio_costo: Decimal
    proveedor: str | None
    fecha_vencimiento: date | None
    estado: str
    dias_restantes: int | None
    tiene_foto: bool
    creado_en: datetime | None
    actualizado_en: datetime | None


class PaginaProductos(BaseModel):
    items: list[ProductoOut]
    total: int
    page: int
    page_size: int


class ConfigAlertasIn(BaseModel):
    dias_alerta: int = Field(ge=1, le=730)


class ConfirmarScanIn(BaseModel):
    fecha: date | None = None
    producto_id: int | None = None
