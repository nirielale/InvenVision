"""Crea un usuario administrador pidiendo la contraseña por teclado (no queda en el historial).

Uso (desde la carpeta backend, con el entorno virtual activo):
    python -m scripts.crear_admin

Solo INSERTA un usuario nuevo; si el correo ya existe, no modifica nada.
"""
import getpass
import sys

from pydantic import ValidationError

from app.database import SessionLocal
from app.models import ROL_ADMIN, Usuario
from app.schemas import RegistroIn
from app.security import hash_password


def main() -> int:
    nombre = input("Nombre: ").strip()
    email = input("Correo: ").strip().lower()
    password = getpass.getpass("Contraseña (mín. 8 caracteres): ")
    if password != getpass.getpass("Repita la contraseña: "):
        print("Las contraseñas no coinciden.")
        return 1
    try:
        RegistroIn(nombre=nombre, email=email, password=password)
    except ValidationError as e:
        print("Datos no válidos:", "; ".join(err["msg"] for err in e.errors()))
        return 1

    with SessionLocal() as db:
        if db.query(Usuario).filter(Usuario.email == email).first():
            print("Ya existe un usuario con ese correo. No se modificó nada.")
            return 1
        db.add(Usuario(nombre=nombre, email=email, password_hash=hash_password(password), rol=ROL_ADMIN, activo=True))
        db.commit()
    print("Administrador creado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
