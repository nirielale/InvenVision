from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import ROL_ADMIN, Usuario

_bearer = HTTPBearer(auto_error=False)
_HASH_FALSO = bcrypt.hashpw(b"x", bcrypt.gensalt())  # iguala el tiempo si el usuario no existe


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str | None) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), (hashed or "").encode())
    except ValueError:  # hash con formato desconocido
        return False


def verificar_credenciales(db: Session, email: str, password: str) -> Usuario | None:
    user = db.query(Usuario).filter(Usuario.email == email.lower()).first()
    if user is None:
        bcrypt.checkpw(password.encode("utf-8"), _HASH_FALSO)
        return None
    if not verify_password(password, user.password_hash) or not user.activo:
        return None
    return user


def crear_token(user: Usuario) -> str:
    if not settings.jwt_secret:
        raise HTTPException(500, "JWT_SECRET no está configurado en el .env")
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": str(user.id), "rol": user.rol, "exp": exp},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def usuario_actual(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    no_auth = HTTPException(401, "Sesión no válida o expirada", headers={"WWW-Authenticate": "Bearer"})
    if cred is None or not settings.jwt_secret:
        raise no_auth
    try:
        datos = jwt.decode(cred.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user = db.get(Usuario, int(datos["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise no_auth
    if user is None or not user.activo:
        raise no_auth
    return user


def requiere_admin(user: Usuario = Depends(usuario_actual)) -> Usuario:
    if user.rol != ROL_ADMIN:
        raise HTTPException(403, "Se requieren permisos de administrador")
    return user
