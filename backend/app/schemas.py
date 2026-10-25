from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Rol = Literal["administrador", "operador"]


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
    negocio: str | None = None
    creado_en: datetime | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


class CategoriaIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)

    @field_validator("nombre")
    @classmethod
    def _strip(cls, v):
        return v.strip()


class CategoriaOut(CategoriaIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    total_productos: int = 0


class ProductoIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    categoria_id: int
    codigo_barras: str | None = Field(default=None, max_length=50)
    lote: str | None = Field(default=None, max_length=50)
    cantidad: int = Field(ge=0, le=10_000_000)
    fecha_vencimiento: date

    @field_validator("nombre")
    @classmethod
    def _strip(cls, v):
        return v.strip()

    @field_validator("codigo_barras", "lote")
    @classmethod
    def _vacio_a_none(cls, v):
        v = (v or "").strip()
        return v or None


class StockIn(BaseModel):
    cantidad: int | None = Field(default=None, ge=0, le=10_000_000)
    delta: int | None = Field(default=None, ge=-10_000_000, le=10_000_000)


class ProductoOut(BaseModel):
    id: int
    nombre: str
    categoria_id: int
    categoria: str
    codigo_barras: str | None
    lote: str | None
    cantidad: int
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
    scan_id: str = Field(pattern=r"^\d+_[0-9a-f]{32}$")
    fecha: date
    producto_id: int | None = None
