from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ROL_OPERADOR, Usuario
from app.schemas import (
    CambiarPasswordIn, LoginIn, PerfilIn, RegistroIn, TokenOut, UsuarioOut,
)
from app.security import (
    crear_token, hash_password, usuario_actual, verificar_credenciales, verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenOut)
def login(datos: LoginIn, db: Session = Depends(get_db)):
    user = verificar_credenciales(db, datos.email, datos.password)
    if user is None:  # mismo mensaje para usuario inexistente, clave errónea o cuenta inactiva
        raise HTTPException(401, "Correo o contraseña incorrectos")
    return TokenOut(access_token=crear_token(user), usuario=user)


@router.post("/register", response_model=UsuarioOut, status_code=201)
def registro(datos: RegistroIn, db: Session = Depends(get_db)):
    """Registro público: siempre crea un usuario con rol operador."""
    user = Usuario(
        nombre=datos.nombre, email=datos.email.lower(),
        password_hash=hash_password(datos.password), rol=ROL_OPERADOR, activo=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ya existe un usuario con ese correo")
    return user


@router.get("/me", response_model=UsuarioOut)
def perfil(user: Usuario = Depends(usuario_actual)):
    return user


@router.put("/me", response_model=UsuarioOut)
def actualizar_perfil(datos: PerfilIn, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    user.nombre = datos.nombre.strip()
    db.commit()
    return user


@router.post("/cambiar-password", status_code=204)
def cambiar_password(
    datos: CambiarPasswordIn, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)
):
    if not verify_password(datos.actual, user.password_hash):
        raise HTTPException(400, "La contraseña actual es incorrecta")
    user.password_hash = hash_password(datos.nueva)
    db.commit()
