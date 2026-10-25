from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Categoria, Producto, Usuario
from app.schemas import CategoriaIn, CategoriaOut
from app.security import requiere_admin, usuario_actual

router = APIRouter(prefix="/api/categorias", tags=["Categorías"])


def _out(c: Categoria, total: int) -> CategoriaOut:
    return CategoriaOut(id=c.id, nombre=c.nombre, total_productos=total)


def _total(db: Session, cat_id: int) -> int:
    return db.query(func.count(Producto.id)).filter(Producto.categoria_id == cat_id).scalar()


@router.get("", response_model=list[CategoriaOut])
def listar(_: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    q = (
        db.query(Categoria, func.count(Producto.id))
        .outerjoin(Producto, Producto.categoria_id == Categoria.id)
        .group_by(Categoria.id)
        .order_by(Categoria.nombre)
    )
    return [_out(c, n) for c, n in q.all()]


def _guardar(db: Session, cat: Categoria):
    db.add(cat)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ya existe una categoría con ese nombre")


@router.post("", response_model=CategoriaOut, status_code=201)
def crear(datos: CategoriaIn, _: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)):
    cat = Categoria(nombre=datos.nombre)
    _guardar(db, cat)
    return _out(cat, 0)


@router.put("/{cat_id}", response_model=CategoriaOut)
def editar(cat_id: int, datos: CategoriaIn, _: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)):
    cat = db.get(Categoria, cat_id)
    if cat is None:
        raise HTTPException(404, "Categoría no encontrada")
    cat.nombre = datos.nombre
    _guardar(db, cat)
    return _out(cat, _total(db, cat.id))


@router.delete("/{cat_id}", status_code=204)
def eliminar(cat_id: int, _: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)):
    """Solo elimina categorías sin productos; nunca toca productos existentes."""
    cat = db.get(Categoria, cat_id)
    if cat is None:
        raise HTTPException(404, "Categoría no encontrada")
    if _total(db, cat.id):
        raise HTTPException(409, "La categoría tiene productos asociados; reasígnelos antes de eliminarla")
    db.delete(cat)
    db.commit()
