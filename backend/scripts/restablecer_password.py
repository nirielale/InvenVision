"""Restablece la contraseña de UN usuario existente, pidiéndola por teclado (sin eco, no queda en el historial).

Uso (desde la carpeta backend, con el entorno virtual activo):
    python -m scripts.restablecer_password

Solo actualiza la columna `password_hash` del usuario indicado, tras una confirmación explícita.
No crea ni elimina usuarios y no toca ningún otro dato.
"""
import getpass
import sys

from pydantic import ValidationError

from app.database import SessionLocal
from app.models import Usuario
from app.schemas import CambiarPasswordIn
from app.security import hash_password


def main() -> int:
    email = input("Correo del usuario: ").strip().lower()
    with SessionLocal() as db:
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if user is None:
            print("No existe un usuario con ese correo. No se modificó nada.")
            return 1
        print(f"Se cambiará SOLO la contraseña de: {user.nombre} <{user.email}> ({user.rol}).")
        if input("Escriba SI para continuar: ").strip() != "SI":
            print("Cancelado. No se modificó nada.")
            return 1
        nueva = getpass.getpass("Nueva contraseña (mín. 8 caracteres): ")
        if nueva != getpass.getpass("Repita la contraseña: "):
            print("Las contraseñas no coinciden. No se modificó nada.")
            return 1
        try:
            CambiarPasswordIn(actual="-", nueva=nueva)
        except ValidationError as e:
            print("Contraseña no válida:", "; ".join(err["msg"] for err in e.errors()))
            return 1
        user.password_hash = hash_password(nueva)
        user.activo = True
        db.commit()
    print("Contraseña actualizada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
