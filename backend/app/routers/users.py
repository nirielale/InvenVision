from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ROL_ADMIN, Usuario
from app.schemas import UsuarioCrearIn, UsuarioEditarIn, UsuarioOut
from app.security import hash_password, requiere_admin

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios (admin)"])


@router.get("", response_model=list[UsuarioOut])
def listar(_: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)):
    return db.query(Usuario).order_by(Usuario.nombre).all()


@router.post("", response_model=UsuarioOut, status_code=201)
def crear(datos: UsuarioCrearIn, _: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)):
    user = Usuario(
        nombre=datos.nombre, email=datos.email.lower(),
        password_hash=hash_password(datos.password), rol=datos.rol, activo=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ya existe un usuario con ese correo")
    return user


@router.put("/{user_id}", response_model=UsuarioOut)
def editar(
    user_id: int, datos: UsuarioEditarIn,
    admin: Usuario = Depends(requiere_admin), db: Session = Depends(get_db),
):
    user = db.get(Usuario, user_id)
    if user is None:
        raise HTTPException(404, "Usuario no encontrado")
    if user.id == admin.id and (datos.activo is False or (datos.rol and datos.rol != ROL_ADMIN)):
        raise HTTPException(400, "No puede quitarse a sí mismo el rol de administrador ni desactivarse")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        if valor is not None:
            setattr(user, campo, valor)
    db.commit()
    return user
